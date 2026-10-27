"""Restricted 3-node modular word lift of the exhaustive Boolean corrector."""
import argparse
import json
from pathlib import Path
import time
import prototype as p
from shared import h,load
front=load('bf_word_front',h.ROOT/'research/bit-feedback/transform.py')


def source(src):
    mod,np,nodes,result=front.source(src)
    if len(nodes)!=3:raise ValueError('Exactly three operation nodes in this gate')
    for op,a,b in nodes:
        if op in ('rotl','rotr','shr_u','shr_s') and a[0]=='n':raise ValueError('Internal noncongruent operation')
    return np,nodes,result


def expressions(np,nodes,mode):
    def ref(r):return ('p',r[1]) if r[0]=='p' else ('v',r[1]) if r[0]=='n' else ('c',r[1])
    f=[(op,ref(a),ref(b)) for op,a,b in nodes]
    if mode=='pipeline':return f
    e=[('xor',('v',i),f[i]) for i in range(3)]
    def anf(poly):
        acc=('c',0)
        for mon in sorted(poly):
            term=('c',0xffffffff)
            for atom in mon:term=('and',term,e[atom//32])
            acc=('xor',acc,term)
        return acc
    return [('xor',f[i],anf(poly)) for i,poly in enumerate(p.anf(p.N3,3))]


def wat(e,np,old):
    if e[0]=='c':return f'(i32.const {e[1]})'
    if e[0]=='p':return f'(local.get {e[1]})'
    if e[0]=='v':return f'(local.get {old+e[1]})'
    return f'(i32.{e[0]} {wat(e[1],np,old)} {wat(e[2],np,old)})'


def render(np,nodes,result,mode,initial=(0,0,0),width=32):
    if width!=32:raise ValueError('Wasm emission is fixed i32')
    rounds=128 if mode=='feedback' else 3;old=np;new=np+3;counter=np+6;parts=[]
    for i,v in enumerate(initial):parts.append(f'(local.set {old+i} (i32.const {v}))')
    init=''.join(parts);steps=''.join(f'(local.set {new+i} {wat(expr,np,old)})' for i,expr in enumerate(expressions(np,nodes,mode)))
    copies=''.join(f'(local.set {old+i} (local.get {new+i}))' for i in range(3));out=('v',result[1]) if result[0]=='n' else result
    return f'(module (func (export "run") (param {" ".join(["i32"]*np)}) (result i32) (local {" ".join(["i32"]*7)}) {init} (local.set {counter} (i32.const {rounds})) (loop {steps} {copies} (br_if 0 (local.tee {counter} (i32.sub (local.get {counter}) (i32.const 1))))) {wat(out,np,old)}))'


def transform(src,dest,mode='feedback',initial=(0,0,0)):
    start=time.perf_counter();np,nodes,result=source(src);h.save(render(np,nodes,result,mode,initial),dest)
    return {'mode':mode,'rounds':128 if mode=='feedback' else 3,'np':np,'nodes':nodes,'result':result,'initial':initial,'elapsed_ms':1000*(time.perf_counter()-start),'memory_bytes':0}


def step(nodes,params,state,width):
    mask=(1<<width)-1;f=[front.calc(node,state,params,width) for node in nodes];e=[s^v for s,v in zip(state,f)];out=list(f)
    for bit in range(width):
        index=sum(((e[i]>>bit)&1)<<i for i in range(3));c=p.N3[index]
        for i in range(3):out[i]^=((c>>i)&1)<<bit
    return [v&mask for v in out]


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--mode',choices=['pipeline','feedback'],default='feedback');q=ap.parse_args();print(json.dumps(transform(q.input,q.output,q.mode),indent=2))
