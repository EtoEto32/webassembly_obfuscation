"""Restricted scalar-memory lowering experiment; no established novelty claim."""
import argparse, copy, importlib.util, re, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('page_common', ROOT/'research/isotope-swizzle/prototype.py')
q = importlib.util.module_from_spec(s); s.loader.exec_module(q)
MASK = 0xffffffff
STEPS = [(0,1,2,5),(1,2,3,11),(2,3,0,17),(3,0,1,23)]
IND = '(v128.const i8x16 '+' '.join(map(str,range(16)))+')'
ZERO = '(v128.const i32x4 0 0 0 0)'

def codec_bytes(data, inverse=False):
    assert len(data)%16 == 0
    out=bytearray()
    for start in range(0,len(data),16):
        v=[int.from_bytes(data[start+4*i:start+4*i+4],'little') for i in range(4)]
        for i,j,k,r in (list(reversed(STEPS)) if inverse else STEPS):
            t=(v[j]+v[k])&MASK
            v[i]^=((t<<r)|(t>>(32-r)))&MASK
        for x in v:out.extend(x.to_bytes(4,'little'))
    return bytes(out)

def codecs():
    out=[]
    for name,seq in [('enc',STEPS),('dec',list(reversed(STEPS)))]:
        body=[]
        for i,j,k,r in seq:
            lane=lambda a:f'(i32x4.extract_lane {a} (local.get $v))'
            rhs=f'(i32.xor {lane(i)} (i32.rotl (i32.add {lane(j)} {lane(k)}) (i32.const {r})))'
            body.append(f'(local.set $v (i32x4.replace_lane {i} (local.get $v) {rhs}))')
        out.append(f'(func ${name} (param $v v128) (result v128) {" ".join(body)} (local.get $v))')
    return '\n'.join(out)

def span(w):
    return f'''(local.set $b (i64.and (local.get $a) (i64.const -16)))
    (local.set $e (i64.and (i64.add (local.get $a) (i64.const {w-1})) (i64.const -16)))
    (local.set $off (i32.and (i32.wrap_i64 (local.get $a)) (i32.const 15)))'''

LOCALS='(local $b i64) (local $e i64) (local $off i32) (local $v0 v128) (local $v1 v128) (local $idx v128)'

def helpers(mode):
    out=[codecs()]
    for w in (1,2,4,8):
        init=f'''{span(w)}
        (local.set $v0 (v128.load (local.get $b)))
        (if (i64.ne (local.get $b) (local.get $e))
          (then (local.set $v1 (v128.load (local.get $e)))))
        (local.set $v0 (call $dec (local.get $v0)))
        (local.set $v1 (call $dec (local.get $v1)))'''
        idx=f'(i8x16.add {IND} (i8x16.splat (local.get $off)))'
        joined=f'''(v128.or (i8x16.swizzle (local.get $v0) (local.get $idx))
          (i8x16.swizzle (local.get $v1) (i8x16.sub (local.get $idx) (i8x16.splat (i32.const 16)))))'''
        value=f'(i64x2.extract_lane 0 {joined})'
        if w<8:value=f'(i64.and {value} (i64.const {(1<<(w*8))-1}))'
        out.append(f'(func $ld{w} (param $a i64) (result i64) {LOCALS} {init} (local.set $idx {idx}) {value})')
        data=f'(i64x2.replace_lane 0 {ZERO} (local.get $x))'
        def patch(vec,idx):
            return f'''(call $enc (v128.bitselect (i8x16.swizzle {data} {idx}) (local.get ${vec})
                     (i8x16.lt_u {idx} (i8x16.splat (i32.const {w})))))'''
        idx0=f'(i8x16.sub {IND} (i8x16.splat (local.get $off)))'
        idx1=f'(i8x16.add {IND} (i8x16.splat (i32.sub (i32.const 16) (local.get $off))))'
        block=f'''{init}
          (v128.store (local.get $b) {patch('v0',idx0)})
          (if (i64.ne (local.get $b) (local.get $e))
            (then (v128.store (local.get $e) {patch('v1',idx1)})))'''
        if mode=='block-high':
            block=f'''{span(w)}
              (if (i64.ne (local.get $b) (local.get $e)) (then
                (local.set $v1 (call $dec (v128.load (local.get $e))))
                (v128.store (local.get $e) {patch('v1',idx1)})))
              (local.set $v0 (call $dec (v128.load (local.get $b))))
              (v128.store (local.get $b) {patch('v0',idx0)})'''
        if mode in ('byte','bad-partial') and w>1:
            check='' if mode=='bad-partial' else f'(drop (v128.load (i64.and (i64.add (local.get $a) (i64.const {w-1})) (i64.const -16))))'
            body=check+'\n'+'\n'.join(f'(call $st1 (i64.add (local.get $a) (i64.const {j})) (i64.shr_u (local.get $x) (i64.const {j*8})))' for j in range(w))
        else:body=block
        out.append(f'(func $st{w} (param $a i64) (param $x i64) {LOCALS} {body})')
    return '\n'.join(out)

