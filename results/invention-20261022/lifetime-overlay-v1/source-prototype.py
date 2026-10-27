"""Liveness-based private-memory packing and binary-only reaching-definition attack.

This probes a hypothesis close to stack coloring, not an established new obfuscator.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('overlay_wat', HERE.parent/'connectivity-elimination/prototype.py')
wat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wat)
PURE = {f'{t}.{op}' for t in ('i32', 'i64') for op in
        ('add', 'sub', 'mul', 'and', 'or', 'xor', 'shl', 'shr_u', 'shr_s', 'rotl', 'rotr',
         'eq', 'ne', 'lt_u', 'lt_s', 'gt_u', 'gt_s', 'le_u', 'le_s', 'ge_u', 'ge_s')}
UNARY = {'i32.wrap_i64', 'i64.extend_i32_u', 'i64.extend_i32_s', 'i32.eqz', 'i64.eqz'}
HEAD = {'type', 'param', 'result', 'local'}


def access(x):
    """(effective address,width,type,address-child-index), only static memory0."""
    if x[0] not in ('i32.load', 'i64.load', 'i32.store', 'i64.store'):
        raise ValueError('Not a full-width scalar access')
    j = next((i for i in range(1, len(x)) if isinstance(x[i], list)), None)
    if j is None or x[j][0] != 'i32.const' or len(x[j]) != 2:
        raise ValueError('Dynamic address')
    opts = x[1:j]
    if any(not s.startswith(('align=', 'offset=')) for s in opts):
        raise ValueError('Memory index or unknown access option')
    off = next((int(s[7:]) for s in opts if s.startswith('offset=')), 0)
    a = (int(x[j][1]) & 0xffffffff) + off  # effective address does not wrap
    w = 4 if x[0].startswith('i32') else 8
    if a < 0 or a+w > 65536:
        raise ValueError('Potential bounds trap')
    return a, w, x[0][:3], j


def read(src):
    wat.tool('wasm-validate', [src])
    m = wat.parse(wat.tool('wasm2wat', [src, '--fold-exprs']))
    if any(x[0] not in ('type', 'func', 'memory', 'export') for x in m[1:]):
        raise ValueError('Module contains unsupported section')
    fs = [x for x in m[1:] if x[0] == 'func']
    ms = [x for x in m[1:] if x[0] == 'memory']
    ex = [x for x in m[1:] if x[0] == 'export']
    if len(fs) != 1 or ms != [['memory', '1', '1']] or len(ex) != 1 or ex[0][2] != ['func', '0']:
        raise ValueError('Need one function, private fixed memory1, one function export')
    f = fs[0]
    params = [v for x in f[1:] if isinstance(x, list) and x[0] == 'param' for v in x[1:]]
    results = [x for x in f[1:] if isinstance(x, list) and x[0] == 'result']
    if params != ['i32', 'i32'] or results != [['result', 'i32']]:
        raise ValueError('Expected (i32,i32)->i32')
    locals_ = [v for x in f[1:] if isinstance(x, list) and x[0] == 'local' for v in x[1:]]
    if any(v not in ('i32', 'i64') for v in locals_):
        raise ValueError('Only integer locals')
    body = [x for x in f[1:] if isinstance(x, list) and x[0] not in HEAD]
    if not body:
        raise ValueError('Empty body')
    def expr(x):
        op = x[0]
        if op in ('i32.const', 'i64.const', 'local.get') and len(x) == 2:
            return
        if op in PURE and len(x) == 3:
            expr(x[1]); expr(x[2]); return
        if op in UNARY and len(x) == 2:
            expr(x[1]); return
        if op in ('i32.load', 'i64.load'):
            a,w,t,j = access(x)
            if len(x) != j+1:
                raise ValueError('Load operands')
            return
        raise ValueError('Unsupported expression: '+wat.emit(x))
    def seq(xs, final=False):
        for i,x in enumerate(xs):
            op = x[0]
            if op in ('i32.store', 'i64.store'):
                a,w,t,j = access(x)
                if len(x) != j+2:
                    raise ValueError('Store operands')
                expr(x[j+1])
            elif op == 'local.set' and len(x) == 3:
                expr(x[2])
            elif op == 'if' and len(x) in (3,4) and x[2][0] == 'then' and (len(x)==3 or x[3][0]=='else'):
                expr(x[1]); seq(x[2][1:]); seq(x[3][1:] if len(x)==4 else [])
            elif final and i == len(xs)-1:
                expr(x)
            else:
                raise ValueError('Unsupported statement: '+wat.emit(x))
    seq(body, True)
    return m, f, body, params+locals_


def expr_cells(x):
    if x[0] in ('i32.load', 'i64.load'):
        a,w,t,j = access(x)
        return {(a,w)}
    s = set()
    for c in x[1:]:
        if isinstance(c, list):
            s |= expr_cells(c)
    return s


def graph(body):
    cells, adj, sites = set(), {}, []
    def interfere(live):
        for c in live:
            cells.add(c); adj.setdefault(c,set()).update(live-{c})
    def backwards(xs, live):
        live = set(live)
        for x in reversed(xs):
            op = x[0]
            if op == 'if':
                a = backwards(x[2][1:], live)
                b = backwards(x[3][1:] if len(x)==4 else [], live)
                live = a|b|expr_cells(x[1])
            elif op in ('i32.store', 'i64.store'):
                a,w,t,j = access(x); d=(a,w)
                cells.add(d)
                interfere(live|{d})  # a dead store must not clobber another live cell
                live = (live-{d})|expr_cells(x[j+1])
            else:
                live |= expr_cells(x)
            interfere(live)
            sites.append(sorted(live))
        return live
    entry=backwards(body,set())
    if entry:
        raise ValueError('Read before definite store: '+str(sorted(entry)))
    ordered=sorted(cells)
    for i,(a,w) in enumerate(ordered):
        for b,v in ordered[i+1:]:
            if max(a,b)<min(a+w,b+v):
                raise ValueError('Input cells overlap or have inconsistent access widths')
    return ordered,adj,sites


def allocate(cells,adj,mode):
    assigned={}
    # Identical order across controls; only position objective differs.
    order=sorted(cells,key=lambda c:(-len(adj.get(c,set())),-c[1],c[0]))
    for c in order:
        w=c[1]; end=max((a+k[1] for k,a in assigned.items()),default=0)
        choices=[]
        for a in range(0,end+w):
            if mode=='first' and a%w:
                continue
            if any(k in adj.get(c,set()) and max(a,b)<min(a+w,b+k[1]) for k,b in assigned.items()):
                continue
            overlap=sum(max(0,min(a+w,b+k[1])-max(a,b)) for k,b in assigned.items() if k[1]!=w)
            footprint=max(end,a+w)
            # Never increase footprint just to inflate a conflict score.
            key=(footprint,-overlap,a) if mode=='conflict' else (a,)
            choices.append((key,a))
        if not choices:
            raise AssertionError('No allocation')
        assigned[c]=min(choices)[1]
    # Check pairwise live interference independently of candidate enumeration.
    for c,a in assigned.items():
        for d in adj.get(c,set()):
            b=assigned[d]
            if max(a,b)<min(a+c[1],b+d[1]):
                raise AssertionError('Interfering placement')
    return assigned


def conflict_metric(m):
    views={}
    def walk(x):
        if x[0] in ('i32.load','i64.load','i32.store','i64.store'):
            a,w,t,j=access(x)
            for b in range(a,a+w):
                views.setdefault(b,set()).add((a,w))
        for y in x[1:]:
            if isinstance(y,list): walk(y)
    walk(m)
    return {'touched_bytes':len(views), 'cross_width_bytes':sum(len({w for a,w in s})>1 for s in views.values()),
            'multi_view_bytes':sum(len(s)>1 for s in views.values())}


def save(m,out):
    out=Path(out)
    if out.exists() or out.with_suffix('.wat').exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.with_suffix('.wat').write_text(wat.emit(m),encoding='utf8')
    wat.tool('wat2wasm',[out.with_suffix('.wat'),'-o',out])
    wat.tool('wasm-validate',[out])


def transform(src,out,mode):
    start=time.perf_counter()
    m,f,body,types=read(src)
    cells,adj,sites=graph(body)
    placement=allocate(cells,adj,mode)
    def rewrite(x):
        if x[0] in ('i32.load','i64.load','i32.store','i64.store'):
            a,w,t,j=access(x)
            x[:]=[x[0],'align=1',['i32.const',str(placement[(a,w)])],*x[j+1:]]
        for y in x[1:]:
            if isinstance(y,list): rewrite(y)
    rewrite(m)
    save(m,out)
    return {'mode':mode,'cells':len(cells),'interference_edges':sum(map(len,adj.values()))//2,
            'placement':[{'source':a,'width':w,'target':b} for (a,w),b in sorted(placement.items())],
            'footprint':max((b+c[1] for c,b in placement.items()),default=0),
            'metric':conflict_metric(m),'elapsed_ms':(time.perf_counter()-start)*1000}


def recover(src,out):
    """Constant-address byte reaching definitions, branch joins in typed locals.

    No source layout, seed, manifest or source body is read. A load is replaced only
    when its bytes all refer to the matching full-width store value or merged phi.
    """
    start=time.perf_counter()
    m,f,body,types=read(src)
    parse_ms=(time.perf_counter()-start)*1000
    newlocals=[]; loads=0; stores=0; phis=0
    def local(t):
        n=len(types)+len(newlocals);newlocals.append(t);return str(n)
    def load_expr(x,env):
        nonlocal loads
        if x[0] in ('i32.load','i64.load'):
            a,w,t,j=access(x); row=[env.get(a+b) for b in range(w)]
            if any(v is None for v in row): raise ValueError('Uninitialized byte in recovery')
            n=row[0][0]
            if row!=[(n,b,w,t) for b in range(w)]:
                raise ValueError('Mixed byte provenance: need extraction/reassembly')
            loads+=1;return ['local.get',n]
        return [x[0],*[load_expr(y,env) if isinstance(y,list) else y for y in x[1:]]]
    def sequence(xs,env):
        nonlocal stores,phis
        out=[];env=dict(env)
        for x in xs:
            op=x[0]
            if op in ('i32.store','i64.store'):
                a,w,t,j=access(x);v=load_expr(x[j+1],env);n=local(t)
                out.append(['local.set',n,v]);stores+=1
                for b in range(w):env[a+b]=(n,b,w,t)
            elif op=='if':
                cond=load_expr(x[1],env)
                left,le=sequence(x[2][1:],env)
                right,re=sequence(x[3][1:] if len(x)==4 else [],env)
                merged={k:v for k,v in le.items() if re.get(k)==v}
                # A full-width loadable value survives only with congruent lane
                # origins on both paths. Make the correlation explicit with a phi.
                for a,lv in sorted(le.items()):
                    ln,offset,w,t=lv
                    if offset or a in merged:continue
                    rv=re.get(a)
                    if rv is None or rv[1:]!=(0,w,t):continue
                    rn=rv[0]
                    if all(le.get(a+b)==(ln,b,w,t) and re.get(a+b)==(rn,b,w,t) for b in range(w)):
                        n=local(t);phis+=1
                        left.append(['local.set',n,['local.get',ln]])
                        right.append(['local.set',n,['local.get',rn]])
                        for b in range(w):merged[a+b]=(n,b,w,t)
                out.append(['if',cond,['then',*left],['else',*right]])
                env=merged
            else:
                out.append(load_expr(x,env))
        return out,env
    normalized,_=sequence(body,{})
    head=[x for x in f[1:] if isinstance(x,list) and x[0] in HEAD]
    f[:]=['func',*head,*([['local',*newlocals]] if newlocals else []),*normalized]
    save(m,out)
    return {'loads':loads,'stores':stores,'phis':phis,'new_locals':len(newlocals),
            'reader_ms':parse_ms,'normalization_and_compile_ms':(time.perf_counter()-start)*1000-parse_ms,
            'elapsed_ms':(time.perf_counter()-start)*1000,'remaining_memory_ops':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['first','conflict','recover'])
    p.add_argument('source');p.add_argument('output');a=p.parse_args()
    result=recover(a.source,a.output) if a.action=='recover' else transform(a.source,a.output,a.action)
    print(json.dumps(result,indent=2))
