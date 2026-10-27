"""Conjugated record updates with read/write-aware gate cancellation."""
import argparse,copy,hashlib,importlib.util,json,random,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('cone_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
w=q.w;save=q.save;compile=q.compile;read=q.read;walk=q.walk;tool=q.tool;digest=q.digest
DECL={'type','param','result','local'};MASK=0xffffffff
class Unsupported(ValueError):pass
def c(x):return ['i32.const',str(x)]
def g(x):return ['local.get',str(x)]
def rot(x,r):return ((x<<r)|(x>>(32-r)))&MASK
def schedule(n,coeff):return [(k,t,coeff[k],(7+5*k)%31+1) for k in range(len(coeff)) for t in range(k%2,n,2)]
def mix(a,gate,n):
    k,t,cc,r=gate
    for lane in range(4):a[4*t+lane]^=rot((a[4*((t-1)%n)+lane]*cc+a[4*((t+1)%n)+lane])&MASK,r)
def encoded(words,n,coeff,inverse=False):
    out=list(words);sched=schedule(n,coeff)
    if inverse:sched=sched[::-1]
    for base in range(0,len(out),4*n):
        a=out[base:base+4*n]
        for gate in sched:mix(a,gate,n)
        out[base:base+4*n]=a
    return out
def plan(n,coeff,reads,writes,mode):
    r=set(reads);v=set(writes);selected=[]
    for gate in schedule(n,coeff):
        _,t,_,_=gate;controls={(t-1)%n,(t+1)%n}
        if mode=='full':keep=True
        elif mode=='footprint':keep=bool((r|v)&(controls|{t}))
        elif mode=='broken':keep=t in v or bool(controls&v)
        elif mode=='patch':keep=t in (r|v) or bool(controls&v)
        else:raise Unsupported('plan mode')
        if keep:
            selected.append(gate)
            changes_target=t in v or bool(controls&v)
            r|=controls|{t}
            if changes_target or mode=='footprint':v.add(t)
    return selected
def data_string(bs):return '"'+''.join('\\%02x'%b for b in bs)+'"'
def unescape(s):
    b=bytearray();i=1
    while i<len(s)-1:
        if s[i]=='\\':
            if i+2<len(s)-1 and all(x in '0123456789abcdefABCDEF' for x in s[i+1:i+3]):b.append(int(s[i+1:i+3],16));i+=3
            else:b.append({'n':10,'r':13,'t':9,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
        else:b.extend(s[i].encode('utf-8'));i+=1
    return bytes(b)
def initial(m,size):
    out=bytearray(size)
    for d in [e for e in m[1:] if e[0]=='data']:
        if d[1][:1]!=['i32.const']:raise Unsupported('active constant data only')
        start=int(d[1][1]);b=b''.join(unescape(x) for x in d[2:])
        if start<0 or start+len(b)>size:raise Unsupported('data outside records')
        out[start:start+len(b)]=b
    return list(struct.unpack('<'+'I'*(size//4),out))
def load(off):return f'(i32.load offset={off} (local.get 3))'
def source_text(words,n,records):
    size=n*16;shift=size.bit_length()-1
    prefix=f'(if (i32.ge_u (local.get 0) (i32.const {records})) (then (unreachable))) (local.set 3 (i32.shl (local.get 0) (i32.const {shift})))'
    body=[f'''(local.set 4 (i32.add {load(0)} (local.get 1)))
      (local.set 5 (i32.xor {load(4)} (local.get 2)))
      (i32.store (local.get 3) (local.get 4)) (i32.store offset=4 (local.get 3) (local.get 5))
      (i32.xor (local.get 4) (local.get 5))''',
      f'''(local.set 4 {load(0)}) (local.set 5 {load(16)}) (local.set 6 {load(32)})
      (i32.store (local.get 3) (i32.add (local.get 4) (i32.mul (local.get 2) (local.get 5))))
      (i32.store offset=16 (local.get 3) (i32.xor (local.get 5) (i32.rotl (local.get 6) (local.get 1))))
      (i32.xor (i32.xor (local.get 4) (local.get 5)) (local.get 6))''',
      f'''(local.set 4 {load(0)}) (local.set 5 {load(size//2)}) (local.set 6 {load(size-16)})
      (local.set 5 (i32.add (local.get 5) (i32.mul (local.get 1) (local.get 6))))
      (i32.store offset={size//2} (local.get 3) (local.get 5))
      (i32.store offset={size-16} (local.get 3) (i32.xor (local.get 6) (local.get 4)))
      (i32.add (local.get 5) (local.get 4))''']
    fs=' '.join(f'(func (export "{name}") (param i32 i32 i32) (result i32) (local i32 i32 i32 i32) {prefix} {b})' for name,b in zip(('bump','coupled','spread'),body))
    bs=struct.pack('<'+'I'*len(words),*words)
    return f'(module (memory 1 1) {fs} (data (i32.const 0) {data_string(bs)}))'
def profile(m,n,records):
    if n<4 or n&(n-1) or not 1<=records<=16 or n*16*records>65536:raise Unsupported('record size')
    if any(e[0] not in ('type','memory','func','export','data') for e in m[1:]):raise Unsupported('module feature')
    if [e for e in m[1:] if e[0]=='memory']!=[['memory','1','1']]:raise Unsupported('one fixed private memory')
    if any(e[2][0]!='func' for e in m[1:] if e[0]=='export'):raise Unsupported('only function exports')
    fs=[e for e in m[1:] if e[0]=='func'];profiles=[]
    for f in fs:
        decl=[e for e in f[1:] if e[0] in DECL];body=[e for e in f[1:] if e[0] not in DECL]
        if [e for e in decl if e[0]=='param']!=[['param','i32','i32','i32']] or [e for e in decl if e[0]=='result']!=[['result','i32']]:raise Unsupported('ABI')
        ls=[t for e in decl if e[0]=='local' for t in e[1:]]
        if not ls or any(t!='i32' for t in ls):raise Unsupported('scalar locals')
        guard=['if',['i32.ge_u',g(0),c(records)],['then',['unreachable']]]
        base=['local.set','3',['i32.shl',g(0),c((n*16).bit_length()-1)]]
        if body[:2]!=[guard,base]:raise Unsupported('bounds/base prologue')
        reads=set();writes=set()
        allowed=set('local.get local.set local.tee i32.const i32.add i32.sub i32.mul i32.and i32.or i32.xor i32.shl i32.shr_u i32.shr_s i32.rotl i32.rotr i32.eqz i32.clz i32.ctz i32.popcnt select i32.load i32.store'.split())
        for e in walk(['body',*body[2:]]):
            if e[0]=='body':continue
            if e[0] not in allowed:raise Unsupported('non-total update '+e[0])
            if e[0] in ('local.set','local.tee') and int(e[1])<=3:raise Unsupported('input/base mutation')
            if e[0] in ('i32.load','i32.store'):
                args=[x for x in e[1:] if isinstance(x,list)];imm=[x for x in e[1:] if isinstance(x,str)]
                if not args or args[0]!=g(3) or any(not x.startswith(('align=','offset=')) for x in imm):raise Unsupported('fixed field access')
                off=next((int(x[7:]) for x in imm if x.startswith('offset=')),0)
                if off%4 or not 0<=off<=n*16-4:raise Unsupported('word field range')
                (reads if e[0]=='i32.load' else writes).add(off//16)
        if body[-1][0] in ('local.set','i32.store'):raise Unsupported('final result required')
        profiles.append(dict(reads=sorted(reads),writes=sorted(writes),locals=len(ls)))
    if not fs:raise Unsupported('no update functions')
    return profiles
def vload(t):return ['v128.load','offset='+str(t*16),g(3)]
def gate_code(gate,n,tmp):
    k,t,cc,r=gate
    f=['i32x4.add',['i32x4.mul',vload((t-1)%n),['v128.const','i32x4',*([str(cc)]*4)]],vload((t+1)%n)]
    rotated=['v128.or',['i32x4.shl',g(tmp),c(r)],['i32x4.shr_u',g(tmp),c(32-r)]]
    return [['local.set',str(tmp),f],['v128.store','offset='+str(t*16),g(3),['v128.xor',vload(t),rotated]]]
def transform(src,dst,n,records,depth=4,mode='patch',seed=7):
    start=time.perf_counter();m=read(src);ps=profile(m,n,records);words=initial(m,n*16*records);t1=time.perf_counter();rng=random.Random(seed);coeff=[]
    while len(coeff)<depth:
        v=rng.randrange(0x1000001,0xffffffff)|1
        if v not in coeff:coeff.append(v)
    plans=[];out=[];fi=0
    for e in m[1:]:
        if e[0]=='data':continue
        if e[0]!='func' or mode=='plain':out.append(e);continue
        p=ps[fi];fi+=1;selected=plan(n,coeff,p['reads'],p['writes'],mode);plans.append(dict(p,selected=len(selected),total=len(coeff)*n//2,targets=[t for k,t,cc,r in selected]))
        decl=[x for x in e[1:] if x[0] in DECL and x[0]!='local'];body=[x for x in e[1:] if x[0] not in DECL];ret=3+p['locals'];tmp=ret+1
        pre=[x for ga in reversed(selected) for x in gate_code(ga,n,tmp)];post=[x for ga in selected for x in gate_code(ga,n,tmp)]
        out.append(['func',*decl,['local',*(['i32']*(p['locals']+1)),'v128'],*body[:2],*pre,*body[2:-1],['local.set',str(ret),body[-1]],*post,g(ret)])
    state=words if mode=='plain' else encoded(words,n,coeff);bs=struct.pack('<'+'I'*len(state),*state);out.append(['data',c(0),data_string(bs)]);t2=time.perf_counter();compile(w.emit(['module',*out]),dst);t3=time.perf_counter()
    return dict(n=n,records=records,depth=depth,mode=mode,seed=seed,plans=plans,read_ms=(t1-start)*1000,build_ms=(t2-t1)*1000,compile_ms=(t3-t2)*1000,transform_ms=(t3-start)*1000,coeff=coeff)
def extract_config(src):
    start=time.perf_counter();m=read(src);t1=time.perf_counter();fs=[e for e in m[1:] if e[0]=='func'];coeff=[]
    # Source scalar kernels have no vector constants. In this public emitter,
    # the inverse prelude exposes unique stage constants in reverse order.
    for e in walk(fs[0]):
        if e[0]=='v128.const':
            bs=q.vconst(e);vs=list(struct.unpack('<4I',bytes(bs)))
            if len(set(vs))==1 and vs[0]&1 and vs[0]>=0x1000001 and vs[0] not in coeff:coeff.append(vs[0])
    if not coeff:raise Unsupported('no mix constants')
    if len(coeff)>32:raise Unsupported('too many stages')
    return dict(coeff=coeff[::-1],depth=len(coeff),read_ms=(t1-start)*1000,extract_ms=(time.perf_counter()-t1)*1000)
def probe(src,dst):
    m=read(src);m.append(['export','"memory"',['memory','0']]);compile(w.emit(m),dst)
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('transform');a.add_argument('source');a.add_argument('output');a.add_argument('--chunks',type=int,required=True);a.add_argument('--records',type=int,default=4);a.add_argument('--depth',type=int,default=4);a.add_argument('--seed',type=int,default=7);a.add_argument('--mode',choices=['plain','full','footprint','patch'],default='patch')
    a=sub.add_parser('extract');a.add_argument('source')
    v=p.parse_args();print(json.dumps(transform(v.source,v.output,v.chunks,v.records,v.depth,v.mode,v.seed) if v.cmd=='transform' else extract_config(v.source)))
if __name__=='__main__':main()
