"""Restricted actual-Wasm SIMD cone transformation and quotient recovery."""
import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import time

spec=importlib.util.spec_from_file_location('wasm_common',Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)


def vec(k):return ('v128.const','i8x16',*([str(k)]*16))
def node(op,*args):return (op,*args)
def text(x):return '('+' '.join(text(y) if isinstance(y,tuple) else str(y) for y in x)+')'
def frozen(x):return tuple(frozen(y) if isinstance(y,list) else y for y in x)
ZERO=vec(0);ONE=vec(1)


def program(path):
    w.tool('wasm-validate',[path]);mod=w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))
    if any(x[0] not in ('type','func','export') for x in mod[1:]):raise ValueError('Pure module required')
    funcs=[x for x in mod[1:] if x[0]=='func']
    if len(funcs)!=1:raise ValueError('One function required')
    f=funcs[0];decl=[x for x in f[1:] if isinstance(x,list) and x[0] in ('type','param','result','local')]
    params=[v for x in decl if x[0]=='param' for v in x[1:]]
    if not params or any(p!='i32' for p in params):raise ValueError('i32 parameters required')
    if [x for x in decl if x[0]=='result']!=[['result','i32']]:raise ValueError('One i32 result')
    localtypes=params+[v for x in decl if x[0]=='local' for v in x[1:]]
    env=[('local.get',str(i)) for i in range(len(params))]+[ZERO if ty=='v128' else ('i32.const','0') for ty in localtypes[len(params):]]
    stack=[]
    def execute(x):
        if not isinstance(x,list):raise ValueError('Unsupported statement '+str(x))
        op=x[0];imm=[]
        if op=='v128.const':stack.append(frozen(x));return
        for y in x[1:]:
            if isinstance(y,list):execute(y)
            else:imm.append(y)
        if op=='local.get':stack.append(env[int(imm[0])]);return
        if op in ('local.set','local.tee'):
            env[int(imm[0])]=stack[-1]
            if op=='local.set':stack.pop()
            return
        if op=='i32.const':stack.append((op,*imm));return
        if op=='i32x4.replace_lane':
            b,a=stack.pop(),stack.pop();stack.append((op,*imm,a,b));return
        if op in ('i32x4.splat','i8x16.splat','v128.not','i8x16.bitmask'):
            stack.append((op,*imm,stack.pop()));return
        if op in ('v128.and','v128.or','v128.xor','i8x16.gt_u','i8x16.lt_u','i8x16.ge_u','i8x16.le_u','i8x16.eq','i8x16.ne','i8x16.sub_sat_u','i8x16.min_u','i8x16.max_u'):
            b,a=stack.pop(),stack.pop();stack.append((op,*imm,a,b));return
        raise ValueError('Unsupported instruction '+op)
    for x in f[1:]:
        if x not in decl:execute(x)
    if len(stack)!=1 or stack[0][0]!='i8x16.bitmask':raise ValueError('Require one bitmask result')
    if not mask(stack[0][1]):raise ValueError('bitmask input must be proven canonical 0/255 masks')
    exports=[x for x in mod[1:] if x[0]=='export']
    if len(exports)!=1 or exports[0][2]!=['func','0']:raise ValueError('One function export required')
    return len(params),exports[0][1],stack[0][1]


def const_bytes(x):
    if x[0]=='v128.const':
        kind=x[1];width={'i8x16':1,'i16x8':2,'i32x4':4,'i64x2':8}.get(kind)
        if not width:raise ValueError('Unsupported vector constant format')
        out=[]
        for s in x[2:]:
            v=int(s,0) if s.startswith(('0x','-0x')) else int(s)
            out.extend((v>>(8*i))&255 for i in range(width))
        if len(out)!=16:raise ValueError('Vector constant length')
        return out
    if x[0]=='i8x16.splat' and x[1][0]=='i32.const':return [int(x[1][1])&255]*16
    return None


def canonical_data(x):
    c=const_bytes(x)
    if c is not None:return ('v128.const','i8x16',*map(str,c))
    return tuple(canonical_data(y) if isinstance(y,tuple) else y for y in x)


def encode(e,mode):
    op=e[0]
    if op.startswith('i8x16.') and op[6:] in ('gt_u','lt_u','ge_u','le_u','eq','ne'):
        a,b=e[1:];kind=op[6:]
        if kind=='gt_u':z=node('i8x16.sub_sat_u',a,b)
        elif kind=='lt_u':z=node('i8x16.sub_sat_u',b,a)
        elif kind=='ge_u':z=node('i8x16.sub_sat_u',ONE,node('i8x16.sub_sat_u',b,a))
        elif kind=='le_u':z=node('i8x16.sub_sat_u',ONE,node('i8x16.sub_sat_u',a,b))
        else:
            ne=node('i8x16.max_u',node('i8x16.sub_sat_u',a,b),node('i8x16.sub_sat_u',b,a))
            z=ne if kind=='ne' else node('i8x16.sub_sat_u',ONE,ne)
    elif op=='v128.not':z=node('i8x16.sub_sat_u',ONE,encode(e[1],mode))
    elif op in ('v128.and','v128.or','v128.xor'):
        a,b=(encode(x,mode) for x in e[1:])
        if op=='v128.and':z=node('i8x16.min_u',a,b)
        elif op=='v128.or':z=node('i8x16.max_u',a,b)
        else:z=node('i8x16.min_u',node('i8x16.max_u',a,b),node('i8x16.sub_sat_u',ONE,node('i8x16.min_u',a,b)))
    else:raise ValueError('Not a comparison/Boolean cone: '+op)
    if mode=='normalized':z=node('v128.and',node('i8x16.gt_u',z,ZERO),ONE)
    return z