def access(op):
    m=re.fullmatch(r'(i32|i64)\.(load|store)(8|16|32)?(?:_([su]))?',op)
    if not m:return None
    t,k,n,sign=m.groups()
    width=int(n)//8 if n else int(t[1:])//8
    return t,k,width,sign

def unescape(text):
    # WABT emits byte strings using ASCII and hex escapes.
    src=text[1:-1];out=bytearray();i=0
    while i<len(src):
        if src[i]!='\\':out.extend(src[i].encode());i+=1
        elif re.match('[0-9a-fA-F]{2}',src[i+1:i+3]):out.append(int(src[i+1:i+3],16));i+=3
        else:out.append({'n':10,'r':13,'t':9,'"':34,"'":39,'\\':92}[src[i+1]]);i+=2
    return bytes(out)

def lower(m,mode):
    m=copy.deepcopy(m)
    if mode not in ('lifted','byte','block','block-high','bad-partial','bad-wrap'):raise q.Unsupported('mode')
    if any(t[0] not in ('type','func','export','memory','data') for t in m[1:]):raise q.Unsupported('module feature')
    mem=[t for t in m[1:] if t[0]=='memory']
    if len(mem)!=1 or len(mem[0])!=3 or not all(isinstance(x,str) and x.isdigit() for x in mem[0][1:]):raise q.Unsupported('fixed memory32 required')
    pages=int(mem[0][1])
    if pages!=int(mem[0][2]) or pages>16:raise q.Unsupported('fixed 0..16 pages profile')
    if any(e[2][0]!='func' for e in m[1:] if e[0]=='export'):raise q.Unsupported('only function exports')
    data=bytearray(pages*65536)
    for seg in [x for x in m[1:] if x[0]=='data']:
        if not(isinstance(seg[1],list) and seg[1][0]=='i32.const') or len(seg)!=3:raise q.Unsupported('constant active data only')
        p=int(seg[1][1])&MASK;raw=unescape(seg[2])
        if p+len(raw)>len(data):raise q.Unsupported('out-of-range data segment')
        data[p:p+len(raw)]=raw
    def rewrite(t):
        if not isinstance(t,list):return t
        op=t[0];a=access(op)
        if a:
            typ,kind,w,sign=a
            args=[rewrite(x) for x in t[1:] if isinstance(x,list)]
            off=0
            for atom in (x for x in t[1:] if not isinstance(x,list)):
                if atom.startswith('offset='):off=int(atom[7:])
                elif not atom.startswith('align='):raise q.Unsupported('memory index')
            if len(args)!=(1 if kind=='load' else 2):raise q.Unsupported('unfolded access')
            ptr=['i64.add',['i64.extend_i32_u',args[0]],['i64.const',str(off)]]
            if mode=='bad-wrap':ptr=['i64.extend_i32_u',['i32.add',args[0],['i32.const',str(off)]]]
            if mode=='lifted':return [op,ptr,*args[1:]]
            if kind=='store':return ['call',f'$st{w}',ptr,(['i64.extend_i32_u',args[1]] if typ=='i32' else args[1])]
            value=['call',f'$ld{w}',ptr]
            if typ=='i32':value=['i32.wrap_i64',value]
            if sign=='s':value=[f'{typ}.extend{w*8}_s',value]
            return value
        if op.startswith(('memory.','v128.','f32.','f64.','ref.','table.')) or 'atomic' in op:raise q.Unsupported('unsupported instruction '+op)
        if op in ('param','result','local') and any(x in ('f32','f64','v128','funcref','externref') for x in t[1:]):raise q.Unsupported('scalar integer profile')
        return [op,*[rewrite(x) for x in t[1:]]]
    out=['module']
    for t in m[1:]:
        if t[0]=='data':continue
        if t[0]=='memory':out.append(['memory','i64',str(pages),str(pages)])
        else:out.append(rewrite(t))
    encoded=bytes(data) if mode=='lifted' else codec_bytes(data)
    end=len(encoded.rstrip(b'\x00'))
    if end:out.append(['data',['i64.const','0'],'"'+''.join('\\%02x'%b for b in encoded[:end])+'"'])
    if mode!='lifted':out.extend(q.w.parse('(module '+helpers(mode)+')')[1:])
    return out

def transform(src,dst,mode):
    t=time.perf_counter();m=q.read(src);r=time.perf_counter();n=lower(m,mode);b=time.perf_counter();q.compile(q.w.emit(n),dst);e=time.perf_counter()
    return dict(mode=mode,read_ms=(r-t)*1000,lower_ms=(b-r)*1000,compile_validate_ms=(e-b)*1000,total_ms=(e-t)*1000)

def probe(src,dst):
    m=q.read(src);m.append(['export','"__physical"',['memory','0']]);q.compile(q.w.emit(m),dst)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--mode',choices=['lifted','byte','block','block-high'],default='block');a=ap.parse_args();print(transform(a.input,a.output,a.mode))
