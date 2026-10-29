"""Content-derived cyclic layout; restricted i32 memory experiment."""
import argparse, copy, importlib.util, struct, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('layout_common',ROOT/'research/page-block-codec/prototype.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
q=old.q
sx=q.w
MASK=(1<<32)-1

def h(x): return (x^(x>>13))&3
def phase(v): return sum(map(h,v))&3
def rotate(v,k): return [v[(j-k)%4] for j in range(4)]
def codec(data,mode,inverse=False):
    result=bytearray(len(data))
    for start in range(0,len(data),16):
        v=list(struct.unpack_from('<4I',data,start))
        k=1 if mode=='fixed' else phase(v)
        struct.pack_into('<4I',result,start,*rotate(v,-k if inverse else k))
    return bytes(result)

IND='(v128.const i8x16 '+' '.join(map(str,range(16)))+')'
IDS='(v128.const i32x4 0 1 2 3)'
def helpers(mode,pages):
    check='(unreachable)' if not pages else f'(if (i64.gt_u (local.get $a) (i64.const {pages*65536-4})) (then (unreachable)))'
    init=f'''{check}
    (local.set $b (i32.and (i32.wrap_i64 (local.get $a)) (i32.const -16)))
    (local.set $i (i32.and (i32.shr_u (i32.wrap_i64 (local.get $a)) (i32.const 2)) (i32.const 3)))
    (local.set $v (v128.load (local.get $b)))'''
    getphase='(i32.const 1)' if mode=='fixed' else '(call $layout_phase (local.get $v))'
    setup=f'''{init} (local.set $s {getphase})'''
    if mode=='full':
        setup+='(local.set $v (call $layout_rotate (local.get $v) (i32.sub (i32.const 0) (local.get $s))))'
        setup+='(local.set $j (local.get $i))'
    else:
        setup+='(local.set $j (i32.and (i32.add (local.get $i) (local.get $s)) (i32.const 3)))'
    get='(call $layout_get (local.get $v) (local.get $j))'
    patch=f'(v128.bitselect (i32x4.splat (local.get $x)) (local.get $v) (i32x4.eq {IDS} (i32x4.splat (local.get $j))))'
    update=f'(local.set $old {get}) (local.set $v {patch})'
    if mode=='full':
        update+='(local.set $v (call $layout_rotate (local.get $v) (call $layout_phase (local.get $v))))'
    elif mode=='transport':
        update+='(local.set $v (call $layout_rotate (local.get $v) (i32.sub (call $layout_h (local.get $x)) (call $layout_h (local.get $old)))))'
    loc='(local $b i32) (local $i i32) (local $j i32) (local $s i32) (local $old i32) (local $v v128)'
    terms=[f'(call $layout_h (i32x4.extract_lane {i} (local.get $v)))' for i in range(4)]
    total=terms[0]
    for t in terms[1:]:total=f'(i32.add {total} {t})'
    return f'''
    (func $layout_h (param $x i32) (result i32) (i32.and (i32.xor (local.get $x) (i32.shr_u (local.get $x) (i32.const 13))) (i32.const 3)))
    (func $layout_phase (param $v v128) (result i32) (i32.and {total} (i32.const 3)))
    (func $layout_rotate (param $v v128) (param $s i32) (result v128)
      (i8x16.swizzle (local.get $v) (v128.and (i8x16.sub {IND} (i8x16.splat (i32.shl (local.get $s) (i32.const 2)))) (i8x16.splat (i32.const 15)))))
    (func $layout_get (param $v v128) (param $j i32) (result i32)
      (i32x4.extract_lane 0 (i8x16.swizzle (local.get $v) (i8x16.add {IND} (i8x16.splat (i32.shl (local.get $j) (i32.const 2)))))))
    (func $layout_load (param $a i64) (result i32) {loc} {setup} {get})
    (func $layout_store (param $a i64) (param $x i32) {loc} {setup} {update} (v128.store (local.get $b) (local.get $v)))'''

def aligned(t):
    if not isinstance(t,list):return False
    if t[0]=='i32.const':return (int(t[1])&3)==0
    if t[0]=='i32.and':return any(aligned(x) for x in t[1:])
    if t[0] in ('i32.add','i32.sub','i32.or','i32.xor'):return all(aligned(x) for x in t[1:])
    if t[0]=='i32.shl' and t[2][0]=='i32.const':return (int(t[2][1])&31)>=2
    return False

def initial(m):
    mem=[x for x in m[1:] if x[0]=='memory']
    if len(mem)!=1 or len(mem[0])!=3 or mem[0][1]!=mem[0][2] or not mem[0][1].isdigit():raise ValueError('fixed memory32 required')
    pages=int(mem[0][1])
    if pages>2:raise ValueError('0..2 pages profile')
    data=bytearray(pages*65536)
    for seg in [x for x in m[1:] if x[0]=='data']:
        if len(seg)!=3 or seg[1][0]!='i32.const':raise ValueError('constant data required')
        p=int(seg[1][1])&MASK;raw=old.unescape(seg[2])
        if p+len(raw)>len(data):raise ValueError('data outside memory')
        data[p:p+len(raw)]=raw
    return pages,bytes(data)

def setdata(m,data):
    m[:]=[m[0]]+[x for x in m[1:] if x[0]!='data']
    end=len(data.rstrip(b'\x00'))
    if end:m.append(['data',['i32.const','0'],'"'+''.join('\\%02x'%b for b in data[:end])+'"'])

ALLOWED=set('func type param result local block loop if then else br br_if return drop nop unreachable local.get local.set local.tee select'.split())
ALLOWED.update('i32.'+x for x in 'const add sub mul xor and or shl shr_u shr_s rotl rotr clz ctz popcnt eqz eq ne lt_u lt_s le_u le_s gt_u gt_s ge_u ge_s div_u div_s rem_u rem_s'.split())

def lower(m,mode):
    if mode not in ('fixed','full','transport','bad'):raise ValueError('mode')
    if any(x[0] not in ('type','memory','data','func','export') for x in m[1:]):raise ValueError('module feature')
    if any(x[2][0]!='func' for x in m[1:] if x[0]=='export'):raise ValueError('private memory required')
    pages,data=initial(m)
    for f in [x for x in m[1:] if x[0]=='func']:
        if any(isinstance(x,str) and x.startswith('$layout_') for x in f):raise ValueError('reserved name')
    def rewrite(t):
        if not isinstance(t,list):return t
        op=t[0]
        if op in ('i32.load','i32.store'):
            args=[x for x in t[1:] if isinstance(x,list)];off=0
            for a in [x for x in t[1:] if isinstance(x,str)]:
                if a.startswith('offset='):off=int(a[7:])
                elif not a.startswith('align='):raise ValueError('memarg')
            if len(args)!=(1 if op=='i32.load' else 2) or not aligned(args[0]) or off%4:raise ValueError('provably word-aligned access required')
            a=['i64.add',['i64.extend_i32_u',rewrite(args[0])],['i64.const',str(off)]]
            return ['call','$layout_load' if op=='i32.load' else '$layout_store',a,*[rewrite(x) for x in args[1:]]]
        if op not in ALLOWED:raise ValueError('unsupported instruction '+op)
        if op in ('param','local','result') and any(x not in ('i32',) and not x.startswith('$') for x in t[1:]):raise ValueError('i32 source only')
        return [op,*[rewrite(x) for x in t[1:]]]
    out=copy.deepcopy(m)
    for i,t in enumerate(out[1:],1):
        if t[0]=='func':out[i]=rewrite(t)
    setdata(out,codec(data,mode))
    out.extend(sx.parse('(module '+helpers(mode,pages)+')')[1:])
    return out

def transform(src,dst,mode):
    t=time.perf_counter();m=q.read(src);out=lower(m,mode);q.compile(sx.emit(out),dst)
    return dict(mode=mode,transform_ms=(time.perf_counter()-t)*1000)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--mode',choices=['fixed','full','transport'],default='transport');a=ap.parse_args();print(transform(a.input,a.output,a.mode))
