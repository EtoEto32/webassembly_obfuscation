"""Demand-driven scalarization with indices canonicalized modulo four.

No source expression, frame manifest, or generator metadata is consumed.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import time
import prototype as p

def canonical(items): return tuple(sorted((k,v%4) for k,v in items.items() if v%4))
def add(a,b,scale=1):
    z=Counter(dict(a))
    for k,v in b:z[k]+=scale*v
    return canonical(z)
def idx(n): return () if n%4==0 else (('',n%4),)
def index(e):
    if e[0]=='i32.const':return idx(int(e[1],0))
    if e[0] in ('i32.add','i32.sub'):return add(index(e[1]),index(e[2]),1 if e[0]=='i32.add' else -1)
    if e[0]=='i32.and':
        for a,b in [(e[1],e[2]),(e[2],e[1])]:
            if b[0]=='i32.const' and int(b[1],0)&3==3:return index(a)
    return ((p.emit(e),1),)
def iconst(i): return dict(i).get('',0) if all(k=='' for k,v in i) else None
def index_expr(i):
    value=p.const(0)
    for k,n in i:
        term=p.const(n) if k=='' else p.w.parse('(module '+k+')')[1]
        if k and n!=1:term=['i32.mul',term,p.const(n)]
        value=simplify(['i32.add',value,term])
    return ['i32.and',value,p.const(3)]
def vector_bytes(e):
    if e[0]!='v128.const':return None
    shape=e[1];bits={'i8x16':8,'i16x8':16,'i32x4':32,'i64x2':64}.get(shape)
    if bits is None:raise ValueError('Unsupported vector constant')
    data=[]
    for v in e[2:]:data.extend((int(v,0)&((1<<bits)-1)).to_bytes(bits//8,'little'))
    if len(data)!=16:raise ValueError('Bad vector constant')
    return data
def simplify(e):
    op=e[0]
    if len(e)==3 and op in p.BINARY:
        a,b=e[1:]
        if a[0]==b[0]=='i32.const':
            x,y=int(a[1],0),int(b[1],0)
            return p.const({'i32.add':lambda:x+y,'i32.sub':lambda:x-y,'i32.mul':lambda:x*y,'i32.and':lambda:x&y,'i32.or':lambda:x|y,'i32.xor':lambda:x^y}[op]())
        if op in ('i32.add','i32.or','i32.xor'):
            if a==p.const(0):return b
            if b==p.const(0):return a
        if op=='i32.sub' and b==p.const(0):return a
    return e

def scalarize(root):
    memo={};visits=0;max_terms=0
    def pick(values,i):
        k=iconst(i)
        if k is not None:return p.const(values[k])
        if len(set(values))==1:return p.const(values[0])
        answer=p.const(values[3]);expr=index_expr(i)
        for j in (2,1,0):answer=['select',p.const(values[j]),answer,['i32.eq',expr,p.const(j)]]
        return answer
    def shift_of(e):
        # Byte permutation (byte + 4*delta) & 15 preserves whole i32 lanes.
        data=vector_bytes(e)
        if data is not None:
            for r in range(4):
                if data==[(i+4*r)&15 for i in range(16)]:return idx(r)
            raise ValueError('Constant swizzle is not a cyclic word permutation')
        if e[0]!='v128.and':raise ValueError('Noncanonical byte bounds')
        a,b=e[1:]
        if vector_bytes(a)==[15]*16:a,b=b,a
        if vector_bytes(b)!=[15]*16 or a[0]!='i8x16.add':raise ValueError('Unproved permutation bounds')
        u,v=a[1:]
        if vector_bytes(v)==list(range(16)):u,v=v,u
        if vector_bytes(u)!=list(range(16)) or v[0]!='i8x16.splat':raise ValueError('Unproved byte permutation')
        s=v[1]
        if s[0]!='i32.shl' or s[2]!=p.const(2):raise ValueError('Byte movement not whole words')
        return index(s[1])
    def lane(v,i):
        nonlocal visits,max_terms
        visits+=1;max_terms=max(max_terms,len(i));key=(id(v),i)
        if key in memo:return memo[key]
        op=v[0]
        if op=='v128.const':out=pick(list(struct.unpack('<4I',bytes(vector_bytes(v)))),i)
        elif op=='i32x4.splat':out=v[1]
        elif op in ('i32x4.add','i32x4.sub','i32x4.mul','v128.and','v128.or','v128.xor'):
            scalar='i32.'+op.split('.')[1];out=simplify([scalar,lane(v[1],i),lane(v[2],i)])
        elif op=='v128.not':out=['i32.xor',lane(v[1],i),p.const(0xffffffff)]
        elif op in ('i32x4.shl','i32x4.shr_u'):out=['i32.'+op.split('.')[1],lane(v[1],i),v[2]]
        elif op=='i8x16.swizzle':out=lane(v[1],add(i,shift_of(v[2])))
        elif op=='i8x16.shuffle':
            indices=list(map(int,v[1:17]));a,b=v[17:19]
            if any(indices[4*j+k]!=indices[4*j]+k for j in range(4) for k in range(4)) or any(indices[4*j]%4 for j in range(4)):raise ValueError('Cross-word shuffle')
            k=iconst(i)
            if k is None:raise ValueError('Dynamic demand of fixed noncyclic shuffle')
            n=indices[4*k]//4;out=lane(a if n<4 else b,idx(n%4))
        else:raise ValueError('Unsupported vector demand '+op)
        memo[key]=out;return out
    if root[0]!='i32x4.extract_lane':raise ValueError('Expected one scalar observation')
    result=lane(root[2],idx(int(root[1])))
    return result,dict(demand_visits=visits,memo_entries=len(memo),maximum_index_terms=max_terms)

def scalar_dag_module(expr):
    """Preserve shared subexpressions instead of exponentially printing a tree."""
    cache={};body=[]
    def lower(e):
        if e[0] in ('local.get','i32.const'):return e
        key=id(e)
        if key in cache:return cache[key]
        value=[e[0],*[lower(x) if isinstance(x,list) else x for x in e[1:]]]
        i=len(body)+2;body.append(['local.set',str(i),value]);cache[key]=p.get(i);return cache[key]
    result=lower(expr)
    return '(module (func (export "run") (param i32 i32) (result i32) '+('(local i32)'*len(body))+''.join(p.emit(e) for e in body)+p.emit(result)+'))'

def recover(src,dst):
    begin=time.perf_counter();root=p.expanded(src,allow_vector=True);loaded=time.perf_counter();result,stats=scalarize(root);solved=time.perf_counter();p.compile_wat(scalar_dag_module(result),dst)
    return dict(stats,read_expand_ms=(loaded-begin)*1000,scalarize_ms=(solved-loaded)*1000,total_ms=(time.perf_counter()-begin)*1000)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();print(json.dumps(recover(a.source,a.output)))
if __name__=='__main__':main()
