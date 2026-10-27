# -*- coding: utf-8 -*-
"""Experimental input-dependent span representation, NOT established novelty."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('span_wat', HERE.parent/'connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
MAGIC = 0x314e5053
MASK = 0xffffffff


def span(tree):
    rows = []
    dim = 1
    def visit(t, v, inv=False):
        nonlocal dim
        op = t[0]
        if op in ('var', 'const'):
            if op == 'const':
                if bool(t[1]) != inv: rows.append({0: v})
            else:
                r = {1 << t[1]: v}
                if inv: r[0] = v
                rows.append(r)
        elif op == 'xor':
            # (a AND NOT b) OR (NOT a AND b); negated XOR is equality.
            a, b = t[1:]
            visit(('or', ('and', a, ('xor', b, ('const', MASK))),
                         ('and', ('xor', a, ('const', MASK)), b)), v, inv) if not (
                             a[0] == 'const' or b[0] == 'const') else literal_xor(t, v, inv)
        elif op in ('and', 'or'):
            join = ('or' if op == 'and' else 'and') if inv else op
            if join == 'or':
                visit(t[1], v, inv); visit(t[2], v, inv)
            else:
                e = 1 << dim; dim += 1
                visit(t[1], v ^ e, inv); visit(t[2], e, inv)
        else:
            raise ValueError('Unknown source operator')
        if len(rows) > 96 or dim > 64:
            raise ValueError('Span expansion exceeds 96 rows / 64 columns')
    def literal_xor(t, v, inv):
        a,b=t[1:]
        if a[0] == 'const': visit(b,v,inv ^ bool(a[1]))
        else: visit(a,v,inv ^ bool(b[1]))
    visit(tree, 1)
    return rows, dim, {0: 1}


def add_scaled(a, b, scalar):
    out = dict(a)
    for mono, bits in b.items():
        m = mono | scalar
        out[m] = out.get(m, 0) ^ bits
        if not out[m]: del out[m]
    return out


def column_add(row, src, dst, scalar):
    delta = {mono: 1 << dst for mono,bits in row.items() if bits >> src & 1}
    return add_scaled(row, delta, scalar)


def construct(n, tree, mode, seed=20261023):
    rows, d, target = span(tree)
    rng = random.Random(seed)
    m = len(rows)
    if not m:
        rows = [{}]; m=1
    if mode not in ('span','constant','dependent'):
        raise ValueError('Invalid mode')
    operations=[]
    if mode != 'span':
        # Same row/column locations and source bits in both mixed versions.
        # Fixed prefix removes the visibly sparse basis even in the control.
        for stage in ('fixed', 'varying'):
            count = 2 * (m+d) if stage == 'fixed' else (m+d)
            for k in range(count):
                side = 'row' if k % 2 == 0 else 'column'
                size = m if side == 'row' else d
                if size < 2: continue
                a,b=rng.sample(range(size),2)
                bit = rng.randrange(n)
                scalar = (1 << bit) if stage == 'varying' and mode == 'dependent' else 0
                if side == 'row': rows[b]=add_scaled(rows[b],rows[a],scalar)
                else:
                    rows=[column_add(r,a,b,scalar) for r in rows]
                    target=column_add(target,a,b,scalar)
                operations.append([stage,side,a,b,bit])
                if sum(len(r) for r in rows+[target]) > 16000:
                    raise ValueError('Polynomial expansion budget')
    record={'n':n,'m':m,'d':d,'rows':[sorted(r.items()) for r in rows],
            'target':sorted(target.items())}
    return record, {'operations':operations,'rows':m,'columns':d,
                    'polynomial_vectors':sum(len(r) for r in rows+[target])}


def encode(record):
    n,m,d=record['n'],record['m'],record['d']
    rows=[dict(r) for r in record['rows']]+[dict(record['target'])]
    if not 1<=n<=32 or not 1<=m<=96 or not 1<=d<=64 or len(rows)!=m+1:
        raise ValueError('Descriptor shape')
    if any(any(not 0<=a<(1<<n) or not 0<b<(1<<d) for a,b in r.items()) for r in rows):
        raise ValueError('Descriptor coefficients')
    monos=sorted({a for r in rows for a in r})
    if not monos: monos=[0]
    index={a:i for i,a in enumerate(monos)}
    offsets=[0];indices=[]
    for r in rows:
        for j in range(d):
            indices.extend(index[a] for a,b in sorted(r.items()) if b>>j&1)
            offsets.append(len(indices))
    words=[MAGIC,1,n,m,d,len(monos),len(indices),*monos,*offsets,*indices]
    blob=struct.pack('<'+'I'*len(words),*words)
    if len(blob)>512*1024: raise ValueError('Public coefficient table exceeds limit')
    return blob,monos,offsets,indices


def decode(image):
    h=struct.unpack_from('<7I',image)
    magic,version,n,m,d,nm,ni=h
    if magic!=MAGIC or version!=1 or not 1<=n<=32 or not 1<=m<=96 or not 1<=d<=64:
        raise ValueError('Unsupported descriptor')
    nc=(m+1)*d
    end=28+4*(nm+nc+1+ni)
    if nm>16000 or end>len(image) or end>512*1024: raise ValueError('Descriptor size')
    monos=list(struct.unpack_from('<'+'I'*nm,image,28))
    offsets=list(struct.unpack_from('<'+'I'*(nc+1),image,28+4*nm))
    indices=list(struct.unpack_from('<'+'I'*ni,image,28+4*(nm+nc+1)))
    if offsets[0]!=0 or offsets[-1]!=ni or offsets!=sorted(offsets) or any(i>=nm for i in indices):
        raise ValueError('Invalid coefficient index')
    rows=[]
    for i in range(m+1):
        r={}
        for j in range(d):
            pos=i*d+j
            for ix in indices[offsets[pos]:offsets[pos+1]]:
                a=monos[ix];r[a]=r.get(a,0)^(1<<j)
        rows.append(sorted((a,b) for a,b in r.items() if b))
    out={'n':n,'m':m,'d':d,'rows':rows[:-1],'target':rows[-1]}
    encode(out)
    return out


def layout(record):
    blob,monos,offsets,indices=encode(record)
    n,m,d=record['n'],record['m'],record['d']
    inputs=(len(blob)+63)//64*64
    cache=inputs+4*n
    matrix=cache+4*len(monos)
    basis=matrix+4*(m+1)*d
    size=basis+4*d*d
    return blob,monos,inputs,cache,matrix,basis,math.ceil(size/65536)


def render(record, name='"run"', probe=False):
    n,m,d=record['n'],record['m'],record['d']
    blob,monos,inp,cache,mat,base,pages=layout(record)
    nm=len(monos); nc=(m+1)*d
    off=28+4*nm;idx=off+4*(nc+1)
    literal='"'+''.join('\\%02x'%b for b in blob)+'"'
    stores='\n'.join(f'(i32.store (i32.const {inp+4*i}) (local.get {i}))' for i in range(n))
    return f'''(module (memory {pages} {pages})
    {'(export "memory" (memory 0))' if probe else ''}
    (data (i32.const 0) {literal})
    (func (export {name}) (param {' '.join(['i32']*n)}) (result i32)
      (local $i i32) (local $j i32) (local $k i32) (local $a i32) (local $new i32)
      (local $v i32) (local $q i32) (local $p i32) (local $end i32)
      (local $row i32) (local $brow i32) (local $bits i32)
      {stores}
      (loop $monos
        (local.set $bits (i32.load offset=28 (i32.shl (local.get $i) (i32.const 2))))
        (local.set $v (i32.const -1)) (local.set $j (i32.const 0))
        (block $done (loop $vars
          (br_if $done (i32.eqz (local.get $bits)))
          (if (i32.and (local.get $bits) (i32.const 1)) (then
            (local.set $v (i32.and (local.get $v) (i32.load offset={inp} (i32.shl (local.get $j) (i32.const 2)))))))
          (local.set $bits (i32.shr_u (local.get $bits) (i32.const 1)))
          (local.set $j (i32.add (local.get $j) (i32.const 1))) (br $vars)))
        (i32.store offset={cache} (i32.shl (local.get $i) (i32.const 2)) (local.get $v))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $monos (i32.lt_u (local.get $i) (i32.const {nm}))))
      (local.set $i (i32.const 0))
      (loop $cells
        (local.set $p (i32.load offset={off} (i32.shl (local.get $i) (i32.const 2))))
        (local.set $end (i32.load offset={off+4} (i32.shl (local.get $i) (i32.const 2))))
        (local.set $v (i32.const 0))
        (block $cdone (loop $terms
          (br_if $cdone (i32.ge_u (local.get $p) (local.get $end)))
          (local.set $q (i32.load offset={idx} (i32.shl (local.get $p) (i32.const 2))))
          (local.set $v (i32.xor (local.get $v) (i32.load offset={cache} (i32.shl (local.get $q) (i32.const 2)))))
          (local.set $p (i32.add (local.get $p) (i32.const 1))) (br $terms)))
        (i32.store offset={mat} (i32.shl (local.get $i) (i32.const 2)) (local.get $v))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $cells (i32.lt_u (local.get $i) (i32.const {nc}))))
      (memory.fill (i32.const {base}) (i32.const 0) (i32.const {4*d*d}))
      (local.set $i (i32.const 0))
      (loop $rows
        (local.set $row (i32.add (i32.const {mat}) (i32.mul (local.get $i) (i32.const {4*d}))))
        (local.set $j (i32.const 0))
        (loop $cols
          (local.set $a (i32.load (i32.add (local.get $row) (i32.shl (local.get $j) (i32.const 2)))))
          (if (local.get $a) (then
            (local.set $brow (i32.add (i32.const {base}) (i32.mul (local.get $j) (i32.const {4*d}))))
            (local.set $new (i32.and (local.get $a) (i32.xor (i32.const -1)
               (i32.load (i32.add (local.get $brow) (i32.shl (local.get $j) (i32.const 2)))))))
            (local.set $k (local.get $j))
            (loop $elim
              (local.set $p (i32.add (local.get $row) (i32.shl (local.get $k) (i32.const 2))))
              (local.set $q (i32.add (local.get $brow) (i32.shl (local.get $k) (i32.const 2))))
              (local.set $v (i32.load (local.get $p)))
              (i32.store (local.get $q) (i32.xor (i32.load (local.get $q)) (i32.and (local.get $v) (local.get $new))))
              (i32.store (local.get $p) (i32.xor (local.get $v) (i32.and (local.get $a) (i32.load (local.get $q)))))
              (local.set $k (i32.add (local.get $k) (i32.const 1)))
              (br_if $elim (i32.lt_u (local.get $k) (i32.const {d}))))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br_if $cols (i32.lt_u (local.get $j) (i32.const {d}))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $rows (i32.lt_u (local.get $i) (i32.const {m}))))
      (local.set $j (i32.const 0))
      (loop $reduce
        (local.set $a (i32.load offset={mat+4*m*d} (i32.shl (local.get $j) (i32.const 2))))
        (local.set $brow (i32.add (i32.const {base}) (i32.mul (local.get $j) (i32.const {4*d}))))
        (local.set $k (local.get $j))
        (loop $target
          (local.set $p (i32.add (i32.const {mat+4*m*d}) (i32.shl (local.get $k) (i32.const 2))))
          (i32.store (local.get $p) (i32.xor (i32.load (local.get $p)) (i32.and (local.get $a)
            (i32.load (i32.add (local.get $brow) (i32.shl (local.get $k) (i32.const 2)))))))
          (local.set $k (i32.add (local.get $k) (i32.const 1)))
          (br_if $target (i32.lt_u (local.get $k) (i32.const {d}))))
        (local.set $j (i32.add (local.get $j) (i32.const 1)))
        (br_if $reduce (i32.lt_u (local.get $j) (i32.const {d}))))
      (local.set $j (i32.const 0)) (local.set $v (i32.const 0))
      (loop $result
        (local.set $v (i32.or (local.get $v) (i32.load offset={mat+4*m*d} (i32.shl (local.get $j) (i32.const 2)))))
        (local.set $j (i32.add (local.get $j) (i32.const 1)))
        (br_if $result (i32.lt_u (local.get $j) (i32.const {d}))))
      (i32.xor (local.get $v) (i32.const -1))))'''


def save(wat, dest):
    dest=Path(dest)
    if dest.exists(): raise FileExistsError(dest)
    dest.parent.mkdir(parents=True,exist_ok=True)
    src=dest.with_suffix('.wat')
    if src.exists(): raise FileExistsError(src)
    src.write_text(wat,encoding='utf8')
    w.tool('wat2wasm',[src,'-o',dest])
    w.tool('wasm-validate',[dest])


def optimize(src,dest):
    if Path(dest).exists():raise FileExistsError(dest)
    w.tool('wasm-opt',[src,'-O3','--enable-bulk-memory','-o',dest])
    w.tool('wasm-validate',[dest])


def transform(src,dest,mode,seed=20261023):
    start=time.perf_counter()
    n,name,t=w.source(Path(src))
    if n>32:raise ValueError('At most 32 Boolean variables')
    if name!='"run"':raise ValueError('Prototype export must be run')
    record,meta=construct(n,t,mode,seed)
    save(render(record,name),dest)
    return {**meta,'elapsed_ms':(time.perf_counter()-start)*1000,
            'linear_memory_bytes':65536*layout(record)[-1]}


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output')
    a.add_argument('--mode',choices=['span','constant','dependent'],default='dependent')
    a.add_argument('--seed',type=int,default=20261023)
    q=a.parse_args();print(json.dumps(transform(q.input,q.output,q.mode,q.seed)))
