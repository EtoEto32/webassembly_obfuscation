"""Recover evaluation at k=0 after checking output cancellation modulo 2^32.

Track only coefficient divisibility and the constant coefficient DAG. No source
expression, generator metadata, degree bound, or private values are needed.
"""
import argparse
import json
import struct
import time
import prototype as p


def v2(n):
    n &= p.MASK
    return 32 if not n else (n & -n).bit_length()-1


def simp(op,a,b):
    if a[0] == b[0] == 'i32.const':
        x,y=int(a[1],0),int(b[1],0)
        return p.const({'i32.add':lambda:x+y,'i32.sub':lambda:x-y,'i32.mul':lambda:x*y}[op]())
    if op == 'i32.add':
        if a == p.const(0): return b
        if b == p.const(0): return a
    if op == 'i32.sub' and b == p.const(0): return a
    if op == 'i32.mul':
        if a == p.const(0) or b == p.const(0): return p.const(0)
        if a == p.const(1): return b
        if b == p.const(1): return a
    return [op,a,b]


def vector_words(e):
    if e[0] != 'v128.const': return None
    bits={'i8x16':8,'i16x8':16,'i32x4':32,'i64x2':64}.get(e[1])
    if bits is None: raise ValueError('Noninteger vector constant')
    data=b''.join((int(v,0)&((1<<bits)-1)).to_bytes(bits//8,'little') for v in e[2:])
    if len(data)!=16: raise ValueError('Vector constant width')
    return list(struct.unpack('<4I',data))


def project(root):
    scalar_memo={};vector_memo={};visits=0;max_degree=0;convolutions=0
    def scalar(e):
        key=id(e)
        if key in scalar_memo:return scalar_memo[key]
        op=e[0]
        if op=='i32.const': out=v2(int(e[1],0))
        elif op=='local.get': out=0
        elif op in ('i32.add','i32.sub'): out=min(scalar(e[1]),scalar(e[2]))
        elif op=='i32.mul':out=min(32,scalar(e[1])+scalar(e[2]))
        elif op=='i32.shl' and e[2][0]=='i32.const':out=min(32,scalar(e[1])+(int(e[2][1],0)&31))
        elif op in ('i32.shr_u','i32.rotl','i32.rotr','i32.and','i32.or','i32.xor'):
            # These are k-independent, total scalar expressions, not vector ops.
            scalar(e[1]);scalar(e[2]);out=0
        else:raise ValueError('Unsupported scalar operation '+op)
        scalar_memo[key]=out;return out
    def vector(e):
        nonlocal visits,max_degree,convolutions
        visits+=1;key=id(e)
        if key in vector_memo:return vector_memo[key]
        op=e[0];words=vector_words(e)
        if words is not None:
            d=(words[1]-words[0])&p.MASK
            if words != [(words[0]+i*d)&p.MASK for i in range(4)]:raise ValueError('Non-affine vector constant')
            c=(words[0]-d)&p.MASK;out=p.const(c);vals={0:v2(c),1:v2(d)}
        elif op=='i32x4.splat':out=e[1];vals={0:scalar(out)}
        elif op in ('i32x4.add','i32x4.sub','i32x4.mul'):
            a,va=vector(e[1]);b,vb=vector(e[2]);out=simp('i32.'+op.split('.')[1],a,b)
            if op=='i32x4.mul':
                vals={}
                for i,vi in va.items():
                    for j,vj in vb.items():
                        convolutions+=1;vals[i+j]=min(vals.get(i+j,32),vi+vj)
            else: vals={i:min(va.get(i,32),vb.get(i,32)) for i in va.keys()|vb.keys()}
        elif op=='i32x4.shl' and e[2][0]=='i32.const':
            a,va=vector(e[1]);s=int(e[2][1],0)&31;out=simp('i32.mul',a,p.const(1<<s));vals={i:v+s for i,v in va.items()}
        else:raise ValueError('Unsupported vector operation '+op)
        vals={i:v for i,v in vals.items() if v<32}
        if vals and max(vals)>256:raise ValueError('Polynomial degree resource limit')
        max_degree=max(max_degree,max(vals,default=0));vector_memo[key]=(out,vals);return out,vals
    # Collect a linear combination of lane observations of one actual vector.
    terms={};nodes={};constant=0
    def output(e,scale=1):
        nonlocal constant
        op=e[0]
        if op=='i32.const':constant=(constant+scale*int(e[1],0))&p.MASK
        elif op=='i32x4.extract_lane':
            key=id(e[2]);nodes[key]=e[2];entry=(key,int(e[1]));terms[entry]=(terms.get(entry,0)+scale)&p.MASK
        elif op in ('i32.add','i32.sub'):
            output(e[1],scale);output(e[2],scale if op=='i32.add' else -scale)
        elif op=='i32.mul' and e[1][0]=='i32.const':output(e[2],scale*int(e[1][1],0))
        elif op=='i32.mul' and e[2][0]=='i32.const':output(e[1],scale*int(e[2][1],0))
        elif op=='i32.shl' and e[2][0]=='i32.const':output(e[1],scale*(1<<(int(e[2][1],0)&31)))
        else:raise ValueError('Nonlinear scalar observation '+op)
    output(root)
    result=p.const(constant);certificates=[]
    for key,node in nodes.items():
        c,vals=vector(node);weights=[terms.get((key,i),0) for i in range(4)]
        for degree,valuation in vals.items():
            if not degree:continue
            moment=sum(coef*pow(i+1,degree,1<<32) for i,coef in enumerate(weights))&p.MASK
            if v2(moment)+valuation<32:raise ValueError('Uncancelled degree '+str(degree))
        factor=sum(weights)&p.MASK
        result=simp('i32.add',result,simp('i32.mul',p.const(factor),c))
        certificates.append(dict(weights=weights,coefficient_valuation=vals))
    return result,dict(vector_visits=visits,vector_memo=len(vector_memo),scalar_memo=len(scalar_memo),max_degree=max_degree,valuation_products=convolutions,certificates=certificates)


def recover(src,dst):
    start=time.perf_counter();root=p.expanded(src,allow_vector=True);loaded=time.perf_counter();expr,stats=project(root);solved=time.perf_counter();p.compile_wat(p.scalar_dag(expr),dst)
    return dict(stats,read_ms=(loaded-start)*1000,project_ms=(solved-loaded)*1000,total_ms=(time.perf_counter()-start)*1000)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();print(json.dumps(recover(a.source,a.output)))
