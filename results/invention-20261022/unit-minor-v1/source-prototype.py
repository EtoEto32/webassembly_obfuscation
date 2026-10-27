"""Whole arithmetic formula -> polynomial matrix -> i32 determinant.

Research hypothesis, not a new determinant primitive or a security claim.
Only one pure exported 3-i32 -> i32 expression with add/sub/mul is supported.
"""
import argparse
import hashlib
import importlib.util
import json
import random
import struct
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('unit_minor_sx', ROOT / 'research/connectivity-elimination/prototype.py')
sx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sx)
MASK = (1 << 32) - 1
MAGIC = 0x31444D55
LOG = []


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tool(name, args):
    folder = sx.BINARYEN if name == 'wasm-opt' else sx.WABT
    cmd = [str(folder / (name + '.exe')), *map(str, args)]
    start = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    LOG.append(dict(command=cmd, exit=r.returncode, stdout=r.stdout, stderr=r.stderr,
                    seconds=time.perf_counter()-start))
    if r.returncode:
        raise RuntimeError(json.dumps(LOG[-1]))
    return r.stdout


def compile_wat(wat, dst):
    dst = Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():
        raise FileExistsError(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.with_suffix('.wat').write_text(wat, encoding='utf-8')
    tool('wat2wasm', [dst.with_suffix('.wat'), '-o', dst])
    tool('wasm-validate', [dst])


def read(src):
    tool('wasm-validate', [src])
    return sx.parse(tool('wasm2wat', [src, '--fold-exprs']))


def source(src):
    m = read(src)
    if any(x[0] not in ('type', 'func', 'export') for x in m[1:]):
        raise ValueError('source module feature unsupported')
    fs = [x for x in m[1:] if x[0] == 'func']
    es = [x for x in m[1:] if x[0] == 'export']
    if len(fs) != 1 or es != [['export', '"run"', ['func', '0']]]:
        raise ValueError('expected one exported run')
    f = fs[0]
    ps = [a for x in f[1:] if isinstance(x, list) and x[0] == 'param' for a in x[1:]]
    if ps != ['i32'] * 3 or [x for x in f[1:] if isinstance(x, list) and x[0] == 'result'] != [['result', 'i32']]:
        raise ValueError('expected 3 i32 parameters and one i32 result')
    body = [x for x in f[1:] if isinstance(x, list) and x[0] not in ('type', 'param', 'result')]
    def walk(x):
        if x[0] == 'local.get' and len(x) == 2 and int(x[1]) in range(3):
            return ('var', int(x[1]))
        if x[0] == 'i32.const' and len(x) == 2:
            return ('const', int(x[1]) & MASK)
        if x[0] in ('i32.add', 'i32.sub', 'i32.mul') and len(x) == 3:
            return (x[0][4:], walk(x[1]), walk(x[2]))
        raise ValueError('source operation unsupported: ' + sx.emit(x))
    if len(body) != 1:
        raise ValueError('expected one expression')
    return walk(body[0])


ZERO = (0, 0, 0)


def const(n):
    return {ZERO: n & MASK} if n & MASK else {}


def var(i):
    a = [0, 0, 0]; a[i] = 1
    return {tuple(a): 1}


def add(a, b, sign=1):
    r = dict(a)
    for k, v in b.items():
        c = (r.get(k, 0) + sign*v) & MASK
        if c: r[k] = c
        else: r.pop(k, None)
    return r


def mul(a, b):
    r = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            k = tuple(x+y for x, y in zip(ka, kb))
            r[k] = (r.get(k, 0) + va*vb) & MASK
    return {k: v for k, v in r.items() if v}


def degree(a):
    return max((sum(k) for k in a), default=0)


def eval_poly(a, xyz, mask=MASK):
    return sum(c * xyz[0]**k[0] * xyz[1]**k[1] * xyz[2]**k[2] for k, c in a.items()) & mask


def to_poly(t):
    if t[0] == 'const': return const(t[1])
    if t[0] == 'var': return var(t[1])
    a, b = to_poly(t[1]), to_poly(t[2])
    return mul(a,b) if t[0]=='mul' else add(a,b, -1 if t[0]=='sub' else 1)


def matrix(t):
    # Series/parallel ABP. Shared terminals, fresh interior vertices.
    vertices = [0, 1]; edges = {}
    def edge(s, u, label):
        edges[s,u] = add(edges.get((s,u), {}), label)
    def build(t, s, u, sign=1):
        if t[0] in ('var', 'const'):
            edge(s,u,mul(const(sign), to_poly(t)))
        elif t[0] in ('add','sub'):
            build(t[1],s,u,sign); build(t[2],s,u,sign*(-1 if t[0]=='sub' else 1))
        else:
            v=len(vertices); vertices.append(v)
            build(t[1],s,v,sign); build(t[2],v,u)
    build(t,0,1)
    remaining=set(vertices); order=[]
    while remaining:
        ready=sorted(v for v in remaining if not any(u in remaining and w==v and p for (u,w),p in edges.items()))
        if not ready: raise AssertionError('ABP cycle')
        v=ready[0]; order.append(v); remaining.remove(v)
    idx={v:i for i,v in enumerate(order)}; k=len(order); n=k+1
    m=[[{} for _ in range(n)] for _ in range(n)]
    for i in range(k): m[i][i]=const(1)
    for (s,u),label in edges.items(): m[idx[s]][idx[u]]=add(m[idx[s]][idx[u]],label,-1)
    m[idx[1]][k]=const(1); m[k][idx[0]]=const(-1)
    return m


def shear(m, row, target, src, h):
    r=[[dict(p) for p in line] for line in m]
    for j in range(len(m)):
        if row: r[target][j]=add(m[target][j],mul(h,m[src][j]))
        else: r[j][target]=add(m[j][target],mul(h,m[j][src]))
    return r


def mix(m, seed):
    rng=random.Random(seed); n=len(m); poly=m; fixed=m; ops=[]; rejected=0
    for _ in range(n*12):
        a,b=rng.sample(range(n),2); row=bool(rng.randrange(2)); c=rng.choice([1,3,5,7,MASK])
        h=add(const(c),var(rng.randrange(3)))
        candidate=shear(poly,row,a,b,h)
        if max(degree(p) for line in candidate for p in line)>3 or sum(len(p) for line in candidate for p in line)>1800:
            rejected+=1; continue
        poly=candidate; fixed=shear(fixed,row,a,b,const(c)); ops.append([row,a,b,c,list(h)])
    if len(ops)<2: raise AssertionError('insufficient accepted shears')
    return fixed,poly,dict(accepted=len(ops),rejected=rejected,seed=seed,operations=ops)


def payload(m):
    n=len(m); records=[]
    for i,line in enumerate(m):
        for j,p in enumerate(line):
            for powers,c in sorted(p.items()): records.append((i*n+j,c,*powers))
    if n>16 or len(records)>1800: raise ValueError('matrix exceeds profile')
    data=struct.pack('<III', MAGIC,n,len(records)) + bytes(244)
    data+=b''.join(struct.pack('<IIIII',*r) for r in records)
    return data


def decode(data):
    if len(data)<256: raise ValueError('short coefficient data')
    magic,n,count=struct.unpack_from('<III',data)
    if magic!=MAGIC or not 2<=n<=16 or count>1800 or len(data)!=256+20*count or any(data[12:256]):
        raise ValueError('invalid coefficient header')
    m=[[{} for _ in range(n)] for _ in range(n)]
    for at in range(256,len(data),20):
        cell,c,x,y,z=struct.unpack_from('<IIIII',data,at)
        if cell>=n*n or max(x,y,z)>8: raise ValueError('invalid coefficient entry')
        i,j=divmod(cell,n); m[i][j]=add(m[i][j],{(x,y,z):c})
    return m


def kernel(data):
    # Data remains a public expanded coefficient table. Scratch is not exported.
    quoted=''.join('\\%02x'%b for b in data)
    return Path(__file__).with_name('kernel.wat').read_text(encoding='utf-8').replace('@DATA@',quoted)


def signed(v):
    return str(v if v < (1<<31) else v-(1<<32))


def poly_wat(p):
    terms=[]
    for powers,c in sorted(p.items()):
        term='(i32.const '+signed(c)+')'
        for i,k in enumerate(powers):
            for _ in range(k): term=f'(i32.mul {term} (local.get {i}))'
        terms.append(term)
    expr='(i32.const 0)'
    for term in terms: expr=f'(i32.add {expr} {term})'
    return '(module (func (export "run") (param i32 i32 i32) (result i32) '+expr+'))'


def transform(src, dst, mode, seed=221040):
    start=time.perf_counter(); t=source(src); m=matrix(t); info={}
    if mode!='unmixed':
        fixed,poly,info=mix(m,seed); m=poly if mode=='polynomial' else fixed
    compile_wat(kernel(payload(m)),dst)
    return dict(mode=mode,dimension=len(m),coefficients=sum(len(p) for line in m for p in line),
                max_degree=max(degree(p) for line in m for p in line),mix=info,
                transform_ms=(time.perf_counter()-start)*1000,sha256=digest(dst))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('output'); ap.add_argument('--mode',choices=['unmixed','constant','polynomial'],default='polynomial'); ap.add_argument('--seed',type=int,default=221040)
    a=ap.parse_args(); print(json.dumps(transform(a.source,a.output,a.mode,a.seed)))
