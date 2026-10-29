"""Encoding of private packed saturating counter banks; restricted Wasm profile."""
import argparse, importlib.util, random, time, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('sa_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
MODES=('plain','complement','random-min','anchor-min','anchor-zero','anchor-native','random-table')
def vc(n):return q.w.emit(q.vc([n]*16))
def table(t,e,strict=False):return q.w.emit(['i8x16.swizzle' if strict else 'i8x16.relaxed_swizzle',q.vc(t),q.w.parse('(module '+e+')')[1]])
def perm(mode,seed):
    if mode=='plain':return list(range(16))
    if mode=='complement':return list(reversed(range(16)))
    a=list(range(16));random.Random(seed).shuffle(a)
    if mode.startswith('anchor'):
        z=a.index(0);a[z],a[15]=a[15],a[z]
    return a
def nib(e,high=False):return f'(i8x16.shr_u {e} (i32.const 4))' if high else f'(v128.and {e} {vc(15)})'
def packed(lo,hi):return f'(v128.or {lo} (i8x16.shl {hi} (i32.const 4)))'
def build(n,mode='plain',encoding=None):
    if n<32 or n>65536 or n%32:raise q.Unsupported('counter count must be 32..65536, divisible by 32')
    e=encoding if encoding is not None else perm(mode,7);d=q.inv(e);size=n//2
    def encode(v):return v if mode=='plain' else f'(v128.xor {v} {vc(15)})' if mode=='complement' else table(e,v)
    def decode(v):return v if mode=='plain' else f'(v128.xor {v} {vc(15)})' if mode=='complement' else table(d,v)
    def encode_packed(v):
        if mode=='plain':return v
        if mode=='complement':return f'(v128.xor {v} {vc(255)})'
        return packed(encode(nib(v)),encode(nib(v,True)))
    def step(a,b):
        if mode=='complement':return f'(i8x16.sub_sat_u (i8x16.add {a} {b}) {vc(15)})'
        if mode=='random-table':
            rows=[[e[min(d[x]+d[y],15)] for x in range(16)] for y in range(16)]
            v=table(rows[0],a)
            for j in range(1,16):v=f'(v128.bitselect {table(rows[j],a)} {v} (i8x16.eq {b} {vc(j)}))'
            return v
        x,y=decode(a),decode(b);s=f'(i8x16.add {x} {y})'
        if mode=='anchor-zero':
            if e[15]!=0:raise q.Unsupported('saturated value must encode to zero')
            return table(e,s,strict=True)
        if mode=='anchor-native':
            s=f'(i8x16.sub (i8x16.add_sat_u (i8x16.add {x} {vc(240)}) {y}) {vc(240)})'
        else:s=f'(i8x16.min_u {s} {vc(15)})'
        return encode(s)
    # Four nibble locals avoid accidental exponential code expansion in the
    # conventional 16-row fused lookup comparator.
    merge=f'''(func (local i32) (local v128 v128 v128 v128)
      (block (loop (br_if 1 (i32.ge_u (local.get 0) (i32.const {size})))
        (local.set 1 (v128.load align=1 (local.get 0)))
        (local.set 2 (v128.load align=1 (i32.add (local.get 0) (i32.const {size}))))
        (local.set 3 {nib('(local.get 1)',True)}) (local.set 4 {nib('(local.get 2)',True)})
        (local.set 1 {nib('(local.get 1)')}) (local.set 2 {nib('(local.get 2)')})
        (v128.store align=1 (local.get 0) {packed(step('(local.get 1)','(local.get 2)'),step('(local.get 3)','(local.get 4)'))})
        (local.set 0 (i32.add (local.get 0) (i32.const 16))) (br 0))))'''
    if mode=='plain':age=f'(v128.and (i8x16.shr_u (local.get 1) (i32.const 1)) {vc(119)})'
    elif mode=='complement':age=f'(v128.or (v128.and (i8x16.shr_u (local.get 1) (i32.const 1)) {vc(119)}) {vc(136)})'
    else:
        t=[e[d[x]//2] for x in range(16)];age=packed(table(t,nib('(local.get 1)')),table(t,nib('(local.get 1)',True)))
    decay=f'''(func (local i32) (local v128)
      (block (loop (br_if 1 (i32.ge_u (local.get 0) (i32.const {size})))
        (local.set 1 (v128.load align=1 (local.get 0)))
        (v128.store align=1 (local.get 0) {age})
        (local.set 0 (i32.add (local.get 0) (i32.const 16))) (br 0))))'''
    reset=f'(func (memory.fill (i32.const 0) (i32.const {e[0]*17}) (i32.const {n})))'
    init=f'''(func (param i32) (local i32) (local v128)
      (block (loop (br_if 1 (i32.ge_u (local.get 1) (i32.const {n})))
        (local.set 0 (i32.add (i32.mul (local.get 0) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 2 (i32x4.splat (local.get 0)))
        (v128.store align=1 (local.get 1) {encode_packed('(local.get 2)')})
        (local.set 1 (i32.add (local.get 1) (i32.const 16))) (br 0))))'''
    guard=f'''(if (i32.or (i32.ge_u (local.get 0) (i32.const {n})) (i32.ge_u (local.get 1) (i32.const 2))) (then (unreachable)))'''
    addr=f'(i32.add (i32.shr_u (local.get 0) (i32.const 1)) (i32.mul (local.get 1) (i32.const {size})))'
    shift='(i32.shl (i32.and (local.get 0) (i32.const 1)) (i32.const 2))'
    scalar=f'(i32.and (i32.shr_u (i32.load8_u {addr}) {shift}) (i32.const 15))'
    decoded=scalar if mode=='plain' else f'(i32.xor {scalar} (i32.const 15))' if mode=='complement' else f'(i8x16.extract_lane_u 0 {decode(f"(i8x16.splat {scalar})")})'
    getter=f'(func (param i32 i32) (result i32) {guard} {decoded})'
    val='(i32.and (local.get 2) (i32.const 15))'
    encoded=val if mode=='plain' else f'(i32.xor {val} (i32.const 15))' if mode=='complement' else f'(i8x16.extract_lane_u 0 {encode(f"(i8x16.splat {val})")})'
    setter=f'''(func (param i32 i32 i32) (local i32 i32) {guard}
      (local.set 3 {addr}) (local.set 4 {shift})
      (i32.store8 (local.get 3) (i32.or
        (i32.and (i32.load8_u (local.get 3)) (i32.xor (i32.shl (i32.const 15) (local.get 4)) (i32.const 255)))
        (i32.shl {encoded} (local.get 4)))))'''
    checksum=f'''(func (result i32) (local i32 i32)
      (block (loop (br_if 1 (i32.ge_u (local.get 0) (i32.const {n})))
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 31))
          (i32.add (call 4 (local.get 0) (i32.const 0)) (call 4 (local.get 0) (i32.const 1)))))
        (local.set 0 (i32.add (local.get 0) (i32.const 1))) (br 0))) (local.get 1))'''
    exports=' '.join(f'(export "{name}" (func {i}))' for i,name in enumerate(('merge','decay','reset','init','get','set','checksum')))
    return f'(module (memory 1 1) {merge} {decay} {reset} {init} {getter} {setter} {checksum} {exports} (start 2))'

def canonical(m):
    def rec(e):
        if not isinstance(e,list):return e
        if e[0]=='v128.const':return q.vc(q.vconst(e))
        if e[0]=='i32.const':return ['i32.const',str(int(e[1],0)&0xffffffff)]
        if e[0]=='module':
            # Stable grouping preserves order within each Wasm index space.
            return ['module',*[rec(x) for x in sorted(e[1:],key=lambda x:x[0]) if x[0]!='type']]
        if e[0]=='func':
            kinds=('param','result','local');decl=[]
            for k in kinds:
                ts=[v for x in e[1:] if isinstance(x,list) and x[0]==k for v in x[1:]]
                if ts:decl.append([k,*ts])
            return ['func',*decl,*[rec(x) for x in e[1:] if not isinstance(x,list) or x[0] not in (*kinds,'type')]]
        return [rec(x) for x in e]
    return rec(m)
def parse(src):
    m=q.read(src);fs=[x for x in m[1:] if x[0]=='func']
    if len(fs)!=7:raise q.Unsupported('seven-function private-bank profile')
    fills=[e for e in q.walk(fs[2]) if e[0]=='memory.fill']
    if len(fills)!=1 or fills[0][-1][0]!='i32.const':raise q.Unsupported('reset length')
    n=int(fills[0][-1][1],0)
    if canonical(m)!=canonical(q.w.parse(build(n))):raise q.Unsupported('source differs from supported bank implementation')
    return n
def transform(src,dst,mode,seed=7):
    if mode not in MODES:raise q.Unsupported('unknown transform mode')
    t=time.perf_counter();n=parse(src);r=time.perf_counter();e=perm(mode,seed)
    text=build(n,mode,e);b=time.perf_counter();q.compile(text,dst)
    return dict(mode=mode,seed=seed,counters_per_bank=n,read_ms=(r-t)*1000,build_ms=(b-r)*1000,ms=(time.perf_counter()-t)*1000,encoding=e,linear_memory_bytes=65536,packed_data_bytes=n)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=MODES,default='anchor-zero');ap.add_argument('--seed',type=int,default=7);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.seed)))
