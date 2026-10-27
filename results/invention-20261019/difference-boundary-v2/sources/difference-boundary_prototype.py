"""Restricted binary transform: differential memory, overlap-safe bulk repair."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('diff_common', ROOT/'research/zero-extent/prototype.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
w = c.w
MODES = ('plain', 'xor', 'roundtrip', 'two', 'shared')
MASK = 167

def encode(data, mode):
    if mode == 'plain': return bytes(data)
    if mode == 'xor': return bytes(x ^ MASK for x in data)
    return bytes(x ^ (data[i-1] if i else 0) for i,x in enumerate(data))

def decode(data, mode):
    if mode in ('plain','xor'): return encode(data, mode)
    out=bytearray();v=0
    for x in data: v ^= x; out.append(v)
    return bytes(out)

def digest(mode, n):
    value = '(i32.load8_u (local.get $i))'
    if mode == 'xor': value = f'(i32.xor {value} (i32.const {MASK}))'
    elif mode != 'plain': value = f'(local.tee $v (i32.xor (local.get $v) {value}))'
    return f'''(func $digest (export "digest") (result i32) (local $i i32) (local $v i32) (local $h i32)
      (local.set $h (i32.const 2166136261))
      (loop $hash
        (local.set $h (i32.mul (i32.xor (local.get $h) {value}) (i32.const 16777619)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br_if $hash (i32.lt_u (local.get $i) (i32.const {n}))))
      (local.get $h))'''

XOR_RANGE = '''(func $range (param $i i32) (param $end i32) (result i32) (local $r i32)
 (block $done (loop $scan
  (br_if $done (i32.ge_u (local.get $i) (local.get $end)))
  (local.set $r (i32.xor (local.get $r) (i32.load8_u (local.get $i))))
  (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $scan))) (local.get $r))'''

def wat(data, mode):
    """data is already in the selected representation, never auto-decoded here."""
    n=len(data)
    if not 1<=n<=65536 or mode not in MODES: raise ValueError('Profile/length unsupported')
    bounds=f'''(if (i32.or
       (i64.gt_u (i64.add (i64.extend_i32_u (local.get $d)) (i64.extend_i32_u (local.get $n))) (i64.const {n}))
       (i64.gt_u (i64.add (i64.extend_i32_u (local.get $s)) (i64.extend_i32_u (local.get $n))) (i64.const {n})))
      (then (unreachable)))'''
    cp='(memory.copy (local.get $d) (local.get $s) (local.get $n))'
    helper=''; locals=''; body=cp
    if mode == 'roundtrip':
        locals='(local $i i32) (local $v i32)'
        body=f'''(if (i32.eqz (local.get $n)) (then (return)))
        (loop $decode
          (local.set $v (i32.xor (local.get $v) (i32.load8_u (local.get $i))))
          (i32.store8 (local.get $i) (local.get $v))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br_if $decode (i32.lt_u (local.get $i) (i32.const {n}))))
        {cp}
        (local.set $i (i32.const {n-1}))
        (block $done (loop $encode
          (br_if $done (i32.eqz (local.get $i)))
          (i32.store8 (local.get $i) (i32.xor (i32.load8_u (local.get $i)) (i32.load8_u (i32.sub (local.get $i) (i32.const 1)))))
          (local.set $i (i32.sub (local.get $i) (i32.const 1))) (br $encode)))'''
    elif mode in ('two','shared'):
        helper=XOR_RANGE
        locals='(local $lo i32) (local $hi i32) (local $c0 i32) (local $c1 i32) (local $common i32)'
        calc='''(local.set $c0 (call $range (local.get $lo) (local.get $hi)))
        (local.set $c1 (call $range (i32.add (local.get $lo) (local.get $n)) (i32.add (local.get $hi) (local.get $n))))'''
        if mode=='shared':
            calc=f'''(if (i32.lt_u (local.get $n) (i32.sub (local.get $hi) (local.get $lo)))
              (then
               (local.set $common (call $range (i32.add (local.get $lo) (local.get $n)) (local.get $hi)))
               (local.set $c0 (i32.xor (local.get $common) (call $range (local.get $lo) (i32.add (local.get $lo) (local.get $n)))))
               (local.set $c1 (i32.xor (local.get $common) (call $range (local.get $hi) (i32.add (local.get $hi) (local.get $n))))))
              (else {calc}))'''
        body=f'''(if (i32.or (i32.eqz (local.get $n)) (i32.eq (local.get $d) (local.get $s))) (then (return)))
          (local.set $lo (select (local.get $d) (local.get $s) (i32.lt_u (local.get $d) (local.get $s))))
          (local.set $hi (select (local.get $d) (local.get $s) (i32.gt_u (local.get $d) (local.get $s))))
          (if (i32.eq (i32.add (local.get $d) (local.get $n)) (i32.const {n}))
            (then (local.set $c0 (call $range (local.get $lo) (local.get $hi))))
            (else {calc}))
          {cp}
          (i32.store8 (local.get $d) (i32.xor (i32.load8_u (local.get $d)) (local.get $c0)))
          (if (i32.lt_u (i32.add (local.get $d) (local.get $n)) (i32.const {n}))
            (then (i32.store8 (i32.add (local.get $d) (local.get $n))
              (i32.xor (i32.load8_u (i32.add (local.get $d) (local.get $n))) (local.get $c1)))))'''
    datawat=''.join('\\%02x'%x for x in data)
    return f'''(module (memory 1 1) {helper}
      (func $copy (export "copy") (param $d i32) (param $s i32) (param $n i32) {locals}
        {bounds} {body}) {digest(mode,n)}
      (data (i32.const 0) "{datawat}"))'''

def sections(data):
    if data[:8] != b'\0asm\1\0\0\0': raise ValueError('Not a core module')
    pos=8; result={}
    def leb():
        nonlocal pos
        v=shift=0
        while True:
            b=data[pos];pos+=1;v|=(b&127)<<shift
            if not b&128:return v
            shift+=7
            if shift>35:raise ValueError('LEB overflow')
    while pos<len(data):
        tag=data[pos];pos+=1;length=leb();end=pos+length
        if end>len(data) or tag in result:raise ValueError('Unexpected/duplicate section')
        if tag:result[tag]=data[pos:end]
        pos=end
    return result

def unquote(s):
    s=s[1:-1];out=bytearray();i=0
    while i<len(s):
        if s[i]!='\\':out.append(ord(s[i]));i+=1
        elif i+2<len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+1:i+3]):out.append(int(s[i+1:i+3],16));i+=3
        else:out.append({'n':10,'r':13,'t':9,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
    return out

def read_data(path):
    w.tool('wasm-validate',[path])
    mod=w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))
    if any(q[0] not in {'type','memory','func','export','data'} for q in mod[1:]):raise ValueError('Unsupported module sections')
    if [q for q in mod[1:] if q[0]=='memory'] != [['memory','1','1']]:raise ValueError('Private fixed memory32 required')
    if any(q[0]=='export' and q[2][0]!='func' for q in mod[1:]):raise ValueError('No memory/table export allowed')
    data=bytearray(65536);end=0
    for q in mod[1:]:
        if q[0]=='data':
            if not isinstance(q[1],list) or q[1][0]!='i32.const':raise ValueError('Active constant data required')
            off=int(q[1][1]);bs=b''.join(unquote(s) for s in q[2:])
            if off<0 or off+len(bs)>65536:raise ValueError('Data out of memory')
            data[off:off+len(bs)]=bs;end=max(end,off+len(bs))
    if not end:raise ValueError('Nonempty initial data required')
    return bytes(data[:end])

def profile(path, scratch, modes):
    """Strict public-template verification, not a general semantic recognizer."""
    start=time.perf_counter();bs=read_data(path);actual=sections(path.read_bytes());actual.pop(11,None)
    scratch.mkdir(parents=True,exist_ok=False)
    for mode in modes:
        raw=scratch/(mode+'.raw.wasm');c.compile_wat(wat(bs,mode),raw)
        for level in ('raw','O3'):
            trial=raw if level=='raw' else scratch/(mode+'.O3.wasm')
            if level=='O3':w.tool('wasm-opt',[raw,'-O3','--all-features','-o',trial])
            check=sections(trial.read_bytes());check.pop(11,None)
            if check==actual:return bs,mode,level,(time.perf_counter()-start)*1000
    raise ValueError('No supported copy/digest profile matched')

def transform(src,out,mode):
    start=time.perf_counter()
    bs,_,level,ms=profile(src,out.with_suffix('.profile'),('plain',))
    c.compile_wat(wat(encode(bs,mode),mode),out)
    return dict(mode=mode,n=len(bs),source_opt=level,profile_ms=ms,transform_ms=(time.perf_counter()-start)*1000)

def recover(src,out):
    bs,mode,level,ms=profile(src,out.with_suffix('.profile'),MODES)
    start=time.perf_counter();plain=decode(bs,mode);elapsed=(time.perf_counter()-start)*1000
    c.compile_wat(wat(plain,'plain'),out)
    return dict(status='recovered',mode=mode,opt=level,n=len(bs),profile_ms=ms,decode_ms=elapsed,logical_data_sha256=hashlib.sha256(plain).hexdigest())

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=MODES,default='shared');ap.add_argument('--recover',action='store_true');o=ap.parse_args()
    print(json.dumps(recover(o.input,o.output) if o.recover else transform(o.input,o.output,o.mode)))