def module(np,name,expr):
    # DAG sharing prevents artificial expression duplication in the emitter.
    order=[];seen=set()
    def visit(e):
        if e in seen:return
        for x in e[1:]:
            if isinstance(x,tuple):visit(x)
        seen.add(e)
        if e[0] not in ('local.get','i32.const','v128.const'):order.append(e)
    visit(expr);slot={e:np+i for i,e in enumerate(order)}
    ty=lambda e:'i32' if e[0]=='i8x16.bitmask' else 'v128'
    ref=lambda e:node('local.get',str(slot[e])) if e in slot else e
    parts=['(module (func '+ ' '.join('(param i32)' for _ in range(np))+' (result i32)',
           '(local '+' '.join(ty(e) for e in order)+')']
    for e in order:
        z=tuple(ref(x) if isinstance(x,tuple) else x for x in e)
        parts.append('(local.set '+str(slot[e])+' '+text(z)+')')
    parts += [text(ref(expr)),') (export '+name+' (func 0)))']
    return '\n'.join(parts)


def emit(path,wat):
    if path.exists():raise ValueError('Refuse overwrite')
    path.parent.mkdir(parents=True,exist_ok=True);wp=path.with_suffix('.wat');wp.write_text(wat,encoding='utf-8')
    w.tool('wat2wasm',[wp,'-o',path]);w.tool('wasm-validate',[path])


def transform(src,out,mode):
    start=time.perf_counter();np,name,e=program(src)
    z=node('i8x16.bitmask',node('i8x16.gt_u',encode(e,mode),ZERO))
    emit(out,module(np,name,z))
    return {'seconds':time.perf_counter()-start,'mode':mode,'bytes':out.stat().st_size}


def bn(op,*args):
    if op=='not':
        a=args[0];return a[1] if a[0]=='not' else ('not',a)
    if op=='xor':return bn('and',bn('or',*args),bn('not',bn('and',*args)))
    xs=[]
    for a in args:xs.extend(a[1:] if a[0]==op and op in ('and','or') else (a,))
    xs=sorted(set(xs),key=repr)
    if len(xs)==1:return xs[0]
    return (op,*xs)


def cmp(kind,a,b):
    a,b=canonical_data(a),canonical_data(b)
    if kind=='gt_u':return ('gt',a,b)
    if kind=='lt_u':return ('gt',b,a)
    if kind=='ge_u':return bn('not',('gt',b,a))
    if kind=='le_u':return bn('not',('gt',a,b))
    ne=bn('or',('gt',a,b),('gt',b,a))
    return ne if kind=='ne' else bn('not',ne)


def quotient(e):
    # Cache only within this analysis; timing repetitions do not share results.
    @lru_cache(None)
    def q(e):
        op=e[0]
        if op in ('i8x16.min_u','i8x16.max_u'):
            return bn('and' if op=='i8x16.min_u' else 'or',*(q(x) for x in e[1:]))
        if op=='i8x16.sub_sat_u':
            if const_bytes(e[1])==[1]*16:return bn('not',q(e[2]))
            return cmp('gt_u',e[1],e[2])
        if op=='i8x16.gt_u' and const_bytes(e[2])==[0]*16:return q(e[1])
        if op=='v128.and':
            for i in (1,2):
                if const_bytes(e[i])==[1]*16 and mask(e[3-i]):return q(e[3-i])
        if op.startswith('i8x16.') and op[6:] in ('gt_u','lt_u','ge_u','le_u','eq','ne'):return cmp(op[6:],e[1],e[2])
        if op=='v128.not' and mask(e[1]):return bn('not',q(e[1]))
        if op in ('v128.and','v128.or','v128.xor') and all(mask(x) for x in e[1:]):return bn(op[5:],*(q(x) for x in e[1:]))
        return cmp('gt_u',e,ZERO)
    return q(e)


def mask(e):
    c=const_bytes(e)
    if c is not None:return all(v in (0,255) for v in c)
    if e[0].startswith('i8x16.') and e[0][6:] in ('gt_u','lt_u','ge_u','le_u','eq','ne'):return True
    if e[0] in ('v128.not','v128.and','v128.or','v128.xor'):return all(mask(x) for x in e[1:])
    return False


def boolean_expr(e):
    if e[0]=='gt':return node('i8x16.gt_u',e[1],e[2])
    if e[0]=='not':return node('v128.not',boolean_expr(e[1]))
    z=boolean_expr(e[1])
    for x in e[2:]:z=node('v128.'+e[0],z,boolean_expr(x))
    return z


def recover(src,out=None):
    start=time.perf_counter();np,name,e=program(src);parsed=time.perf_counter()
    q=quotient(e);end=time.perf_counter()
    if out:emit(out,module(np,name,node('i8x16.bitmask',boolean_expr(q))))
    return {'status':'ok','formula':q,'parse_seconds':parsed-start,'solve_seconds':end-parsed}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=('fused','normalized','recover'));ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();r=recover(a.input,a.output) if a.action=='recover' else transform(a.input,a.output,a.action);print(json.dumps(r))
