"""Binary-to-binary contract probe. Does not claim a general obfuscator."""
import argparse,hashlib,importlib.util,json,random,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('copy_packet',ROOT/'research/exception-packet/prototype.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
s=importlib.util.spec_from_file_location('copy_sections',ROOT/'research/difference-boundary/prototype.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
MODES=('plain','uniform','position','coupled')

def rol(x,r):r%=8;return ((x<<r)|(x>>(8-r)))&255
def encode(data,mode):
    if mode=='plain':return bytes(data)
    if mode=='uniform':return bytes(rol((x*5)&255,3) for x in data)
    if mode=='position':return bytes(rol(x,i%8) for i,x in enumerate(data))
    out=bytearray(data)
    for i in range(0,len(out),2):
        if (out[i]^out[i+1])&1:out[i],out[i+1]=out[i+1],out[i]
    return bytes(out)

def wat(data,mode='plain',alignment=1,probe=False):
    if len(data)!=65536 or alignment not in (1,2):raise ValueError('profile')
    load='(i32.load8_u (local.get 0))';locals=''
    if mode=='uniform':
        load='(i32.and (i32.mul (i32.or (i32.shr_u (local.get $v) (i32.const 3)) (i32.shl (local.get $v) (i32.const 5))) (i32.const 205)) (i32.const 255))'
        locals='(local $v i32) (local.set $v (i32.load8_u (local.get 0)))'
    elif mode=='position':
        load='(i32.and (i32.or (i32.shr_u (local.get $v) (local.get $r)) (i32.shl (local.get $v) (i32.sub (i32.const 8) (local.get $r)))) (i32.const 255))'
        locals='(local $v i32) (local $r i32) (local.set $v (i32.load8_u (local.get 0))) (local.set $r (i32.and (local.get 0) (i32.const 7)))'
    elif mode=='coupled':
        # Pair selection is an involution: the condition is invariant under swap.
        locals='''(local $a i32) (local $b i32)
        (local.set $a (i32.load8_u (i32.and (local.get 0) (i32.const -2))))
        (local.set $b (i32.load8_u (i32.or (local.get 0) (i32.const 1))))'''
        load='(select (local.get $b) (local.get $a) (i32.and (i32.xor (local.get 0) (i32.xor (local.get $a) (local.get $b))) (i32.const 1)))'
    cp=' '.join(f'(local.get {i})' if alignment==1 else f'(i32.and (local.get {i}) (i32.const -2))' for i in range(3))
    return f'''(module (memory 1 1) {'(export "memory" (memory 0))' if probe else ''}
     (func (export "copy") (param i32 i32 i32) (memory.copy {cp}))
     (func (export "read") (param i32) (result i32) {locals} {load})
     (data (i32.const 0) "{''.join(chr(92)+format(x,'02x') for x in data)}"))'''

def fingerprint(path):
    sections=b.sections(Path(path).read_bytes())
    return {i:hashlib.sha256(v).hexdigest() for i,v in sections.items() if i not in (0,11)}

def profile(path,folder):
    for alignment in (1,2):
        ref=folder/f'profile-{alignment}.wasm'
        if not ref.exists():p.compile(wat(bytes(65536),'plain',alignment),ref)
        if fingerprint(path)==fingerprint(ref):return alignment
    raise ValueError('Only the canonical private-memory copy/read source profile is accepted')

def data_image(src):
    # The verified source profile has one active data segment at offset 0.
    m=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names','--enable-all']))
    ds=[x for x in m[1:] if isinstance(x,list) and x[0]=='data']
    if len(ds)!=1:raise ValueError('one data segment required')
    d=ds[0]
    # WABT names may include a numeric data segment id.
    off=next(x for x in d[1:] if isinstance(x,list));strings=[x for x in d[1:] if isinstance(x,str) and x.startswith('"')]
    if off!=['i32.const','0']:raise ValueError('zero data offset required')
    raw=bytearray()
    for z in strings:
        i=1
        while i<len(z)-1:
            if z[i]=='\\':
                if z[i+1] in '0123456789abcdefABCDEF' and i+2<len(z) and z[i+2] in '0123456789abcdefABCDEF':raw.append(int(z[i+1:i+3],16));i+=3
                else:
                    raw.append({'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}[z[i+1]]);i+=2
            else:raw.append(ord(z[i]));i+=1
    if len(raw)!=65536:raise ValueError('one full page required')
    return bytes(raw)

def transform(src,dst,mode,allow_invalid=False):
    start=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    alignment=profile(src,dst.parent);data=data_image(src)
    legal=mode in ('plain','uniform') or mode=='coupled' and alignment==2
    if not legal and not allow_invalid:raise ValueError('Rejected: this encoding does not commute with the source copy operations')
    p.compile(wat(encode(data,mode),mode,alignment),dst)
    return dict(mode=mode,alignment=alignment,legal=legal,bytes=dst.stat().st_size,elapsed_ms=(time.perf_counter()-start)*1000)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');a.add_argument('--mode',choices=MODES,default='coupled');a.add_argument('--negative-control',action='store_true');v=a.parse_args()
    print(json.dumps(transform(v.input,v.output,v.mode,v.negative_control)))
