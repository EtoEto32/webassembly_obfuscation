"""Public benchmarks and independent expected source operations."""
import prototype as p
c=p.c;g=p.g;op=p.op
def store(width,addr,value,offset=0):return [ {1:'i32.store8',2:'i32.store16',4:'i32.store'}[width],f'offset={offset}',addr,value]
def iff(cond,a,b=None):return ['if',cond,['then',*a],*([['else',*b]] if b is not None else [])]
def models():
    # Signature (p,q,n,value,condition). All source expressions are total.
    a,b,n,v,t=[g(i) for i in range(5)]
    return {
      'byte': [iff(t,[store(1,a,v)],[store(1,b,op('i32.xor',v,c(165)))])],
      'wide': [iff(op('i32.lt_u',v,n),[store(4,a,op('i32.mul',v,c(2654435761)),7),store(2,b,n,1)],
                     [store(2,b,op('i32.xor',v,n),3),store(1,a,t)])],
      'nested': [iff(t,[store(1,a,v),iff(op('i32.and',v,c(1)),[store(4,b,n,2)],[store(2,a,n,11)])],
                      [store(4,a,op('i32.add',v,n)),store(1,b,v)])],
      'bulk': [iff(t,[op('memory.copy',a,b,n),store(4,a,v,4)],
                     [op('memory.fill',b,v,n),store(1,a,op('i32.shr_u',v,c(8)))])]
    }
def module(body):
    return ['module',['memory','0','2'],['export','"memory"',['memory','0']],
            ['func',['export','"run"'],['param',*['i32']*5],['result','i32'],*body,op('i32.xor',g(3),g(2))]]
