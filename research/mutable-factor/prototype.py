"""Restricted mutable graph factorization and scheme-aware abstraction.

This tests a data-refinement hypothesis; no novelty or resistance is presumed.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import struct
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
s = importlib.util.spec_from_file_location('factor_common', HERE.parent/'mutation-quotient/prototype.py')
c = importlib.util.module_from_spec(s); s.loader.exec_module(c)
q = c.q


def packed(values):
    return struct.pack('<%dI' % len(values), *values)


def arrays(edges, payload, mode, perm=None):
    n = len(edges)
    if n not in (4, 8, 16, 32, 64, 128, 256): raise ValueError('power-of-two size 4..256')
    if len(payload) != n or any(not 0 <= x < n for x in edges): raise ValueError('graph arrays')
    if mode == 'plain': return edges + payload
    if mode not in ('fixed', 'moving', 'bad-order'): raise ValueError('mode')
    if sorted(perm) != list(range(n)): raise ValueError('permutation')
    b = [0]*n
    for i in range(n): b[perm[i]] = edges[i]
    return perm + b + payload


def render(edges, payload, mode='plain', perm=None, diagnostic=False):
    n = len(edges); data = packed(arrays(edges, payload, mode, perm))
    g = lambda x: '(local.get %s)' % x
    load = lambda x, base=0: f'(i32.load offset={base} (i32.shl {x} (i32.const 2)))'
    store = lambda x, val, base=0: f'(i32.store offset={base} (i32.shl {x} (i32.const 2)) {val})'
    init = f'(memory.init 0 (i32.const 0) (i32.const 0) (i32.const {len(data)}))'
    guard = ' '.join(f'(if (i32.ge_u {g(i)} (i32.const {n})) (then unreachable))' for i in range(3))
    if mode == 'plain':
        update = store(g(0), g(1)); successor = load(g(2)); payload_base = n*4
    else:
        successor = load(load(g(2)), n*4); payload_base = n*8
        if mode == 'fixed': update = store(load(g(0)), g(1), n*4)
        else:
            update = f'''(local.set 5 (i32.and (i32.add (i32.add {g(0)} {g(1)}) {g(3)}) (i32.const {n-1})))
              (local.set 6 {load(g(0))}) (local.set 7 {load(g(5))})
              (local.set 8 {load(g(7),n*4)})
              {store(g(0),g(7))} {store(g(5),g(6))} '''
            writes = [store(g(6),g(8),n*4), store(g(7),g(1),n*4)]
            if mode == 'bad-order': writes.reverse()
            update += ' '.join(writes)
    return f'''(module (memory 1 1) {'(export "memory" (memory 0))' if diagnostic else ''}
      (data {c.token(data)})
      (func $reset (export "reset") {init}) (start $reset)
      (func $run (export "run") (param i32 i32 i32 i32) (result i32)
        (local i32 i32 i32 i32 i32)
        {guard} {update}
        (local.set 3 (i32.and {g(3)} (i32.const 255)))
        (block $done (loop $walk
          (br_if $done (i32.eqz {g(3)}))
          (local.set 4 (i32.xor (i32.rotl {g(4)} (i32.const 5)) {load(g(2),payload_base)}))
          (local.set 2 {successor})
          (local.set 3 (i32.sub {g(3)} (i32.const 1))) (br $walk))) {g(4)}))'''


def data_of(m):
    ds = [e for e in m[1:] if e[0] == 'data']
    if len(ds) != 1: raise ValueError('one passive data segment')
    data = b''.join(c.decode(t) for t in ds[0][1:] if isinstance(t,str) and t.startswith('"'))
    if len(data)%4: raise ValueError('word data')
    return list(struct.unpack('<%dI' % (len(data)//4), data))


def recognize(src, allowed):
    """Read delivered binary only; validate whole semantics-bearing profile."""
    m=q.read(src); values=data_of(m)
    for mode in allowed:
        parts=2 if mode=='plain' else 3
        if len(values)%parts: continue
        n=len(values)//parts
        if n not in (4,8,16,32,64,128,256): continue
        if mode=='plain': edges,payload=values[:n],values[n:];perm=None
        else:
            perm,b,payload=values[:n],values[n:2*n],values[2*n:]
            if sorted(perm)!=list(range(n)) or any(v>=n for v in b): continue
            edges=[b[i] for i in perm]
        if any(e>=n for e in edges): continue
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as td:
            raw=Path(td)/'raw.wasm'; q.compile(render(edges,payload,mode,perm),raw)
            if q.read(raw)==m: return edges,payload,mode,perm
            opt=Path(td)/'opt.wasm';q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',opt])
            if q.read(opt)==m: return edges,payload,mode,perm
    raise ValueError('unsupported or changed profile')


def transform(src,dst,mode,seed):
    t=time.perf_counter();edges,payload,_,_=recognize(src,['plain'])
    perm=list(range(len(edges)));random.Random(seed).shuffle(perm)
    q.compile(render(edges,payload,mode,perm),dst)
    return dict(ms=(time.perf_counter()-t)*1000,n=len(edges),mode=mode)


def recover(src,dst):
    t=time.perf_counter();edges,payload,mode,_=recognize(src,['fixed','moving'])
    q.compile(render(edges,payload),dst)
    return dict(ms=(time.perf_counter()-t)*1000,n=len(edges),identified_mode=mode)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['transform','recover']);a.add_argument('src');a.add_argument('dst');a.add_argument('--mode',choices=['fixed','moving'],default='moving');a.add_argument('--seed',type=int,default=20261023);v=a.parse_args()
    print(json.dumps(transform(v.src,v.dst,v.mode,v.seed) if v.command=='transform' else recover(v.src,v.dst)))
