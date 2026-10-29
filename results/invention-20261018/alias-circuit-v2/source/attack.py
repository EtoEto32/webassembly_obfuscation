"""Recover the alias helper's relation and emit a scalar circuit from actual Wasm.

No source expression, generation DAG, mapping, or target oracle is an input.
This bounded, structural attack refuses unsupported optimized bodies.
"""
import argparse
import json
from pathlib import Path
import time
from compile import parse, emit, tool

UNSET=object()


class Heap:
    def __init__(self):self.cells=[];self.reads=0;self.writes=0
    def new(self,fields):
        self.cells.append(list(fields));return len(self.cells)-1
    def get(self,p,k):
        x=self.cells[p][k];self.reads+=1
        if x is UNSET:raise ValueError('Read of preexisting scratch field: quotient unsupported')
        return x
    def set(self,p,k,v):self.cells[p][k]=v;self.writes+=1


def declarations(f,kind):return [x for x in f[2:] if isinstance(x,list) and x[0]==kind]
def body(f):return [x for x in f[2:] if isinstance(x,list) and x[0] not in ['type','param','result','local']]


def evaluate(f,args,h):
    env={p[1]:v for p,v in zip(declarations(f,'param'),args)}
    env.update({p[1]:None for p in declarations(f,'local')})
    def ev(x):
        op=x[0]
        if op=='local.get':return env[x[1]]
        if op in ('local.set','local.tee'):
            v=ev(x[2]);env[x[1]]=v;return v if op=='local.tee' else None
        if op=='ref.as_non_null':
            v=ev(x[1])
            if v is None:raise ValueError('Unexpected null')
            return v
        if op=='struct.new_default':return h.new([UNSET])
        if op=='struct.new':return h.new([ev(y) for y in x[2:]])
        if op=='struct.get':return h.get(ev(x[3]),int(x[2]))
        if op=='struct.set':h.set(ev(x[3]),int(x[2]),ev(x[4]));return None
        if op=='ref.eq':return int(ev(x[1])==ev(x[2]))
        if op=='if':
            xs=x[1:]
            if xs[0][0]=='result':xs=xs[1:]
            return ev(xs[1][1] if ev(xs[0]) else xs[2][1])
        raise ValueError('Unsupported helper opcode '+op)
    r=None
    for x in body(f):r=ev(x)
    return r


def partitions(n):
    if n==0:yield ();return
    for p in partitions(n-1):
        for v in range(max(p,default=-1)+2):yield p+(v,)


def recover(src,out):
    if out.exists():raise ValueError('Refuse overwrite')
    t=time.perf_counter();m=parse(tool('wasm-dis',[src]));fs=[x for x in m[1:] if x[0]=='func']
    exports=[x for x in m[1:] if x[0]=='export']
    if exports!=[['export','"run"',['func',exports[0][2][1]]]]:raise ValueError('Expected sole run export')
    name=exports[0][2][1];main=next(x for x in fs if x[1]==name)
    roles={};evidence=[]
    for f in fs:
        if f is main:continue
        ps=declarations(f,'param');rs=declarations(f,'result')
        types=[x[2] for x in ps]
        if len(ps)==2 and all(isinstance(x,list) and x[0]=='ref' for x in types):
            # No equality/if in the transfer: only equivariant identity and field operations.
            allowed={'local.get','local.set','local.tee','ref.as_non_null','struct.new_default','struct.new','struct.get','struct.set'}
            def check(x):
                if x[0] not in allowed:raise ValueError('Gate outside quotient profile: '+x[0])
                for y in x[1:]:
                    if isinstance(y,list):check(y)
            for x in body(f):check(x)
            rows=[]
            for p in partitions(4):
                h=Heap();cs=[h.new([UNSET]) for _ in range(max(p)+1)]
                a=h.new([cs[p[0]],cs[p[1]]]);b=h.new([cs[p[2]],cs[p[3]]])
                r=evaluate(f,[a,b],h);v=int(h.get(r,0)==h.get(r,1))
                x,y=int(p[0]==p[1]),int(p[2]==p[3])
                rows.append({'partition':p,'inputs':[x,y],'output':v,'heap_objects':len(h.cells)})
            if any(r['output']!=1-(r['inputs'][0]&r['inputs'][1]) for r in rows):
                raise ValueError('Recovered helper is not NAND')
            roles[f[1]]='nand';evidence.append({'function':f[1],'classification':'nand','partitions':rows})
        elif types==['i32'] and rs[0][1][0]=='ref':
            for b in (0,1):
                h=Heap();r=evaluate(f,[b],h)
                if int(h.get(r,0)==h.get(r,1))!=b:raise ValueError('Encoder mismatch')
            roles[f[1]]='enc'
        elif len(ps)==1 and isinstance(types[0],list) and rs==[['result','i32']]:
            for b in (0,1):
                h=Heap();a=h.new([UNSET]);c=a if b else h.new([UNSET]);p=h.new([a,c])
                if evaluate(f,[p],h)!=b:raise ValueError('Decoder mismatch')
            roles[f[1]]='dec'
        else:raise ValueError('Unknown helper signature')
    if sorted(roles.values())!=['dec','enc','nand']:raise ValueError('Expected three verified helpers')
    calls={'nand':0,'enc':0,'dec':0}
    def cv(x):
        op=x[0]
        if op=='ref.as_non_null':return cv(x[1])
        if op=='call':
            role=roles[x[1]];calls[role]+=1;args=[cv(y) for y in x[2:]]
            if role=='nand':return ['i32.xor',['i32.and',*args],['i32.const','1']]
            if role=='dec':return args[0]
            a=args[0]
            if not (a in (['i32.const','0'],['i32.const','1']) or
                    (a[0]=='i32.and' and ['i32.const','1'] in a[1:])):
                raise ValueError('Encoder input not certified as a bit')
            return a
        if op not in ('local.get','local.set','local.tee','i32.const','i32.and','i32.or','i32.xor','i32.shl','i32.shr_u'):
            raise ValueError('Unsupported main opcode '+op)
        return [cv(y) if isinstance(y,list) else y for y in x]
    result=['module',['func','$run',['export','"run"'],*declarations(main,'param'),['result','i32'],
             *[['local',x[1],'i32'] for x in declarations(main,'local')],*[cv(x) for x in body(main)]]]
    wp=Path(str(out)+'.wat');wp.write_text(emit(result),encoding='utf-8');tool('wat2wasm',[wp,'-o',out],True)
    tool('wasm-validate',[out],True)
    report={'status':'recovered','helper_evidence':evidence,'calls':calls,'seconds':time.perf_counter()-t,
            'bytes':out.stat().st_size,'input':str(src),'output':str(out),
            'limits':'Structural single-function profile; helper identity partition quotient. Not general heap inference.'}
    Path(str(out)+'.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();print(json.dumps(recover(a.input,a.output)))
