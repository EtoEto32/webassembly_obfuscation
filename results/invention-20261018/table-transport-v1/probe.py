"""Restricted binary transformer and source-free cyclic-table quotient recognizer."""
import argparse, copy, hashlib, json, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
import transform as wasm
C=lambda n:['i32.const',str(n)]
G=lambda n:['local.get',str(n)]
def op(o,a,b):return ['i32.'+o,a,b]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def ast(p):return wasm.parse(wasm.tool('wasm2wat',[p,'--fold-exprs']))
def write(p,m):
    if p.exists():raise ValueError('Refuse overwrite')
    wp=Path(str(p)+'.wat');wp.write_text(wasm.emit(m),encoding='utf-8')
    wasm.tool('wat2wasm',[wp,'-o',p]);wasm.tool('wasm-validate',[p])
def items(m,kind):return [x for x in m if isinstance(x,list) and x and x[0]==kind]
def decl(n):return isinstance(n,list) and n and n[0] in ('type','param','result','local')
def nodes(n):
    if isinstance(n,list):
        yield n
        for x in n:yield from nodes(x)
def layout(m,encoded=False):
    if items(m,'import') or items(m,'global') or items(m,'memory') or items(m,'start'):raise ValueError('unsupported external/state effects')
    ex=items(m,'export');tables=items(m,'table');fs=items(m,'func')
    if len(ex)!=1 or ex[0][1]!='"run"' or ex[0][2][0]!='func':raise ValueError('require only run export and private table')
    if len(tables)!=1 or len(tables[0])!=4 or tables[0][-1]!='funcref':raise ValueError('table shape')
    size=int(tables[0][1]);N=size//2 if encoded else size
    if N<2 or N&(N-1) or tables[0][2]!=str(size):raise ValueError('fixed power-of-two table')
    ri=int(ex[0][2][1]);run=fs[ri]
    if ri!=N or len(fs)!=(N+2 if encoded else N+1):raise ValueError('restricted function layout')
    if sum(len(n)-1 for n in run if isinstance(n,list) and n[0]=='param')!=2:raise ValueError('two parameters required')
    if [n for n in run if isinstance(n,list) and n[0]=='local']!=[['local','i32']]:raise ValueError('one state local required')
    for f in fs[:N]:
        if any(n[0] not in ('func','type','param','result','i32.const','local.get','i32.add','i32.mul','i32.xor','i32.rotl') for n in nodes(f)):raise ValueError('step not pure supported arithmetic')
    return N,run,tables[0],fs
def rotation(N):
    return [
      ['table.copy','0','0',C(N),C(0),C(N)],
      ['table.copy','0','0',C(0),op('add',C(N),G(0)),op('sub',C(N),G(0))],
      ['table.copy','0','0',op('sub',C(N),G(0)),C(N),G(0)]]
def canon(n):
    if not isinstance(n,list):return n
    if n[0]=='table.copy':
        if any(v!='0' for v in n[1:-3]):raise ValueError('nonzero table')
        return ['table.copy',*map(canon,n[-3:])]
    return list(map(canon,n))
def encode(source,out):
    m=ast(source);N,run,table,fs=layout(m);calls=updates=0
    delta=op('and',op('xor',G(0),op('shr_u',G(0),C(11))),C(N-1))
    assignment=['local.set','2',op('and',op('add',G(2),delta),C(N-1))]
    def visit(n):
        nonlocal calls,updates
        if not isinstance(n,list):return n
        if n[0]=='call_indirect':
            if len(n)!=4 or n[-1]!=G(2) or n[-2]!=G(0):raise ValueError('unexpected indirect call')
            calls+=1;return [*n[:-1],C(0)]
        if n==assignment:updates+=1;return ['call','$rotate',delta]
        if n[0]=='local.set' and n[1]=='2':raise ValueError('unexpected state update')
        return list(map(visit,n))
    new=visit(run)
    if calls!=1 or updates!=1:raise ValueError('require one cyclic transition')
    # Only the canonical driver is accepted; no hidden state uses are allowed.
    if sum(n==G(2) for n in nodes(run))!=2:raise ValueError('extra state uses')
    run[:]=new
    pos=next(i for i,n in enumerate(run[1:],1) if isinstance(n,list) and not decl(n))
    run.insert(pos,['table.init','$restore',C(0),C(0),C(N)])
    table[1:3]=[str(2*N)]*2
    m.append(['elem','$restore','func',*map(str,range(N))])
    m.append(['func','$rotate',['param','i32'],*rotation(N)])
    write(out,m);return {'N':N,'inputSHA256':sha(source),'outputSHA256':sha(out),'calls':calls,'updates':updates}
