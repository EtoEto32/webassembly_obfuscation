"""Native saturation over a noninjective quotient representation."""
import argparse, importlib.util, json, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bucket_tools',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

def vc(v):return '(v128.const i16x8 '+' '.join(map(str,v))+')'
def vec(node):
    raw=q.vconst(node)
    return [raw[i]+256*raw[i+1] for i in range(0,16,2)]

def source(bits,ops,mode='plain'):
    if len(bits)!=8 or any(b not in range(1,9) for b in bits):raise ValueError('eight widths in 1..8')
    cap=[(1<<b)-1 for b in bits];scale=[1<<(16-b) for b in bits];factor=[1<<b for b in bits]
    if not 1<=len(ops)<=256 or any(op['sign'] not in ('+','-') or len(op['mask'])!=8 or any(not 0<=m<=c for m,c in zip(op['mask'],cap)) for op in ops):raise ValueError('bounded update masks')
    lifted=mode!='plain'
    if mode not in ('plain','canonical','zero','bucket','bad'):raise ValueError(mode)
    body=[]
    for param,local in [(0,2),(1,3)]:
        body.append(f'(local.set {local} (i16x8.min_u (i16x8.extend_low_i8x16_u (i64x2.splat (local.get {param}))) {vc(cap)}))')
    if lifted:
        initial=f'(i16x8.mul (local.get 2) {vc(scale)})'
        if mode in ('bucket','bad'):initial=f'(v128.or {initial} (local.get 3))'
        body.append(f'(local.set 2 {initial})')
        if mode!='bad':body.append(f'(local.set 3 (i16x8.mul (local.get 3) {vc(scale)}))')
    for op in ops:
        mask=[m*a for m,a in zip(op['mask'],scale)] if lifted and mode!='bad' else op['mask']
        d=f'(v128.and (local.get 3) {vc(mask)})'
        if op['sign']=='+':
            term=f'(i16x8.add_sat_u (local.get 2) {d})' if lifted else f'(i16x8.min_u (i16x8.add (local.get 2) {d}) {vc(cap)})'
        else:term=f'(i16x8.sub_sat_u (local.get 2) {d})'
        if mode=='canonical':term=f'(v128.and {term} {vc([65536-a for a in scale])})'
        body.append(f'(local.set 2 {term})')
    final='(local.get 2)'
    if lifted:
        lo=f'(i32x4.shr_u (i32x4.extmul_low_i16x8_u (local.get 2) {vc(factor)}) (i32.const 16))'
        hi=f'(i32x4.shr_u (i32x4.extmul_high_i16x8_u (local.get 2) {vc(factor)}) (i32.const 16))'
        final=f'(i16x8.narrow_i32x4_u {lo} {hi})'
    body.append(f'(i64x2.extract_lane 0 (i8x16.narrow_i16x8_u {final} {vc([0]*8)}))')
    return '(module (func (export "run") (param i64 i64) (result i64) (local v128 v128) '+' '.join(body)+'))'

def read(src):
    mod=q.read(src)
    if any(e[0] not in ('type','func','export') for e in mod[1:]):raise ValueError('pure one-function profile')
    fs=[e for e in mod[1:] if e[0]=='func']
    if len(fs)!=1:raise ValueError('one function')
    body=[e for e in fs[0][1:] if e[0] not in ('type','param','result','local')]
    try:
        cap=vec(body[0][2][2]);bits=[(c+1).bit_length()-1 for c in cap]
        if cap!=[(1<<b)-1 for b in bits]:raise ValueError('power-of-two bounds')
        ops=[]
        for e in body[2:-1]:
            term=e[2]
            if term[0]=='i16x8.min_u':term=term[1];sign='+'
            elif term[0]=='i16x8.sub_sat_u':sign='-'
            else:raise ValueError('source update')
            ops.append(dict(sign=sign,mask=vec(term[2][2])))
    except (IndexError,TypeError,KeyError) as exc:raise ValueError('source profile') from exc
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='bucket-profile-') as td:
        ref=Path(td)/'ref.wasm';q.compile(source(bits,ops),ref)
        if q.read(ref)!=mod:raise ValueError('not the supported raw source profile')
    return bits,ops

def transform(src,dst,mode):
    start=time.perf_counter();bits,ops=read(src);loaded=time.perf_counter()
    q.compile(source(bits,ops,mode),dst)
    return dict(bits=bits,ops=ops,mode=mode,read_ms=(loaded-start)*1000,transform_ms=(time.perf_counter()-start)*1000)

def recovered(table,dst):
    # Each (lane, input delta byte) stores lo, hi, translation as three i32s.
    import struct
    data=b''.join(struct.pack('<iii',row['lo'],row['hi'],row['t']) for lane in table for row in lane)
    blob=''.join('\\'+format(b,'02x') for b in data)
    body=[]
    for lane in range(8):
        x=f'(i32.wrap_i64 (i64.and (i64.shr_u (local.get 0) (i64.const {8*lane})) (i64.const 255)))'
        d=f'(i32.wrap_i64 (i64.and (i64.shr_u (local.get 1) (i64.const {8*lane})) (i64.const 255)))'
        body += [f'(local.set 2 (i32.add (i32.const {lane*256*12}) (i32.mul {d} (i32.const 12))))',
            '(local.set 3 (i32.load (local.get 2)))',
            '(local.set 4 (i32.load offset=4 (local.get 2)))',
            f'(local.set 5 (i32.add {x} (i32.load offset=8 (local.get 2))))',
            '(local.set 5 (select (local.get 3) (local.get 5) (i32.lt_s (local.get 5) (local.get 3))))',
            '(local.set 5 (select (local.get 4) (local.get 5) (i32.gt_s (local.get 5) (local.get 4))))',
            f'(local.set 6 (i64.or (local.get 6) (i64.shl (i64.extend_i32_u (local.get 5)) (i64.const {8*lane}))))']
    body.append('(local.get 6)')
    wat='(module (memory 1 1) (func (export "run") (param i64 i64) (result i64) (local i32 i32 i32 i32 i64) '+' '.join(body)+') (data (i32.const 0) "'+blob+'"))'
    q.compile(wat,dst)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['plain','canonical','zero','bucket'],default='bucket');a=ap.parse_args();q.save(str(a.output)+'.json',transform(a.source,a.output,a.mode))
