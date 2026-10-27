"""Experimental error-bounded region lowering; known numerical principle.

Single pure exported i32 add/mul expression. No imports, side effects or loops.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

# Load the earlier syntax/tool utility under an unambiguous module name.
import importlib.util
_spec = importlib.util.spec_from_file_location('switching_util', Path(__file__).resolve().parents[1] / 'connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(w)
MASK = 2**32-1


def source(path):
    w.tool('wasm-validate', [path])
    mod = w.parse(w.tool('wasm2wat', [path, '--fold-exprs']))
    if any(x[0] not in ('type', 'func', 'export') for x in mod[1:]):
        raise ValueError('Only a pure function and export are supported')
    funcs = [x for x in mod[1:] if x[0] == 'func']
    exports = [x for x in mod[1:] if x[0] == 'export']
    if len(funcs) != 1 or len(exports) != 1 or exports[0][2] != ['func','0']:
        raise ValueError('Expected one function and one export')
    f = funcs[0]
    params = [p for x in f[1:] if isinstance(x,list) and x[0] == 'param' for p in x[1:]]
    if not 1 <= len(params) <= 128 or set(params) != {'i32'}:
        raise ValueError('Expected 1..128 i32 parameters')
    if [x for x in f[1:] if isinstance(x,list) and x[0] == 'result'] != [['result','i32']]:
        raise ValueError('Expected i32 result')
    body = [x for x in f[1:] if isinstance(x,list) and x[0] not in ('param','result','type')]
    if len(body) != 1:
        raise ValueError('Expected one expression with no locals')
    def walk(x):
        if x[0] == 'local.get' and len(x)==2 and 0 <= int(x[1]) < len(params):
            return ('v',int(x[1]))
        if x[0] == 'i32.const' and len(x)==2:
            return ('c',int(x[1]) & MASK)
        if x[0] in ('i32.add','i32.mul') and len(x)==3:
            return (x[0][4:],walk(x[1]),walk(x[2]))
        raise ValueError('Unsupported expression: '+w.emit(x))
    return len(params),exports[0][1],walk(body[0])


def bound(t):
    if t[0] == 'c': return t[1],0
    if t[0] in ('v','r'): return MASK,0
    ma,ba = bound(t[1]); mb,bb = bound(t[2])
    if t[0] == 'add': m,b = ma+mb,ba+bb
    elif t[0] == 'mul': m,b = ma*mb,ma*bb+mb*ba+ba*bb
    else: raise ValueError(t[0])
    # All intermediates are integer-valued. Below 2**53 they are exact;
    # otherwise a full ulp at a conservative magnitude is safe, including bins.
    extent = m+b
    extra = 0 if extent <= 2**53 else 2**max(0,extent.bit_length()-53)
    return m,b+extra


def width(t):
    m,b = bound(t)
    return max(1,(2*b).bit_length()),m,b


def partition(t, mode):
    regions=[]
    def seal(node):
        k,m,b = width(node)
        if k>30 or m+b >= 2**80: raise ValueError('Region outside numeric bounds')
        idx=len(regions)
        regions.append({'tree':node,'k':k,'maximum':m,'error_bound':b})
        return ('r',idx)
    def walk(node):
        if node[0] in ('v','c'): return node
        children=[walk(node[1]),walk(node[2])]
        if mode=='per_op':
            return seal((node[0],*children))
        while True:
            candidate=(node[0],*children)
            k,m,b=width(candidate)
            if k<=30 and m+b < 2**80: return candidate
            choices=[i for i,c in enumerate(children) if c[0] in ('add','mul')]
            if not choices: raise ValueError('Atomic operation does not fit')
            i=max(choices,key=lambda j:bound(children[j])[0])
            children[i]=seal(children[i])
    result=walk(t)
    if result[0] in ('add','mul'): result=seal(result)
    return regions,result


def polynomial(t, mask):
    if t[0] in ('v','r'): return {(t,):1}
    if t[0]=='c': return {():t[1]&mask} if t[1]&mask else {}
    a,b=polynomial(t[1],mask),polynomial(t[2],mask)
    out=dict(a) if t[0]=='add' else {}
    terms=b.items() if t[0]=='add' else ((tuple(sorted(x+y)),v*z) for x,v in a.items() for y,z in b.items())
    for monomial,c in terms:
        v=(out.get(monomial,0)+c)&mask
        if v: out[monomial]=v
        else: out.pop(monomial,None)
        if len(out)>4096: raise ValueError('Polynomial expansion budget')
    return out


def iref(t):
    if t[0]=='v': return f'(local.get {t[1]})'
    if t[0]=='r': return f'(local.get $o{t[1]})'
    if t[0]=='c': return f'(i32.const {t[1] if t[1]<2**31 else t[1]-2**32})'
    return f'(i32.{t[0]} {iref(t[1])} {iref(t[2])})'


def high(t):
    if t[0] in ('v','r'): return f'(f64.convert_i32_u {iref(t)})'
    if t[0]=='c': return f'(f64.const {t[1]})'
    return f'(f64.{t[0]} {high(t[1])} {high(t[2])})'


def low(t,k):
    poly=polynomial(t,2**k-1)
    terms=[]
    for monomial,c in sorted(poly.items()):
        factors=[iref(v) for v in monomial]
        if c != 1 or not factors: factors.append(f'(i32.const {c})')
        value=factors[0]
        for factor in factors[1:]: value=f'(i32.mul {value} {factor})'
        terms.append(value)
    value=terms[0] if terms else '(i32.const 0)'
    for term in terms[1:]: value=f'(i32.add {value} {term})'
    return f'(i32.and {value} (i32.const {2**k-1}))'


def plain(n,name,t):
    return f'(module (func (export {name}) (param {" ".join(["i32"]*n)}) (result i32) {iref(t)}))'


def emit(n,name,regions,result,bad_width=False):
    declarations=[];lines=[]
    for i,region in enumerate(regions):
        k=1 if bad_width else region['k']
        declarations += [f'(local $h{i} f64)',f'(local $r{i} i32)',f'(local $o{i} i32)']
        h=f'(local.get $h{i})';r=f'(local.get $r{i})'
        lines += [f'(local.set $h{i} {high(region["tree"])})',
                  f'(local.set $r{i} (i32.wrap_i64 (i64.trunc_f64_s (f64.sub {h} (f64.mul (f64.nearest (f64.mul {h} (f64.const 0x1p-32))) (f64.const 0x1p32))))))',
                  f'(local.set $o{i} (i32.add {r} (i32.shr_s (i32.shl (i32.sub {low(region["tree"],k)} {r}) (i32.const {32-k})) (i32.const {32-k})))))']
    return f'(module (func (export {name}) (param {" ".join(["i32"]*n)}) (result i32) {" ".join(declarations)} {" ".join(lines)} {iref(result)}))'


def transform(src,out,mode='fused',bad_width=False):
    if out.exists(): raise ValueError('Refuse overwrite')
    started=time.perf_counter()
    n,name,t=source(src)
    regions,result=partition(t,mode)
    text=emit(n,name,regions,result,bad_width)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[out.with_suffix('.wat'),'-o',out])
    w.tool('wasm-validate',[out])
    report={'mode':mode,'regions':len(regions),'widths':[x['k'] for x in regions],
            'bounds':[{'maximum':x['maximum'],'error_bound':x['error_bound']} for x in regions],
            'seconds':time.perf_counter()-started,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
            'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bad_width_control':bad_width,'linear_memory_bytes':0}
    Path(str(out)+'.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=['fused','per_op'],default='fused')
    a=ap.parse_args();print(json.dumps(transform(a.input,a.output,a.mode)))