def erase(source,out):
    # No generator file, original binary, manifest, or source-to-state map is read.
    m=ast(source);N,run,table,fs=layout(m,True)
    helper=fs[-1];body=[n for n in helper[1:] if isinstance(n,list) and not decl(n)]
    if canon(body)!=canon(rotation(N)):raise ValueError('unsupported rotation helper')
    elems=items(m,'elem')
    if len(elems)!=2 or elems[0][1]!=C(0) or elems[0][2:]!=['func',*map(str,range(N))] or elems[1][1:]!=['func',*map(str,range(N))]:raise ValueError('unexpected element initialization')
    calls=updates=resets=0
    def visit(n):
        nonlocal calls,updates,resets
        if not isinstance(n,list):return n
        if n[0]=='table.init':
            if n[-3:]!=[C(0),C(0),C(N)]:raise ValueError('reset bounds')
            resets+=1;return None
        if n[0]=='call_indirect':
            if n[-1]!=C(0):raise ValueError('not fixed slot')
            calls+=1;return [*n[:-1],G(2)]
        if n[0]=='call':
            if n[1]!=str(N+1) or len(n)!=3:raise ValueError('unexpected helper call')
            updates+=1;return ['local.set','2',op('and',op('add',G(2),n[2]),C(N-1))]
        return [v for child in n if (v:=visit(child)) is not None]
    run[:]=visit(run)
    if (calls,updates,resets)!=(1,1,1):raise ValueError('unrecognized control updates')
    table[1:3]=[str(N)]*2;m.remove(helper);m.remove(elems[1])
    write(out,m);return {'N':N,'inputSHA256':sha(source),'outputSHA256':sha(out),'quotient':'rotation phase q in Z/NZ','execution_queries':0}
def source(N):
    funcs=[]
    for j in range(N):
        k=(2654435761*(j+1))&0xffffffff;k=k if k<2**31 else k-2**32
        funcs.append(f'(func (param i32) (result i32) (i32.add (i32.mul (i32.rotl (i32.xor (local.get 0) (i32.const {k})) (i32.const {j+1})) (i32.const {3+2*j})) (i32.const {(j+1)*17})))')
    return f'''(module (type $step (func (param i32) (result i32)))
      (table {N} {N} funcref) (elem (i32.const 0) func {' '.join(map(str,range(N)))})
      {' '.join(funcs)}
      (func (export "run") (param i32 i32) (result i32) (local i32)
       (local.set 1 (i32.and (local.get 1) (i32.const 63)))
       (block $exit (loop $loop (br_if $exit (i32.eqz (local.get 1)))
        (local.set 0 (call_indirect (type $step) (local.get 0) (local.get 2)))
        (local.set 2 (i32.and (i32.add (local.get 2) (i32.and (i32.xor (local.get 0) (i32.shr_u (local.get 0) (i32.const 11))) (i32.const {N-1}))) (i32.const {N-1})))
        (local.set 1 (i32.sub (local.get 1) (i32.const 1))) (br $loop))) (local.get 0)))'''
def build(out):
    out.mkdir();save(out/'plan.json',{'N':[4,8,16],'levels':['raw','O2','O3'],'seed':20261018,'random_inputs':1024,
      'attack':'recognize three-copy rotation, replace by phase; no original source; unsupported optimized recognition is not resistance'})
    records=[];attacks=[]
    for N in (4,8,16):
        d=out/str(N);d.mkdir();plain=d/'plain.wasm';write(plain,wasm.parse(source(N)))
        enc=d/'transport.wasm';start=time.perf_counter();info=encode(plain,enc);encsec=time.perf_counter()-start
        dec=d/'erased.wasm';start=time.perf_counter();recovery=erase(enc,dec);decsec=time.perf_counter()-start
        attacks.append({'N':N,'level':'raw','status':'recovered','seconds':decsec,**recovery})
        for mode in ('plain','transport','erased'):
            for level in ('raw','O2','O3'):
                p=d/(mode+'-'+level+'.wasm');src=d/(mode+'.wasm')
                if level=='raw':p.write_bytes(src.read_bytes())
                else:subprocess.run([str(wasm.TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(src),'-'+level,'--enable-reference-types','--enable-bulk-memory','-o',str(p)],check=True,capture_output=True)
                wasm.tool('wasm-validate',[p]);Path(str(p)+'.wat').write_text(wasm.tool('wasm2wat',[p,'--fold-exprs']),encoding='utf-8')
                records.append({'N':N,'mode':mode,'level':level,'file':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p),'transform_seconds':encsec if mode=='transport' else None})
                if mode=='transport' and level!='raw':
                    start=time.perf_counter()
                    try:rr=erase(p,d/('recovered-'+level+'.wasm'));status={'status':'recovered',**rr}
                    except ValueError as e:status={'status':'unsupported','reason':str(e)}
                    attacks.append({'N':N,'level':level,'seconds':time.perf_counter()-start,**status})
        # Exported tables violate this transform's noninterference assumptions.
        bad=ast(plain);bad.append(['export','"table"',['table','0']]);bp=d/'negative-exported.wasm';write(bp,bad)
        try:encode(bp,d/'negative-should-not-exist.wasm');raise AssertionError('accepted exported table')
        except ValueError:pass
    save(out/'manifest.json',{'artifacts':records,'attacks':attacks,'python':sys.version,'sourceSHA256':sha(Path(__file__))})
    (out/'probe.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'variants':len(records),'attacks':attacks},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=('build','encode','erase'));ap.add_argument('source',type=Path);ap.add_argument('output',type=Path,nargs='?');a=ap.parse_args()
    if a.command=='build':build(a.source.resolve())
    else:print(json.dumps((encode if a.command=='encode' else erase)(a.source,a.output)))
