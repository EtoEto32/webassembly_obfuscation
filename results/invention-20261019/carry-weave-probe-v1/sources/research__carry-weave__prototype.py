"""Mask-partitioned carry-save forests. Established CSA/MBA identities, experimental planning."""
import argparse,collections,hashlib,importlib.util,json,random,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('carry_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
w=q.w;read=q.read;compile=q.compile;save=q.save;digest=q.digest;tool=q.tool;MASK=0xffffffff
class Unsupported(ValueError):pass
def c(x):return ['i32.const',str(x&MASK)]
def g(x):return ['local.get',str(x)]
def vc(xs):return ['v128.const','i32x4',*map(lambda x:str(x&MASK),xs)]
def module(body,locals_=()):return ['module',['func',['export','"run"'],['param','i32','i32','i32'],['result','i32'],*([['local',*locals_]] if locals_ else []),*body]]
def sumexpr(xs):
    if not xs:return c(0)
    if len(xs)==1:return xs[0]
    k=len(xs)//2;return ['i32.add',sumexpr(xs[:k]),sumexpr(xs[k:])]

class Pool:
    def __init__(self):self.nodes=[];self.ids={}
    def intern(self,t):
        if t not in self.ids:self.ids[t]=len(self.nodes);self.nodes.append(t)
        return self.ids[t]
    def const(self,n):return self.intern(('const',n&MASK))
    def op(self,op,*args):
        if op=='xor':
            count=collections.Counter()
            def add(a):
                t=self.nodes[a]
                if t[0]=='xor':
                    for b in t[1:]:add(b)
                else:count[a]^=1
            for a in args:add(a)
            args=tuple(sorted(a for a,k in count.items() if k and self.nodes[a]!=('const',0)))
            if not args:return self.const(0)
            if len(args)==1:return args[0]
        elif op in ('and','or','mul','add'):args=tuple(sorted(args))
        if op=='and':
            if any(self.nodes[a]==('const',0) for a in args):return self.const(0)
            if self.nodes[args[0]]==('const',MASK):return args[1]
            if self.nodes[args[1]]==('const',MASK):return args[0]
        return self.intern((op,*args))
    def expression(self,i):
        t=self.nodes[i]
        if t[0]=='const':return c(t[1])
        if t[0]=='arg':return g(t[1])
        args=[self.expression(x) for x in t[1:]]
        if t[0]=='xor':
            a=args[0]
            for b in args[1:]:a=['i32.xor',a,b]
            return a
        return ['i32.'+t[0],*args]
    def text(self,i):return w.emit(self.expression(i))

OPS={'add','sub','mul','and','or','xor','shl','shr_u','shr_s','rotl','rotr'}
def parse(src,vector=False):
    m=read(src)
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise Unsupported('pure module')
    fs=[x for x in m[1:] if x[0]=='func'];ex=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]]:raise Unsupported('one run export')
    f=fs[0];types=lambda name:[t for e in f[1:] if e[0]==name for t in e[1:]]
    if types('param')!=['i32']*3 or types('result')!=['i32']:raise Unsupported('ABI')
    ls=types('local')
    if any(t not in (('i32','v128') if vector else ('i32',)) for t in ls):raise Unsupported('local type')
    p=Pool();env={i:p.intern(('arg',i)) for i in range(3)};env.update({i+3:tuple(p.const(0) for _ in range(4)) if t=='v128' else p.const(0) for i,t in enumerate(ls)});stack=[]
    def resolve(e):
        op=e[0]
        if op=='local.get':return env[int(e[1])]
        if op in ('local.set','local.tee'):
            val=resolve(e[2]) if len(e)==3 else stack.pop();env[int(e[1])]=val;return val if op=='local.tee' else None
        if op=='i32.const':return p.const(int(e[1],0))
        if op.startswith('i32.') and op[4:] in OPS:return p.op(op[4:],*[resolve(x) for x in e[1:]])
        if not vector:raise Unsupported('source instruction '+op)
        if op=='v128.const':
            b=bytes(q.vconst(e));return tuple(p.const(int.from_bytes(b[j:j+4],'little')) for j in range(0,16,4))
        if op=='i32x4.splat':return (resolve(e[1]),)*4
        if op=='i32x4.replace_lane':
            a=list(resolve(e[2]));a[int(e[1])]=resolve(e[3]);return tuple(a)
        if op=='i32x4.extract_lane':return resolve(e[2])[int(e[1])]
        if op=='v128.not':return tuple(p.op('xor',a,p.const(MASK)) for a in resolve(e[1]))
        if op in ('v128.and','v128.or','v128.xor','i32x4.add','i32x4.mul'):
            a,b=map(resolve,e[1:]);return tuple(p.op(op.split('.')[1],x,y) for x,y in zip(a,b))
        if op in ('i32x4.shl','i32x4.shr_u'):
            a=resolve(e[1]);b=resolve(e[2]);return tuple(p.op(op.split('.')[1],x,b) for x in a)
        if op=='i8x16.shuffle':
            ix=list(map(int,e[1:17]));ab=resolve(e[17])+resolve(e[18]);out=[]
            for j in range(0,16,4):
                if ix[j]%4 or ix[j:j+4]!=list(range(ix[j],ix[j]+4)):raise Unsupported('nonword shuffle')
                out.append(ab[ix[j]//4])
            return tuple(out)
        raise Unsupported('target instruction '+op)
    for e in f[1:]:
        if e[0] in ('type','param','result','local'):continue
        a=resolve(e)
        if a is not None:stack.append(a)
    if len(stack)!=1 or not isinstance(stack[0],int):raise Unsupported('one scalar result')
    return p,stack[0]

def frontier(p,root):
    out=collections.Counter()
    def visit(i,k=1):
        t=p.nodes[i]
        if t[0]=='add':visit(t[1],k);visit(t[2],k)
        elif t!=('const',0):out[i]+=k
    visit(root);return out

def transform(src,dst,mode='splitcsa',seed=37,broken=False):
    start=time.perf_counter();p,r=parse(src);terms=[i for i,k in frontier(p,r).items() for _ in range(k)]
    if not 4<=len(terms)<=128:raise Unsupported('4..128 additive terms')
    exprs=[p.expression(i) for i in terms];t1=time.perf_counter()
    if mode=='plain':body=[sumexpr(exprs)];locals_=[];compressors=0
    else:
        rng=random.Random(seed);body=[];locals_=[]
        def emit(e,typ):
            i=3+len(locals_);locals_.append(typ);body.append(['local.set',str(i),e]);return g(i)
        values=[emit(e,'i32') for e in exprs]
        if mode.startswith('split'):
            pieces=[]
            for e in values:
                mask=rng.randrange(1,1<<32);pieces.extend([['i32.and',e,c(mask)],['i32.and',e,c(mask^MASK)]])
            rng.shuffle(pieces);values=pieces
        values += [c(0)]*((-len(values))%4);vectors=[]
        for j in range(0,len(values),4):
            v=vc([0]*4)
            for lane,e in enumerate(values[j:j+4]):v=['i32x4.replace_lane',str(lane),v,e]
            vectors.append(emit(v,'v128'))
        compressors=0
        if mode in ('csa','splitcsa'):
            while len(vectors)>2:
                if mode=='splitcsa':rng.shuffle(vectors)
                a,b,d=vectors[:3];vectors=vectors[3:];x=emit(['v128.xor',a,b],'v128')
                s=emit(['v128.xor',x,d],'v128');major=['v128.or',['v128.and',a,b],['v128.and',x,d]]
                carry=emit(['i32x4.shl',major,c(0 if broken else 1)],'v128');vectors.extend((s,carry));compressors+=1
        while len(vectors)>1:vectors=[emit(['i32x4.add',vectors[0],vectors[1]],'v128'),*vectors[2:]]
        body.append(sumexpr([['i32x4.extract_lane',str(i),vectors[0]] for i in range(4)]))
    t2=time.perf_counter();compile(w.emit(module(body,locals_)),dst);end=time.perf_counter()
    return dict(mode=mode,seed=seed,terms=len(terms),compressors=compressors,read_ms=(t1-start)*1000,build_ms=(t2-t1)*1000,compile_ms=(end-t2)*1000,transform_ms=(end-start)*1000)

def recover(src,dst=None):
    start=time.perf_counter();p,r=parse(src,True);t1=time.perf_counter();items=frontier(p,r);pairs=[]
    for carry,t in enumerate(list(p.nodes)):
        if t[0]!='shl' or p.nodes[t[2]]!=('const',1):continue
        m=p.nodes[t[1]]
        if m[0]!='or':continue
        for ab,xd in ((m[1],m[2]),(m[2],m[1])):
            aa,bb=p.nodes[ab],p.nodes[xd]
            if aa[0]!='and' or bb[0]!='and':continue
            a,b=aa[1:];xor=p.op('xor',a,b)
            for x,d in ((bb[1],bb[2]),(bb[2],bb[1])):
                if x==xor:pairs.append((p.op('xor',a,b,d),carry,(a,b,d)))
    undone=0;rounds=0
    while True:
        changed=False;rounds+=1
        for s,carry,args in reversed(pairs):
            count=min(items[s],items[carry])
            if count>0:
                items[s]-=count;items[carry]-=count
                for a in args:
                    if p.nodes[a]!=('const',0):items[a]+=count
                undone+=count;changed=True
        if not changed:break
        if rounds>len(pairs)+1:raise Unsupported('nonterminating frontier')
    merged=0
    while True:
        pieces={};changed=False
        for i,k in list(items.items()):
            if k<=0:continue
            t=p.nodes[i]
            if t[0]!='and':continue
            for base,mask in ((t[1],t[2]),(t[2],t[1])):
                if p.nodes[mask][0]=='const':pieces[(base,p.nodes[mask][1])]=i
        for (base,mask),i in pieces.items():
            j=pieces.get((base,mask^MASK));count=min(items[i],items[j]) if j is not None else 0
            if count>0:items[i]-=count;items[j]-=count;items[base]+=count;merged+=count;changed=True
        if not changed:break
    terms=sorted(p.text(i) for i,k in items.items() for _ in range(k) if k>0)
    info=dict(terms=terms,compressors_undone=undone,partitions_merged=merged,rounds=rounds,nodes=len(p.nodes),read_ms=(t1-start)*1000,recover_ms=(time.perf_counter()-t1)*1000)
    if dst is not None:compile(w.emit(module([sumexpr([w.parse(t) for t in terms])])),dst)
    return info

def main():
    a=argparse.ArgumentParser();a.add_argument('action',choices=['transform','recover']);a.add_argument('source');a.add_argument('output');a.add_argument('--mode',choices=['plain','packed','csa','splitadd','splitcsa'],default='splitcsa');a.add_argument('--seed',type=int,default=37);v=a.parse_args()
    print(json.dumps(transform(v.source,v.output,v.mode,v.seed) if v.action=='transform' else recover(v.source,v.output)))
if __name__=='__main__':main()
