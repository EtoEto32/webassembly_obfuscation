"""Idempotent-copy-compatible encodings; restricted real-Wasm prototype."""
import argparse, copy, importlib.util, json, random, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('cf_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
MASK=0xffffffff
def c(n):return ['i32.const',str(n if n<0x80000000 else n-0x100000000)]
def get(n):return ['local.get',str(n)]
def op(name,*xs):return ['i32.'+name,*xs]
def load(i):return ['i32.load',c(4*i)]
def store(i,x):return ['i32.store',c(4*i),x]
def add(*xs):
    v=xs[0]
    for x in xs[1:]:v=op('add',v,x)
    return v
def xor(*xs):
    v=xs[0]
    for x in xs[1:]:v=op('xor',v,x)
    return v
def sigma(x,shifts,last=False):return xor(*[op('shr_u' if last and i==2 else 'rotr',x,c(b)) for i,b in enumerate(shifts)])
def constants():
    text=(ROOT/'experiments/sha256-research-baseline/vendor/sha256.js').read_text()
    return [int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',re.search(r'var K = \[([\s\S]*?)\]',text)[1])]
def source():
    k=constants();assert len(k)==64
    # Params 0..7: H; 8..23: message. Locals 24..87: schedule;
    # 88..95: round state snapshot; 96,97: T1,T2.
    f=['func',['export','"compress"'],['param',*(['i32']*24)],['result',*(['i32']*8)],['local',*(['i32']*74)]]
    f.extend(store(i,get(i)) for i in range(8));f.append(['memory.copy',c(32),c(0),c(32)])
    for i in range(64):
        v=get(8+i) if i<16 else add(sigma(get(24+i-2),[17,19,10],True),get(24+i-7),sigma(get(24+i-15),[7,18,3],True),get(24+i-16))
        f.append(['local.set',str(24+i),v])
    a,b,cc,d,e,ff,g,h=[get(88+i) for i in range(8)]
    for i in range(64):
        f.extend(['local.set',str(88+j),load(8+j)] for j in range(8))
        ch=xor(g,op('and',e,xor(ff,g)));maj=xor(op('and',a,b),op('and',a,cc),op('and',b,cc))
        f.append(['local.set','96',add(h,sigma(e,[6,11,25]),ch,c(k[i]),get(24+i))])
        f.append(['local.set','97',add(sigma(a,[2,13,22]),maj)])
        f.extend(store(8+j,v) for j,v in enumerate([add(get(96),get(97)),a,b,cc,add(d,get(96)),e,ff,g]))
    f.extend(add(load(i),load(8+i)) for i in range(8))
    return q.w.emit(['module',['memory','1','1'],f])

def gates(layers=1,seed=211051):
    rng=random.Random(seed);gs=[]
    for _ in range(layers):
        order=list(range(8));rng.shuffle(order)
        for i in order:
            j,k=rng.sample([x for x in range(8) if x!=i],2)
            gs.append((i,j,k,rng.randrange(1,32),rng.randrange(1,32)))
    return gs
def shear_code(gs,base,linear=False,inverse=False):
    out=[]
    for i,j,k,r,s in reversed(gs) if inverse else gs:
        u,v=get(base+j),get(base+k)
        z=xor(op('rotl',u,c(r)),op('rotl',v,c(s))) if linear else xor(op('rotl',add(u,v),c(r)),op('and',u,op('rotl',v,c(s))))
        out.append(['local.set',str(base+i),xor(get(base+i),z)])
    return out
def helpers(gs,linear=False):
    fs=[]
    for i in range(8):
        f=['func',['result','i32'],['local',*(['i32']*8)]]
        f.extend(['local.set',str(j),xor(load(8+j),load(j))] for j in range(8))
        f.extend(shear_code(gs,0,linear,True));f.append(xor(load(i),get(i)));fs.append(f)
    for i in range(8):
        f=['func',['param','i32'],['local',*(['i32']*8)]]
        f.extend(['local.set',str(1+j),xor(load(8+j),load(j))] for j in range(8))
        f.extend(shear_code(gs,1,linear,True));f.append(['local.set',str(1+i),xor(get(0),load(i))])
        f.extend(shear_code(gs,1,linear));f.extend(store(8+j,xor(load(j),get(1+j))) for j in range(8));fs.append(f)
    return fs
ALLOWED={'i32.const','local.get','local.set','local.tee','i32.add','i32.sub','i32.mul','i32.and','i32.or','i32.xor','i32.shl','i32.shr_u','i32.rotl','i32.rotr','i32.load','i32.store'}
def addr(e):
    if len(e)!=2 or e[0]!='i32.const':raise ValueError('constant address required')
    return int(e[1],0)&MASK
def inspect(src):
    m=q.read(src)
    if any(e[0] not in ('type','func','memory','export') for e in m[1:]):raise ValueError('closed module required')
    fs=[e for e in m[1:] if e[0]=='func'];ms=[e for e in m[1:] if e[0]=='memory'];es=[e for e in m[1:] if e[0]=='export']
    if len(fs)!=1 or ms!=[['memory','1','1']] or es!=[['export','"compress"',['func','0']]]:raise ValueError('private one-page memory, single compress export required')
    f=fs[0];decl=[e for e in f[1:] if e[0] in ('type','param','result','local')];body=[e for e in f[1:] if e[0] not in ('type','param','result','local')]
    if [e for e in decl if e[0]=='param']!=[['param',*(['i32']*24)]] or [e for e in decl if e[0]=='result']!=[['result',*(['i32']*8)]]:raise ValueError('24-to-8 i32 profile')
    if any(any(t!='i32' for t in e[1:]) for e in decl if e[0]=='local'):raise ValueError('i32 locals only')
    prefix=[store(i,get(i)) for i in range(8)]+[['memory.copy',c(32),c(0),c(32)]]
    if body[:9]!=prefix:raise ValueError('initial H stores and exact disjoint copy required')
    counts={'loads':0,'stores':0}
    def check(e):
        if not isinstance(e,list) or e[0] not in ALLOWED:raise ValueError('unsupported body instruction')
        if e[0] in ('i32.load','i32.store'):
            expected=2 if e[0]=='i32.load' else 3
            if len(e)!=expected:raise ValueError('no load/store attributes')
            p=addr(e[1]);valid=range(0,64,4) if e[0]=='i32.load' else range(32,64,4)
            if p not in valid:raise ValueError('immutable H and bounded aligned W required')
            if p>=32:counts['loads' if e[0]=='i32.load' else 'stores']+=1
        for x in e[1:]:
            if isinstance(x,list):check(x)
    for e in body[9:]:check(e)
    return m,decl,body,counts
def transform(src,dst,mode='native',layers=1,seed=211051,linear=False):
    t=time.perf_counter();m,decl,body,counts=inspect(src);gs=gates(layers,seed)
    if mode not in ('native','repair'):raise ValueError('mode')
    def rewrite(e):
        if e[0]=='i32.load' and addr(e[1])>=32:return ['call',str(1+(addr(e[1])-32)//4)]
        if e[0]=='i32.store':return ['call',str(9+(addr(e[1])-32)//4),rewrite(e[2])]
        return [rewrite(x) if isinstance(x,list) else x for x in e]
    head=copy.deepcopy(body[:9]);extra=[]
    if mode=='repair':
        # Before the initial copy W is dead. Decode nevertheless to measure the
        # straightforward full repair policy, not an optimal baseline.
        f=['func',['local',*(['i32']*8)]]
        f.extend(['local.set',str(i),['call',str(1+i)]] for i in range(8));f.extend(store(8+i,get(i)) for i in range(8));extra.append(f)
        f=['func',['local',*(['i32']*8)]]
        f.extend(['local.set',str(i),xor(load(8+i),load(i))] for i in range(8));f.extend(shear_code(gs,0,linear));f.extend(store(8+i,xor(load(i),get(i))) for i in range(8));extra.append(f)
        head=body[:8]+[['call','17'],body[8],['call','18']]
    f=['func',*[e for e in decl if e[0]!='type'],*head,*[rewrite(e) for e in body[9:]]]
    module=['module',['memory','1','1'],f,*helpers(gs,linear),*extra,['export','"compress"',['func','0']]]
    q.compile(q.w.emit(module),dst)
    return {'mode':mode,'layers':layers,'seed':seed,'linear':linear,'gates':gs,'rewritten':counts,'elapsed_ms':1000*(time.perf_counter()-t)}
def probe(src,dst):
    m=q.read(src);m.append(['export','"memory"',['memory','0']]);q.compile(q.w.emit(m),dst)
if __name__=='__main__':
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
    b=sub.add_parser('source');b.add_argument('dst')
    b=sub.add_parser('transform');b.add_argument('src');b.add_argument('dst');b.add_argument('--mode',choices=['native','repair'],default='native');b.add_argument('--layers',type=int,choices=[1,2],default=1);b.add_argument('--seed',type=int,default=211051);b.add_argument('--linear',action='store_true')
    a=ap.parse_args()
    if a.command=='source':q.compile(source(),a.dst)
    else:print(json.dumps(transform(a.src,a.dst,a.mode,a.layers,a.seed,a.linear)))
