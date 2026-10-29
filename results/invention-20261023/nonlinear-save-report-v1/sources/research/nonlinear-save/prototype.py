"""Finite nonlinear save compiler for four binary bytes and constant bulk copies."""
import argparse, importlib.util, json, subprocess, tempfile, time
from pathlib import Path
import model as m
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ns_tools',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
N=4
def c(v):return '(i32.const %d)'%(v&0xffffffff)
def pack():
    ts=['(i32.shl (i32.load8_u %s) %s)'%(c(i),c(i)) for i in range(N)]
    v=ts[0]
    for t in ts[1:]:v='(i32.or '+v+' '+t+')'
    return v
def stores(expr,local):
    return '(local.set %d %s) '%(local,expr)+' '.join('(i32.store8 %s (i32.and (i32.shr_u (local.get %d) %s) (i32.const 1)))'%(c(i),local,c(i)) for i in range(N))
def blob(a):return ''.join('\\%02x'%x for x in a)
def rawcopy(op,j):
    dst,src,n=op
    return '(memory.copy (select (i32.const 65536) %s (i32.eq (local.get 0) %s)) %s %s)'%(c(dst),c(j),c(src),c(n))
def plain(ops):
    return '''(module (memory 1 1)
      (func (export "reset") (param i32) (local i32) '''+stores('(i32.and (local.get 0) (i32.const 15))',1)+''')
      (func (export "peek") (result i32) '''+pack()+''')
      (func (export "run") (param i32) '''+' '.join(rawcopy(op,j) for j,op in enumerate(ops))+'))'
def parse(src):
    module=q.read(src);fs=[e for e in module[1:] if e[0]=='func']
    if len(fs)!=3:raise ValueError('three function profile')
    copies=[e for e in q.walk(fs[2]) if e[0]=='memory.copy'];ops=[]
    if not 1<=len(copies)<=8:raise ValueError('1..8 copies')
    for j,e in enumerate(copies):
        if len(e)!=4 or e[1][0]!='select' or e[2][0]!='i32.const' or e[3][0]!='i32.const':raise ValueError('constant selected copy')
        a=e[1]
        if a[1]!=['i32.const','65536'] or a[2][0]!='i32.const' or a[3]!=['i32.eq',['local.get','0'],['i32.const',str(j)]]:raise ValueError('copy failure selector')
        ops.append([int(a[2][1],0),int(e[2][1],0),int(e[3][1],0)])
    m.plan(N,ops,list(range(16)))
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='nonlinear-save-') as td:
        f=Path(td)/'source.wasm';q.compile(plain(ops),f)
        if q.read(f)!=module:raise ValueError('canonical closed source profile required')
    return ops

def encoded(ops,encoding,mode):
    info=m.plan(N,ops,encoding);linear=m.linear_save(info)
    if mode=='full':colors=list(range(16));count=16
    elif mode=='linear':colors=linear['colors'];count=linear['color_count']
    elif mode in ('color','bad'):colors=info['colors'];count=info['color_count']
    else:raise ValueError('mode')
    bits=(count-1).bit_length();palette=1<<bits
    data=list(encoding)+info['inverse']+colors;offset=64;tables=[]
    for ss,tt in zip(info['side'],info['target']):
        table=[None]*(16*palette)
        for y in range(16):
            at=ss[y]*palette+colors[y]
            if table[at] is not None and table[at]!=tt[y]:raise AssertionError('conflicting repair')
            table[at]=tt[y]
        tables.append([0 if v is None else v for v in table])
    def lookup(base,index):return '(i32.load8_u (i32.add %s %s))'%(c(base),index)
    def repair(j):
        at='(i32.add (i32.shl %s %s) (local.get 1))'%(pack(),c(bits))
        return stores(lookup(offset+48+j*16*palette,at),2)
    # Data tables are operational; no generation manifest is embedded.
    data += [v for table in tables for v in table]
    parts=['(local.set 1 '+lookup(offset+32,pack())+')']
    for j,op in enumerate(ops):
        if j and mode!='bad':parts.append('(if (i32.eq (local.get 0) %s) (then %s))'%(c(j),repair(j)))
        parts.append(rawcopy(op,j))
    parts.append(repair(len(ops)))
    init=[(encoding[0]>>i)&1 for i in range(N)]
    text='(module (memory 1 1) (data (i32.const 0) "'+blob(init)+'") (data (i32.const 64) "'+blob(data)+'")'
    text+=' (func (export "reset") (param i32) (local i32) '+stores(lookup(offset,'(i32.and (local.get 0) (i32.const 15))'),1)+')'
    text+=' (func (export "peek") (result i32) '+lookup(offset+16,pack())+')'
    text+=' (func (export "run") (param i32) (local i32 i32) '+' '.join(parts)+'))'
    return text,{'info':info,'linear':linear,'saved_bits':bits,'saved_colors':count,'saved_i32_locals':1,'temporary_i32_locals':1,'repair_table_bytes':sum(map(len,tables)),'all_table_bytes':len(data)}

def transform(src,dst,encoding,mode='color'):
    start=time.perf_counter();ops=parse(src);text,info=encoded(ops,encoding,mode);q.compile(text,dst)
    return {'mode':mode,**info,'transform_ms':(time.perf_counter()-start)*1000}

def recovered_text(tables):
    k=len(tables)-1;data=[v for row in tables for v in row]
    index='(i32.add (i32.shl (select (local.get 0) %s (i32.lt_u (local.get 0) %s)) (i32.const 4)) %s)'%(c(k),c(k),pack())
    value='(i32.load8_u (i32.add (i32.const 64) '+index+'))'
    text='(module (memory 1 1) (data (i32.const 64) "'+blob(data)+'")'
    text+=' (func (export "reset") (param i32) (local i32) '+stores('(i32.and (local.get 0) (i32.const 15))',1)+')'
    text+=' (func (export "peek") (result i32) '+pack()+')'
    text+=' (func (export "run") (param i32) (local i32) '+stores(value,1)+' (if (i32.lt_u (local.get 0) '+c(k)+') (then (memory.copy (i32.const 65536) (i32.const 0) (i32.const 1))))))'
    return text

def recover(src,dst):
    start=time.perf_counter();r=subprocess.run(['node',str(HERE/'query.cjs'),str(Path(src).resolve())],capture_output=True,text=True,timeout=30)
    if r.returncode:raise ValueError(r.stderr)
    obs=json.loads(r.stdout);q.compile(recovered_text(obs['tables']),dst)
    return {'status':'finite_profile_candidate','calls':obs['calls'],'prefixes':len(obs['tables']),'tables':obs['tables'],'total_ms':(time.perf_counter()-start)*1000,'assumptions':'complete four-bit observable state; hidden state outside the public profile is not certified'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--encoding',type=Path);ap.add_argument('--mode',choices=['full','linear','color','bad'],default='color');a=ap.parse_args()
    result=transform(a.source,a.output,json.loads(a.encoding.read_text()),a.mode) if a.action=='transform' else recover(a.source,a.output)
    q.save(str(a.output)+'.json',result);print(json.dumps(result))
