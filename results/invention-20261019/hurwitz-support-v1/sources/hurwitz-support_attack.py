"""Read operational code/data, then recover an equivalent Boolean ROBDD.
No source formula, seed, rewrite log, or generator metadata is read.
"""
import argparse
import json
import struct
import time
from pathlib import Path
import prototype as p

MASK=(1<<32)-1

def unquote(s):
    s=s[1:-1];out=bytearray();i=0
    while i<len(s):
        if s[i]!='\\':out.append(ord(s[i]));i+=1
        elif i+2<len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):out.append(int(s[i+1:i+3],16));i+=3
        else:out.append({'n':10,'r':13,'t':9,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
    return out

def extract(path):
    p.w.tool('wasm-validate',[path]);mod=p.c.read(path)
    if any(q[0] not in ('type','memory','data','func','export') for q in mod[1:]):raise ValueError('Unsupported module effects')
    funcs=[q for q in mod[1:] if q[0]=='func'];exports=[q for q in mod[1:] if q[0]=='export'];mems=[q for q in mod[1:] if q[0]=='memory']
    if len(funcs)!=1 or exports!=[['export','"run"',['func','0']]] or len(mems)!=1:raise ValueError('Unexpected interface')
    mem=bytearray(int(mems[0][1])*65536)
    for q in mod[1:]:
        if q[0]=='data':
            if q[1][0]!='i32.const':raise ValueError('Nonconstant data offset')
            pos=int(q[1][1]);b=b''.join(unquote(s) for s in q[2:]);mem[pos:pos+len(b)]=b
    f=funcs[0];params=[v for q in f[1:] if q[0]=='param' for v in q[1:]];res=[q for q in f[1:] if q[0]=='result']
    if params!=['i32','i32'] or res!=[['result','i32']]:raise ValueError('Signature')
    env={0:['local.get','0'],1:['local.get','1']}
    for q in f[1:]:
        if q[0]=='local':
            for t in q[1:]:env[len(env)]=['i32.const','0'] if t=='i32' else ['v128.const','i32x4','0','0','0','0']
    allowed={'i32.const','v128.const','i32.and','i32.or','i32.xor','i32.add','i32.shl','i32.shr_u','v128.load','i8x16.swizzle','i8x16.shuffle','i8x16.extract_lane_u','i32.ne','i32.eq','i32.eqz'}
    def expand(q):
        op=q[0]
        if op=='local.get':return env[int(q[1])]
        if op in ('local.set','local.tee'):
            v=expand(q[2]);env[int(q[1])]=v;return v if op=='local.tee' else None
        if op=='block':
            v=None
            for z in q[1:]:
                if z[0] not in ('type','result'):v=expand(z)
            return v
        if op not in allowed:raise ValueError('Unsupported instruction '+op)
        return [op,*[expand(z) if isinstance(z,list) else z for z in q[1:]]]
    result=None
    for q in f[1:]:
        if q[0] not in ('type','param','result','local'):result=expand(q)
    if result[0]=='i32.ne' and result[2]==['i32.const','0']:result=result[1]
    elif result[0]=='i32.eqz' and result[1][0]=='i32.eqz':result=result[1][1]
    else:raise ValueError('Expected public nonzero test')
    if result[:2]!=['i8x16.extract_lane_u','0']:raise ValueError('Expected lane0 observation')
    deps_memo={}
    def deps(q):
        key=id(q)
        if key in deps_memo:return deps_memo[key]
        op=q[0]
        if op=='local.get':out=[{32*int(q[1])+j} for j in range(32)]
        elif op=='i32.const':out=[set() for _ in range(32)]
        elif op in ('i32.shl','i32.shr_u') and q[2][0]=='i32.const':
            a=deps(q[1]);shift=int(q[2][1],0)&31;out=[]
            for j in range(32):
                k=j-shift if op=='i32.shl' else j+shift
                out.append(a[k] if 0<=k<32 else set())
        elif op in ('i32.and','i32.or','i32.xor','i32.add'):
            a,b=deps(q[1]),deps(q[2]);out=[];carry=set()
            for j in range(32):
                v=a[j]|b[j]
                if op=='i32.and' and any(z[0]=='i32.const' and not ((int(z[1],0)>>j)&1) for z in q[1:]):v=set()
                if op=='i32.or' and any(z[0]=='i32.const' and ((int(z[1],0)>>j)&1) for z in q[1:]):v=set()
                if op=='i32.add':carry=carry|v;v=carry
                out.append(v)
        else:raise ValueError('Address expression '+op)
        deps_memo[key]=out;return out
    def scalar(q,x):
        op=q[0]
        if op=='local.get':return (x>>(32*int(q[1])))&MASK
        if op=='i32.const':return int(q[1],0)&MASK
        a,b=scalar(q[1],x),scalar(q[2],x)
        if op=='i32.and':return a&b
        if op=='i32.or':return a|b
        if op=='i32.xor':return a^b
        if op=='i32.add':return (a+b)&MASK
        if op=='i32.shl':return (a<<(b&31))&MASK
        if op=='i32.shr_u':return a>>(b&31)
        raise ValueError(op)
    def vector(q,x):
        op=q[0]
        if op=='v128.const':
            if q[1]=='i32x4':return list(struct.pack('<4I',*[int(s,0)&MASK for s in q[2:]]))
            if q[1]=='i8x16':return [int(s,0)&255 for s in q[2:]]
            raise ValueError('v128 format')
        if op=='v128.load':
            off=sum(int(s.split('=')[1]) for s in q[1:-1] if isinstance(s,str) and s.startswith('offset='));addr=scalar(q[-1],x)+off
            if not 0<=addr<=len(mem)-16:raise ValueError('Potential load trap')
            return list(mem[addr:addr+16])
        if op=='i8x16.swizzle':
            a,b=vector(q[1],x),vector(q[2],x);return [a[i] if i<16 else 0 for i in b]
        if op=='i8x16.shuffle':
            both=vector(q[-2],x)+vector(q[-1],x);return [both[int(i)] for i in q[1:17]]
        raise ValueError('Vector expression '+op)
    supports={}
    def support(q):
        if id(q) in supports:return supports[id(q)]
        if q[0]=='v128.load':out=set().union(*deps(q[-1]))
        else:out=set().union(*(support(z) for z in q[1:] if isinstance(z,list)))
        supports[id(q)]=out;return out
    def small(q):
        s=sorted(support(q))
        if len(s)>3:raise ValueError('Factor support above public profile')
        table=[]
        for k in range(1<<len(s)):
            x=sum(((k>>j)&1)<<v for j,v in enumerate(s));v=vector(q,x)
            if v[5:]!=list(range(5,16)) or tuple(v[:5]) not in p.IDS:raise ValueError('Not an S5 permutation')
            table.append(p.IDS[tuple(v[:5])])
        return p.factor(s,table)
    def chain(q):
        if len(support(q))<=3:return [small(q)]
        if q[0]=='i8x16.swizzle':return chain(q[1])+[small(q[2])]
        raise ValueError('Unsupported product shape '+q[0])
    word=chain(result[2])
    return word

def reduce_support(word):
    out=list(word);moves=0;trials=0
    # Strict descent in the number of table entries. No seed or original word.
    for sweep in range(32):
        changed=False
        for j in range(len(out)-1):
            a,b=out[j:j+2]
            if len(set(a.support+b.support))>6:continue
            best=(a,b);sc=p.score(best)
            for d in (0,1):
                pair=p.move(a,b,d);trials+=1
                if p.score(pair)<sc:best=pair;sc=p.score(pair)
            if best!=(a,b):out[j:j+2]=best;moves+=1;changed=True
        if not changed:break
    return out,dict(moves=moves,trials=trials,sweeps=sweep+1,before_entries=p.score(word),after_entries=p.score(out))

class BDD:
    def __init__(self,node_limit=300000,seconds=20):
        self.nodes={};self.unique={};self.terminals={};self.values={};self.cache={};self.calls=0;self.limit=node_limit;self.deadline=time.perf_counter()+seconds
    def terminal(self,v):
        if v not in self.terminals:
            k=-len(self.terminals)-1;self.terminals[v]=k;self.values[k]=v
        return self.terminals[v]
    def node(self,v,a,b):
        if a==b:return a
        key=(v,a,b)
        if key not in self.unique:
            if len(self.nodes)>=self.limit:raise MemoryError('BDD node limit')
            k=len(self.nodes)+1;self.unique[key]=k;self.nodes[k]=key
        return self.unique[key]
    def apply(self,op,a,b):
        key=(op,a,b)
        if key in self.cache:return self.cache[key]
        self.calls+=1
        if self.calls%4096==0 and time.perf_counter()>self.deadline:raise TimeoutError('BDD wall limit')
        if a<0 and b<0:
            av,bv=self.values[a],self.values[b]
            if op=='step':v=('s',p.PERMS[av[1]][bv[1]])
            else:v=('b',{'and':av[1]&bv[1],'or':av[1]|bv[1],'xor':av[1]^bv[1]}[op])
            out=self.terminal(v)
        else:
            va=self.nodes[a][0] if a>0 else 999;vb=self.nodes[b][0] if b>0 else 999;v=min(va,vb)
            aa=self.nodes[a][1:] if va==v else (a,a);bb=self.nodes[b][1:] if vb==v else (b,b)
            out=self.node(v,self.apply(op,aa[0],bb[0]),self.apply(op,aa[1],bb[1]))
        self.cache[key]=out;return out
    def build_factor(self,f):
        def go(j,k):
            if j==len(f.support):return self.terminal(('p',f.table[k]))
            return self.node(f.support[j],go(j+1,k),go(j+1,k|(1<<j)))
        return go(0,0)
    def finish(self,root):
        memo={}
        def go(n):
            if n not in memo:
                if n<0:memo[n]=self.terminal(('b',int(self.values[n][1]!=0)))
                else:
                    v,a,b=self.nodes[n];memo[n]=self.node(v,go(a),go(b))
            return memo[n]
        return go(root)
    def recover(self,word):
        root=self.terminal(('s',0))
        for f in reversed(word):root=self.apply('step',self.build_factor(f),root)
        return self.finish(root)
    def source(self,t):
        op=t[0]
        if op=='v':return self.node(t[1],self.terminal(('b',0)),self.terminal(('b',1)))
        if op=='c':return self.terminal(('b',t[1]))
        if op=='not':return self.apply('xor',self.source(t[1]),self.terminal(('b',1)))
        return self.apply(op,self.source(t[1]),self.source(t[2]))
    def reachable(self,root):
        seen=set()
        def go(n):
            if n>0 and n not in seen:seen.add(n);go(self.nodes[n][1]);go(self.nodes[n][2])
        go(root);return seen
    def wasm(self,root):
        ids={};body=[]
        def go(n):
            if n<0:return f'(i32.const {self.values[n][1]})'
            if n not in ids:
                v,a,b=self.nodes[n];lo,hi=go(a),go(b);idx=len(ids)+2;ids[n]=idx
                body.append(f'(local.set {idx} (select {hi} {lo} {p.formula_wat(("v",v))}))')
            return f'(local.get {ids[n]})'
        ans=go(root)
        return '(module (func (export "run") (param i32 i32) (result i32) '+'(local i32)'*len(ids)+''.join(body)+ans+'))'

def recover(src,dst,reduce=False):
    start=time.perf_counter();word=extract(src);read_ms=(time.perf_counter()-start)*1000;stats={}
    start=time.perf_counter()
    if reduce:word,stats=reduce_support(word)
    reduction_ms=(time.perf_counter()-start)*1000;bdd=BDD();start=time.perf_counter();root=bdd.recover(word)
    analysis_ms=(time.perf_counter()-start)*1000
    p.c.compile_wat(bdd.wasm(root),dst)
    return dict(status='recovered',read_ms=read_ms,analysis_ms=analysis_ms,reduction_ms=reduction_ms,bdd_allocated=len(bdd.nodes),apply_calls=bdd.calls,output_nodes=len(bdd.reachable(root)),**stats)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--reduce',action='store_true');a=ap.parse_args();print(json.dumps(recover(a.source,a.output,a.reduce)))
