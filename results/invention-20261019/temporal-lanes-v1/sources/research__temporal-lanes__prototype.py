"""Temporal SIMD pipeline probe; retiming and SLP are established techniques."""
import argparse,copy,importlib.util,json,random,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('temporal_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
w=q.w;compile=q.compile;read=q.read;walk=q.walk;save=q.save;digest=q.digest;tool=q.tool
MASK=0xffffffff;LIMIT=16384;DECL={'type','param','result','local','export'}
class Unsupported(ValueError):pass
def c(x):return ['i32.const',str(x&MASK)]
def g(i):return ['local.get',str(i)]
def st(i,x):return ['local.set',str(i),x]
def vc(xs):return ['v128.const','i32x4',*[str(x&MASK) for x in xs]]
def spl(x):return ['i32x4.splat',x]
def words(e):return list(struct.unpack('<4I',bytes(q.vconst(e))))
def scalar(kind,a,b,cc,r):
    mul=['i32.mul',a,c(cc)]
    if kind==0:return ['i32.rotl',['i32.add',mul,b],c(r)]
    if kind==1:return ['i32.add',['i32.mul',['i32.xor',a,b],c(cc)],['i32.rotl',a,c(r)]]
    return ['i32.xor',['i32.rotl',['i32.add',a,b],c(r)],mul]
def stream(t):return ['i32.xor',['i32.rotl',['i32.add',g(3),['i32.mul',t,c(0x9e3779b9)]],c(11)],g(2)]
def initial(i):return ['i32.add',['i32.xor',g(1),c((i+1)*0x10204081)],g(2)]
def guard():return ['if',['i32.gt_u',g(0),c(LIMIT)],['then',['unreachable']]]
def foldxor(xs):
    a=xs[0]
    for b in xs[1:]:a=['i32.xor',a,b]
    return a
def module(locals_,body):return ['module',['memory','1','1'],['func',['export','"run"'],['param',*(['i32']*4)],['result','i32'],['local',*locals_],*body]]
def loop(body,limit):return ['block',['loop',['br_if','1',['i32.ge_u',g(4),limit]],*body,st(4,['i32.add',g(4),c(1)]),['br','0']]]
def outputs(vals):return [['i32.store','offset='+str(4*i),c(0),v] for i,v in enumerate(vals)]+[foldxor(vals)]
def source(coeff,kind,r):
    n=len(coeff);body=[guard(),*[st(5+i,initial(i)) for i in range(n)]]
    step=[st(5+i,scalar(kind,g(5+i),stream(g(4)) if i==0 else g(4+i),cc,r)) for i,cc in enumerate(coeff)]
    body+=[loop(step,g(0)),*outputs([g(5+i) for i in range(n)])]
    return module(['i32']*(n+1),body)
def normalize(e):
    if not isinstance(e,list):return e
    if e[:1]==['i32.const']:return c(int(e[1],0))
    if e[:1]==['i32.store']:
        imm=[x for x in e[1:] if isinstance(x,str)];off=next((int(x[7:]) for x in imm if x.startswith('offset=')),0)
        return ['i32.store','offset='+str(off),*[normalize(x) for x in e[1:] if isinstance(x,list)]]
    return [normalize(x) for x in e]
def bodyof(f):return [e for e in f[1:] if e[0] not in DECL]
def parse_source(m):
    if any(e[0] not in ('type','memory','func','export') for e in m[1:]):raise Unsupported('module feature')
    if [e for e in m[1:] if e[0]=='memory']!=[['memory','1','1']]:raise Unsupported('fixed private memory')
    if [e for e in m[1:] if e[0]=='export']!=[['export','"run"',['func','0']]]:raise Unsupported('run export only')
    fs=[e for e in m[1:] if e[0]=='func']
    if len(fs)!=1:raise Unsupported('one cascade function')
    f=fs[0]
    if [e for e in f[1:] if e[0]=='param']!=[['param',*(['i32']*4)]] or [e for e in f[1:] if e[0]=='result']!=[['result','i32']]:raise Unsupported('ABI')
    ls=[x for e in f[1:] if e[0]=='local' for x in e[1:]];n=len(ls)-1
    if n not in (4,8,16) or any(x!='i32' for x in ls):raise Unsupported('stage count')
    lp=[e for e in walk(f) if e[0]=='loop']
    if len(lp)!=1:raise Unsupported('one loop')
    sets=[e for e in lp[0][1:] if e[0]=='local.set' and 5<=int(e[1])<5+n]
    if len(sets)!=n:raise Unsupported('stage updates')
    coeff=[]
    for i,e in enumerate(sets):
        cs=[int(x[2][1],0)&MASK for x in walk(e[2]) if x[0]=='i32.mul' and len(x)==3 and x[2][0]=='i32.const']
        if i==0:cs=[x for x in cs if x!=0x9e3779b9]
        if len(cs)!=1:raise Unsupported('one coefficient per stage')
        coeff.append(cs[0])
    for kind in range(3):
        for r in range(1,32):
            expected=source(coeff,kind,r)[2]
            if normalize(bodyof(expected))==normalize(bodyof(f)):return dict(coeff=coeff,kind=kind,r=r,n=n)
    raise Unsupported('not a supported total cascade')
def build(spec,mode,seed=37,broken=False):
    coeff,kind,r,n=(spec[k] for k in ('coeff','kind','r','n'))
    if mode=='plain':return source(coeff,kind,r)
    limit=['i32.add',g(0),c(n-1)];body=[guard()]
    if mode=='scalar':
        body += [st(5+i,initial(i)) for i in range(n)];step=[]
        for i,cc in enumerate(coeff):
            val=scalar(kind,g(5+i),stream(g(4)) if i==0 else g(4+i),cc,r)
            active=['i32.and',['i32.ge_u',g(4),c(i)],['i32.lt_u',g(4),['i32.add',g(0),c(i)]]]
            step.append(st(5+n+i,['select',val,g(5+i),active]))
        step += [st(5+i,g(5+n+i)) for i in range(n)]
        return module(['i32']*(2*n+1),body+[loop(step,limit),*outputs([g(5+i) for i in range(n)])])
    m=n//4;rng=random.Random(seed);orders=[]
    for k in range(m):
        ids=list(range(4*k,4*k+4))
        if mode=='mixed':rng.shuffle(ids)
        orders.append(ids)
    for k,ids in enumerate(orders):
        init=['i32x4.add',['v128.xor',spl(g(1)),vc([(i+1)*0x10204081 for i in ids])],spl(g(2))]
        body.append(st(5+k,init))
    step=[]
    for k,ids in enumerate(orders):
        old=g(5+k);prev=g(4+k) if k else spl(stream(g(4)));idx=[]
        for i in ids:
            lane=(orders[k].index(i-1) if i%4 else (orders[k-1].index(i-1)+4 if k else 4))
            idx += list(range(lane*4,lane*4+4))
        pred=['i8x16.shuffle',*map(str,idx),old,prev];cc=vc([coeff[i] for i in ids]);tmp=5+m+k
        mix=['i32x4.add',['i32x4.mul',old,cc],pred] if kind==0 else (['i32x4.mul',['v128.xor',old,pred],cc] if kind==1 else ['i32x4.add',old,pred])
        step.append(st(tmp,mix))
        def rotate(x):return ['v128.or',['i32x4.shl',x,c(r)],['i32x4.shr_u',x,c(32-r)]]
        value=rotate(g(tmp)) if kind==0 else (['i32x4.add',g(tmp),rotate(old)] if kind==1 else ['v128.xor',rotate(g(tmp)),['i32x4.mul',old,cc]])
        phases=vc(ids);stop=vc([0]*4) if broken else phases
        mask=['v128.and',['i32x4.ge_u',spl(g(4)),phases],['i32x4.lt_u',spl(g(4)),['i32x4.add',spl(g(0)),stop]]]
        step.append(st(5+2*m+k,['v128.bitselect',value,old,mask]))
    step += [st(5+k,g(5+2*m+k)) for k in range(m)]
    vals=[['i32x4.extract_lane',str(orders[i//4].index(i)),g(5+i//4)] for i in range(n)]
    return module(['i32']+['v128']*(3*m),body+[loop(step,limit),*outputs(vals)])
def transform(src,dst,mode='mixed',seed=37):
    t=time.perf_counter();spec=parse_source(read(src));t1=time.perf_counter();out=build(spec,mode,seed);t2=time.perf_counter();compile(w.emit(out),dst);t3=time.perf_counter()
    return dict(spec,mode=mode,seed=seed,read_ms=(t1-t)*1000,build_ms=(t2-t1)*1000,compile_ms=(t3-t2)*1000,transform_ms=(t3-t)*1000)
def probe(src,dst):
    m=read(src);m.append(['export','"memory"',['memory','0']]);compile(w.emit(m),dst)
def extract(src):
    start=time.perf_counter();m=read(src);t1=time.perf_counter();loops=[e for e in walk(m) if e[0]=='loop']
    if len(loops)!=1:raise Unsupported('one pipeline loop')
    env={};packets=[]
    def resolve(e):
        if not isinstance(e,list):return e
        if e[0]=='local.get':return copy.deepcopy(env.get(e[1],e))
        if e[0] in ('local.set','local.tee'):
            val=resolve(e[2]);env[e[1]]=val;return val
        z=[e[0],*[resolve(x) for x in e[1:]]]
        if e[0]=='v128.bitselect':packets.append(z)
        return z
    for e in loops[0][1:]:resolve(e)
    coeff={};kinds=set();rotations=set();detail=[]
    for packet in packets:
        update,old,mask=packet[1:]
        candidates=[words(x) for x in walk(mask) if x[0]=='v128.const']
        phases=[x for x in candidates if len(set(x))==4 and max(x)<64]
        if not phases or any(x!=phases[0] for x in phases):raise Unsupported('phase mask pattern')
        ids=phases[0]
        cc=[words(x) for x in walk(update) if x[0]=='v128.const' and all(v>65536 and v&1 for v in words(x))]
        if not cc or any(x!=cc[0] for x in cc):raise Unsupported('coefficient vector')
        shifts=[int(x[2][1],0) for x in walk(update) if x[0]=='i32x4.shl' and x[2][0]=='i32.const']
        if not shifts or len(set(shifts))!=1:raise Unsupported('rotate form')
        kind={'v128.or':0,'i32x4.add':1,'v128.xor':2}.get(update[0])
        if kind is None:raise Unsupported('update form')
        kinds.add(kind);rotations.update(shifts)
        for i,c0 in zip(ids,cc[0]):
            if i in coeff:raise Unsupported('duplicate logical phase')
            coeff[i]=c0
        detail.append(dict(phases=ids,coeff=cc[0]))
    n=len(coeff)
    if n not in (4,8,16) or set(coeff)!=set(range(n)) or len(kinds)!=1 or len(rotations)!=1:raise Unsupported('incomplete pipeline')
    return dict(n=n,coeff=[coeff[i] for i in range(n)],kind=kinds.pop(),r=rotations.pop(),packets=detail,read_ms=(t1-start)*1000,extract_ms=(time.perf_counter()-t1)*1000)
def main():
    a=argparse.ArgumentParser();sub=a.add_subparsers(dest='cmd',required=True)
    t=sub.add_parser('transform');t.add_argument('source');t.add_argument('output');t.add_argument('--mode',choices=['plain','scalar','vector','mixed'],default='mixed');t.add_argument('--seed',type=int,default=37)
    t=sub.add_parser('recover');t.add_argument('source');t.add_argument('output')
    v=a.parse_args()
    if v.cmd=='transform':info=transform(v.source,v.output,v.mode,v.seed)
    else:info=extract(v.source);compile(w.emit(source(info['coeff'],info['kind'],info['r'])),v.output)
    print(json.dumps(info))
if __name__=='__main__':main()
