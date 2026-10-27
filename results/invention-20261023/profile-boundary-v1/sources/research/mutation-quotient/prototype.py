"""Exact translation quotient for a restricted mutable Wasm state machine.

No secrecy or resistance claim. The representative implementation deliberately
tests whether a cheap equivalent state machine defeats the proposed protection.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('mutation_wasm', HERE.parent/'isotope-swizzle/prototype.py')
q = importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
MASK = 0xffffffff
MAGIC = 0x3153514d
BASE = 64


def erased(k, width=32):
    x = (k-1) & ((1 << width)-1)
    return width if not x else (x & -x).bit_length()-1


def canonical(xs, d):
    low = xs[0] & ((1 << (32-d))-1)
    return [low] + [(v-xs[0]) & MASK for v in xs[1:]]


def representative(xs, d):
    high = xs[0] & (MASK ^ ((1 << (32-d))-1))
    return [(v-high) & MASK for v in xs]


def token(data):
    return '"' + ''.join('\\%02x' % b for b in data) + '"'


def decode(token_):
    s=token_[1:-1]; out=bytearray(); i=0
    escapes={'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}
    while i < len(s):
        if s[i] != '\\':out.extend(s[i].encode('utf-8'));i+=1
        elif len(s) >= i+3 and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):
            out.append(int(s[i+1:i+3],16));i+=3
        else:out.append(escapes[s[i+1]]);i+=2
    return out


def render(xs, k, mode=0, d=None):
    """xs are physical initial words, not the pre-transformation secrets."""
    n=len(xs);d=erased(k) if d is None else d
    if not 2<=n<=1024 or mode not in (0,1,2) or not 0<=d<=32:raise ValueError('schema')
    data=struct.pack('<5I',MAGIC,n,k&MASK,mode,d)+bytes(BASE-20)+struct.pack('<%dI'%n,*xs)
    ptr=lambda x:f'(i32.add (i32.const {BASE}) (i32.shl {x} (i32.const 2)))'
    load=lambda x:f'(i32.load {ptr(x)})'
    store=lambda x,v:f'(i32.store {ptr(x)} {v})'
    i='(local.get 1)';j='(local.get 2)'
    if mode==2:
        # Logical representative uses a low anchor plus stored differences.
        value=lambda ix:f'(i32.add (call $rel {ix}) (i32.load (i32.const {BASE})))'
        update=f'''(if (i32.eqz {i})
          (then
            (local.set 5 (i32.sub (i32.load (i32.const {BASE})) (local.get 4)))
            (local.set 6 (i32.const 1))
            (loop $fix
              {store('(local.get 6)',f'(i32.add {load("(local.get 6)")} (local.get 5))')}
              (local.set 6 (i32.add (local.get 6) (i32.const 1)))
              (br_if $fix (i32.lt_u (local.get 6) (i32.const {n}))))
            (i32.store (i32.const {BASE}) (i32.and (local.get 4) (i32.const {(1<<(32-d))-1}))))
          (else {store(i,f'(i32.sub (local.get 4) (i32.load (i32.const {BASE})))')}))'''
        result=f'(i32.sub (call $rel {i}) (call $rel {j}))'
        helper=f'''(func $rel (param i32) (result i32)
          (if (result i32) (i32.eqz (local.get 0)) (then (i32.const 0))
            (else {load('(local.get 0)')})))'''
    else:
        value=load;update=store(i,'(local.get 4)');result=f'(i32.sub {load(i)} {load(j)})';helper=''
    writes=' '.join(store(f'(i32.const {ii})',f'(i32.const {v})') for ii,v in enumerate(xs))
    return f'''(module (memory 1 1) (data (i32.const 0) {token(data)})
      (func $run (export "run") (param i32 i32 i32 i32) (result i32) (local i32 i32 i32)
        (if (i32.or (i32.gt_u (local.get 0) (i32.const 3))
          (i32.or (i32.ge_u {i} (i32.const {n})) (i32.ge_u {j} (i32.const {n}))))
          (then unreachable))
        (if (local.get 0) (then
          (local.set 4 (i32.add (local.get 3)
            (if (result i32) (i32.eq (local.get 0) (i32.const 2))
              (then {value(j)})
              (else (if (result i32) (i32.eq (local.get 0) (i32.const 3))
                (then (i32.mul (i32.const {k&MASK}) {value(i)}))
                (else {value(i)}))))))
          {update})) {result})
      (func (export "reset") {writes}) {helper})'''


def read(src, allow_optimized=True):
    t=time.perf_counter();m=q.read(src)
    if any(e[0] not in ('type','func','export','data','memory') for e in m[1:]):raise ValueError('module profile')
    ds=[e for e in m[1:] if e[0]=='data'];data=bytearray(65536)
    for seg in ds:
        if len(seg)<3 or seg[1][:1]!=['i32.const']:raise ValueError('active data required')
        offset=int(seg[1][1],0)&MASK;part=b''.join(decode(x) for x in seg[2:])
        if offset+len(part)>len(data):raise ValueError('data extent')
        data[offset:offset+len(part)]=part
    magic,n,k,mode,d=struct.unpack('<5I',data[:20])
    if magic!=MAGIC or not 2<=n<=1024 or d!=erased(k) or mode not in (0,1,2):raise ValueError('invalid quotient certificate')
    if any(data[BASE+4*n:]) or any(data[20:BASE]):raise ValueError('data extent')
    xs=list(struct.unpack('<%dI'%n,data[BASE:BASE+4*n]));parsed=time.perf_counter()
    # Public descriptors are not trusted. Validate the actual code against the
    # complete supported generator, including bounds, operation and reset.
    with tempfile.TemporaryDirectory(prefix='mutation-quotient-') as td:
        check=Path(td)/'expected.wasm';q.compile(render(xs,k,mode,d),check)
        same=q.read(check)==m;optimization='raw'
        if not same and allow_optimized:
            opt=Path(td)/'optimized.wasm';q.w.tool('wasm-opt',[check,'-O3','-o',opt]);same=q.read(opt)==m;optimization='O3'
        if not same:raise ValueError('actual code is outside the certified profile')
    return dict(xs=xs,n=n,k=k,mode=mode,d=d,optimization=optimization,read_ms=(parsed-t)*1000,profile_ms=(time.perf_counter()-parsed)*1000)


def transform(src,dst,mode='canonical'):
    t=time.perf_counter();p=read(src)
    if p['mode']!=0:raise ValueError('source must be plain')
    xs=canonical(p['xs'],p['d']) if mode=='canonical' else representative(p['xs'],p['d'])
    q.compile(render(xs,p['k'],2 if mode=='canonical' else 1),dst)
    return dict(erased_bits=p['d'],ms=(time.perf_counter()-t)*1000,source=q.digest(src),output=q.digest(dst))


def recover(src,dst):
    t=time.perf_counter();p=read(src);start=time.perf_counter()
    xs=p['xs'] if p['mode']!=2 else [p['xs'][0]]+[(v+p['xs'][0])&MASK for v in p['xs'][1:]]
    analysis=(time.perf_counter()-start)*1000
    q.compile(render(xs,p['k']),dst)
    return dict(n=p['n'],k=p['k'],erased_bits=p['d'],analysis_ms=analysis,read_ms=p['read_ms'],profile_ms=p['profile_ms'],total_ms=(time.perf_counter()-t)*1000,output=q.digest(dst))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['transform','recover']);a.add_argument('source');a.add_argument('output');a.add_argument('--mode',choices=['canonical','representative'],default='canonical');v=a.parse_args()
    print(json.dumps(transform(v.source,v.output,v.mode) if v.command=='transform' else recover(v.source,v.output),indent=2))
