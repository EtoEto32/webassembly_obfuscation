"""Extract candidate source atoms from public recurrence; certify exactly."""
import itertools
import json
from pathlib import Path
import random
import sys
import time
import word
import screen
from shared import h,load
saved=sys.modules.get('transform');sys.modules['transform']=word.front
reader=load('bf_word_reader',h.ROOT/'research/bit-feedback/recover.py')
if saved is None:del sys.modules['transform']
else:sys.modules['transform']=saved


def variables(e):
    if e[0]=='v':return {e[1]}
    if len(e)==2:return set()
    return set().union(*(variables(a) for a in e[1:] if isinstance(a,tuple)))


def subtrees(e):
    out={e}
    if len(e)>2:
        for x in e[1:]:out|=subtrees(x)
    return out


def size(e):return 1 if len(e)==2 else 1+sum(size(x) for x in e[1:])


def calc(e,params,state):
    if e[0]=='c':return e[1]&h.MASK
    if e[0]=='p':return params[e[1]]
    if e[0]=='v':return state[e[1]]
    x,y=calc(e[1],params,state),calc(e[2],params,state);op=e[0]
    if op=='add':return (x+y)&h.MASK
    if op=='sub':return (x-y)&h.MASK
    if op=='mul':return (x*y)&h.MASK
    if op=='xor':return x^y
    if op=='and':return x&y
    if op=='or':return x|y
    if op=='shl':return (x<<(y%32))&h.MASK
    if op=='shr_u':return x>>(y%32)
    if op=='rotl':return ((x<<(y%32))|(x>>((-y)%32)))&h.MASK
    if op=='rotr':return ((x>>(y%32))|(x<<((-y)%32)))&h.MASK
    raise ValueError(op)


def canon(e):
    if len(e)==2:return e
    op=e[0];x,y=canon(e[1]),canon(e[2])
    if op in ('add','mul','xor','and','or') and repr(x)>repr(y):x,y=y,x
    return (op,x,y)


def bpoly(e):
    e=canon(e)
    if e==('c',0):return set()
    if e==('c',h.MASK):return {()}
    if e[0] not in ('xor','and','or'):return {(e,)}
    x,y=bpoly(e[1]),bpoly(e[2]);prod=set()
    if e[0] in ('and','or'):
        for u in x:
            for v in y:
                term=tuple(sorted(set(u+v),key=repr))
                if term in prod:prod.remove(term)
                else:prod.add(term)
    return x^y if e[0]=='xor' else prod if e[0]=='and' else x^y^prod


def candidate_update(fs,states):
    # Deliberately reuse only the publicly documented N, never source metadata.
    polys=word.p.anf(word.p.N3,3);err=[('xor',('v',i),f) for i,f in zip(states,fs)];out=[]
    for f,poly in zip(fs,polys):
        z=('c',0)
        for mon in sorted(poly):
            term=('c',h.MASK)
            for atom in mon:term=('and',term,err[atom//32])
            z=('xor',z,term)
        out.append(('xor',f,z))
    return out


def congruent(e):
    if len(e)==2:return True
    if e[0] in ('rotl','rotr','shr_u','shr_s') and variables(e[1]):return False
    if e[0]=='shl' and e[2][0]!='c':return False
    return all(congruent(x) for x in e[1:])


def run(binary,output):
    start=time.perf_counter();np,result,eq,rounds=reader.expressions(binary);read_ms=1000*(time.perf_counter()-start)
    counters={i for i,e in eq.items() if e==('sub',('v',i),('c',1))}
    states=set().union(*(variables(e) for i,e in eq.items() if i not in counters))-counters
    if len(states)!=3 or not states<=set(eq) or not variables(result)<=states:raise ValueError('Not three recurrent words')
    if rounds<128:raise ValueError('Insufficient word lift rounds')
    assert screen.check(3,word.p.N3,list(screen.triangular(3)))['bound']==4
    pool=set().union(*(subtrees(eq[i]) for i in states));pool={e for e in pool if size(e)<=9 and congruent(e)};rng=random.Random(20261023)
    probes=[([rng.getrandbits(32) for _ in range(np)],{i:rng.getrandbits(32) for i in states}) for _ in range(8)]
    expected=[[calc(eq[i],x,s) for i in sorted(states)] for x,s in probes];tried=0;start2=time.perf_counter();found=None
    for order in itertools.permutations(sorted(states)):
        options=[sorted([e for e in pool if variables(e)<=set(order[:j])],key=lambda e:(size(e),repr(e))) for j in range(3)]
        for fs in itertools.product(*options):
            tried+=1
            if tried%2048==0 and time.perf_counter()-start2>30:raise TimeoutError('Candidate search 30 seconds')
            rhs=candidate_update(fs,order);lookup=dict(zip(order,rhs))
            if any([calc(lookup[i],x,s) for i in sorted(states)]!=target for (x,s),target in zip(probes,expected)):continue
            if all(bpoly(lookup[i])==bpoly(eq[i]) for i in states):found=(order,fs);break
        if found:break
    if not found:raise ValueError('No exact source-atom certificate')
    order,fs=found;slots={i:np+j for j,i in enumerate(order)}
    def emit(e):
        if e[0]=='v':return f'(local.get {slots[e[1]]})'
        if e[0]=='p':return f'(local.get {e[1]})'
        if e[0]=='c':return f'(i32.const {e[1]})'
        return f'(i32.{e[0]} {emit(e[1])} {emit(e[2])})'
    body=''.join(f'(local.set {slots[i]} {emit(f)})' for i,f in zip(order,fs));text=f'(module (func (export "run") (param {" ".join(["i32"]*np)}) (result i32) (local i32 i32 i32) {body} {emit(result)}))'
    analysis_ms=1000*(time.perf_counter()-start2);emit_start=time.perf_counter()
    h.save(text,output);opt=Path(output).with_name(Path(output).stem+'-O3.wasm');h.w.tool('wasm-opt',[output,'-O3','-o',opt]);h.w.tool('wasm-validate',[opt])
    return {'status':'recovered','read_ms':read_ms,'analysis_ms':analysis_ms,'emit_ms':1000*(time.perf_counter()-emit_start),'candidates_tried':tried,'order':order,'recovered_functions':fs,'exact_boolean_certificate':True,'output':str(Path(output).resolve())}


if __name__=='__main__':
    res=run(sys.argv[1],sys.argv[2]);Path(sys.argv[2]).with_suffix('.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
