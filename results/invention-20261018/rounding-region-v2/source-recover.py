"""Known-family attack: validate residue correction, lift floating arithmetic.

Input is only the distributed binary. No original tree or transformation report.
"""
import argparse
import json
from pathlib import Path
import time
import prototype as p


def number(x):
    text=x.lower()
    return float.fromhex(text) if '0x' in text else float(text)


def lift(x):
    if x[0]=='f64.const' and x[1].is_integer() and 0<=x[1]<=p.MASK: return ('c',int(x[1]))
    if x[0]=='f64.convert_i32_u': return int_tree(x[1])
    if x[0] in ('f64.add','f64.mul'): return (x[0][4:],lift(x[1]),lift(x[2]))
    raise ValueError('Not a supported integer-valued high path')


def int_tree(x):
    if x[0]=='arg': return ('v',x[1])
    if x[0]=='i32.const': return ('c',x[1]&p.MASK)
    if x[0] in ('i32.add','i32.mul'): return (x[0][4:],int_tree(x[1]),int_tree(x[2]))
    if x[0]=='i32.shl' and x[2][0]=='i32.const':
        return ('mul',int_tree(x[1]),('c',1<<(x[2][1]&31)))
    raise ValueError('Not a pure recovered integer path: '+x[0])


def scale(x,value):
    return x[0]=='f64.const' and x[1]==value


def split_scale(x,value):
    if x[0]!='f64.mul': return None
    if scale(x[1],value): return x[2]
    if scale(x[2],value): return x[1]
    return None


def remainder(x):
    if x[0]!='i32.wrap_i64' or x[1][0]!='i64.trunc_f64_s' or x[1][1][0]!='f64.sub': return None
    _,h,q=x[1][1]
    near=split_scale(q,2.0**32)
    if near is None or near[0]!='f64.nearest': return None
    h2=split_scale(near[1],2.0**-32)
    return h if h2==h else None


def residue_poly(x,k):
    if x[0]=='i32.and':
        for a,b in ((x[1],x[2]),(x[2],x[1])):
            if b[0]=='i32.const' and (b[1] & (2**k-1))==2**k-1:
                return residue_poly(a,k)
    return p.polynomial(int_tree(x),2**k-1)


def tree_expr(t):
    if t[0]=='v': return ('arg',t[1])
    if t[0]=='c': return ('i32.const',t[1])
    return ('i32.'+t[0],tree_expr(t[1]),tree_expr(t[2]))


def recover_model(mod):
    funcs=[x for x in mod[1:] if x[0]=='func']
    if len(funcs)!=1 or any(x[0] not in ('type','func','export') for x in mod[1:]): raise ValueError('Unsupported module')
    f=funcs[0]
    params=[t for x in f[1:] if isinstance(x,list) and x[0]=='param' for t in x[1:]]
    if set(params)!={'i32'}: raise ValueError('Wrong parameters')
    locals_=[t for x in f[1:] if isinstance(x,list) and x[0]=='local' for t in x[1:]]
    env=[('arg',i) for i in range(len(params))]+[('f64.const',0.0) if t=='f64' else ('i32.const',0) for t in locals_]
    converted=0
    def simplify(x):
        nonlocal converted
        if x[0]!='i32.add': return x
        for rv,d in ((x[1],x[2]),(x[2],x[1])):
            h=remainder(rv)
            if h is None or d[0]!='i32.shr_s' or d[2][0]!='i32.const': continue
            shift=d[2][1]&31
            if not 2<=shift<=31 or d[1][0]!='i32.shl' or d[1][2]!=d[2]: continue
            delta=d[1][1]
            if delta[0]!='i32.sub' or delta[2]!=rv: continue
            k=32-shift
            t=lift(h)
            required,m,b=p.width(t)
            # The recovered tree may have expanded earlier cut regions. Bounds
            # must instead regard a converted i32 operand as an arbitrary word.
            def local_lift(z):
                if z[0]=='f64.convert_i32_u': return ('v',0)
                if z[0]=='f64.const': return ('c',int(z[1]))
                return (z[0][4:],local_lift(z[1]),local_lift(z[2]))
            required,m,b=p.width(local_lift(h))
            if required>k or m+b>=2**80: raise ValueError('Correction width not justified')
            if residue_poly(delta[1],k)!=p.polynomial(t,2**k-1): raise ValueError('Wrong exact residue')
            converted+=1
            return tree_expr(t)
        return x
    supported={'i32.add','i32.mul','i32.sub','i32.and','i32.shl','i32.shr_s','i32.wrap_i64',
               'i64.trunc_f64_s','f64.add','f64.sub','f64.mul','f64.nearest','f64.convert_i32_u'}
    def expr(x):
        op=x[0]
        if op=='local.get': return env[int(x[1])]
        if op in ('local.set','local.tee'):
            value=expr(x[2]);env[int(x[1])]=value
            return value if op=='local.tee' else None
        if op=='i32.const': return (op,int(x[1])&p.MASK)
        if op=='f64.const': return (op,number(x[1]))
        if op=='return': return expr(x[1])
        if op not in supported: raise ValueError('Unsupported instruction: '+op)
        return simplify((op,*[expr(v) for v in x[1:]]))
    value=None
    for x in f[1:]:
        if isinstance(x,list) and x[0] not in ('type','param','result','local'): value=expr(x)
    result=int_tree(value)
    name=[x for x in mod[1:] if x[0]=='export'][0][1]
    return len(params),name,result,converted


def recover(src,out):
    if out.exists(): raise ValueError('Refuse overwrite')
    started=time.perf_counter()
    mod=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs']))
    a=time.perf_counter()
    n,name,t,count=recover_model(mod)
    analysis=time.perf_counter()-a
    out.parent.mkdir(parents=True,exist_ok=True)
    wp=out.with_suffix('.wat');wp.write_text(p.plain(n,name,t),encoding='utf-8')
    p.w.tool('wat2wasm',[wp,'-o',out]);p.w.tool('wasm-validate',[out])
    return {'status':'recovered','regions_recognized':count,'analysis_seconds':analysis,
            'total_seconds':time.perf_counter()-started}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();print(json.dumps(recover(a.input,a.output)))
