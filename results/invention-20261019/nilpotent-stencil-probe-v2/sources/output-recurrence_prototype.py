"""Division-free state elimination, restricted Wasm profile, research only."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import time

spec=importlib.util.spec_from_file_location('common_wasm',Path(__file__).resolve().parents[1]/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
M=0xffffffff
def compile_wat(text,path):
    path=Path(path)
    if path.exists() or path.with_suffix('.wat').exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix('.wat').write_text(text,encoding='utf-8');w.tool('wat2wasm',[path.with_suffix('.wat'),'-o',path]);w.tool('wasm-validate',[path])
def get(i):return f'(local.get {i})'
def c(v):return f'(i32.const {v&M})'
def add(a,b):return f'(i32.add {a} {b})'
def mul(a,b):return f'(i32.mul {a} {b})'
def sub(a,b):return f'(i32.sub {a} {b})'
def ld(offset):return f'(i32.load 1 offset={offset} (i32.const 0))'
def poly(base,x,u):
    # Basis: 1,x,u,x*x,x*u,u*u. Data is operational, not recovery metadata.
    terms=[ld(base),mul(ld(base+4),x),mul(ld(base+8),u),mul(ld(base+12),mul(x,x)),mul(ld(base+16),mul(x,u)),mul(ld(base+20),mul(u,u))]
    result=terms[0]
    for term in terms[1:]:result=add(result,term)
    return result
def words(d,mode):
    if mode=='source':return [d['b'],d['x0'],d['y0'],*d['P'],*d['Q'],*d['R']]
    return [d['x0'],d['w0'],*d['P'],*d['D'],*d['R']]
def quotient(d):return dict(x0=d['x0'],w0=d['b']*d['y0']&M,P=d['P'],D=[d['b']*v&M for v in d['Q']],R=d['R'])
def wat(d,mode):
    blob=struct.pack('<'+'I'*len(words(d,mode)),*words(d,mode));escaped=''.join('\\%02x'%v for v in blob)
    head=f'(module (memory (export "memory") 1 1) (memory 1 1) (data (memory 1) (i32.const 0) "{escaped}") (func (export "run") (param i32 i32) (result i32) (local i32 i32 i32 i32 i32 i32)'
    test='(br_if 1 (i32.ge_u (local.get 2) (local.get 1)))'
    load=f'(i32.load8_u {add(get(0),get(2))})'
    inc=f'(local.set 2 {add(get(2),c(1))})'
    if mode in ('source','quotient'):
        base=12 if mode=='source' else 8
        P=poly(base,get(3),get(5));Q=poly(base+24,get(3),get(5));R=poly(base+48,get(3),get(5))
        yy=mul(ld(0),get(4)) if mode=='source' else get(4)
        initx=ld(4) if mode=='source' else ld(0);inity=ld(8) if mode=='source' else ld(4)
        return head+f'''(local.set 3 {initx})(local.set 4 {inity})
        (block (loop {test}(local.set 5 {load})
        (local.set 6 {add(P,yy)})(local.set 7 {add(Q,mul(R,get(4)))})
        (local.set 3 (local.get 6))(local.set 4 (local.get 7)){inc}(br 0))) (local.get 3)))'''
    if mode!='history':raise ValueError('Unknown profile')
    Pprev=poly(8,get(3),get(5));Pcur=poly(8,get(4),get(6));Dprev=poly(32,get(3),get(5));Rprev=poly(56,get(3),get(5))
    update=add(Pcur,add(Dprev,mul(Rprev,sub(get(4),Pprev))))
    return head+f'''(local.set 3 {ld(0)})(if (i32.eqz (local.get 1)) (then (return (local.get 3))))
      (local.set 5 (i32.load8_u (local.get 0)))(local.set 4 {add(Pprev,ld(4))})(local.set 2 (i32.const 1))
      (block (loop {test}(local.set 6 {load})(local.set 7 {update})
      (local.set 3 (local.get 4))(local.set 4 (local.get 7))(local.set 5 (local.get 6)){inc}(br 0))) (local.get 4)))'''

def uleb(data,pos):
    value=0;shift=0
    while pos<len(data):
        b=data[pos];pos+=1;value|=(b&127)<<shift
        if not b&128:return value,pos
        shift+=7
        if shift>35:raise ValueError('Oversize ULEB')
    raise ValueError('Truncated ULEB')
def payload(path):
    w.tool('wasm-validate',[path]);data=Path(path).read_bytes();pos=8;blobs=[]
    if data[:8]!=b'\0asm\x01\0\0\0':raise ValueError('Not wasm')
    while pos<len(data):
        kind=data[pos];size,at=uleb(data,pos+1);end=at+size
        if end>len(data):raise ValueError('Truncated section')
        if kind==11:
            count,at=uleb(data,at)
            for _ in range(count):
                flags,at=uleb(data,at)
                if flags!=2:raise ValueError('Expected explicit private memory')
                mem,at=uleb(data,at)
                if mem!=1 or data[at:at+3]!=b'\x41\x00\x0b':raise ValueError('Expected private offset zero')
                at+=3;n,at=uleb(data,at);blobs.append(data[at:at+n]);at+=n
            if at!=end:raise ValueError('Trailing data')
        pos=end
    if len(blobs)!=1 or len(blobs[0]) not in (80,84):raise ValueError('Unexpected operational coefficients')
    return list(struct.unpack('<'+'I'*(len(blobs[0])//4),blobs[0]))
def read(path):return w.parse(w.tool('wasm2wat',[path,'--fold-exprs','--no-debug-names']))
def extract(path,parent,mode):
    start=time.perf_counter();v=payload(path)
    if mode=='source':
        if len(v)!=21:raise ValueError('Source needs 21 words')
        d=dict(b=v[0],x0=v[1],y0=v[2],P=v[3:9],Q=v[9:15],R=v[15:21])
    else:
        if len(v)!=20:raise ValueError('Reduced representation needs 20 words')
        d=dict(x0=v[0],w0=v[1],P=v[2:8],D=v[8:14],R=v[14:20])
    mod=read(path);matched=None
    with tempfile.TemporaryDirectory(prefix='profile-',dir=parent) as td:
        raw=Path(td)/'raw.wasm';compile_wat(wat(d,mode),raw)
        for opt in ('raw','O3'):
            candidate=raw
            if opt=='O3':
                candidate=Path(td)/'O3.wasm';w.tool('wasm-opt',[raw,'-O3','--enable-multimemory','-o',candidate])
            if read(candidate)==mod:matched=opt;break
    if matched is None:raise ValueError('Outside the complete verified '+mode+' profile')
    return d,dict(matched=matched,extract_validate_ms=(time.perf_counter()-start)*1000)
def transform(src,dst):
    begin=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    d,stats=extract(src,dst.parent,'source');small=quotient(d);compile_wat(wat(small,'history'),dst)
    return dict(stats,transform_ms=(time.perf_counter()-begin)*1000)
def recover(src,dst):
    begin=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    d,stats=extract(src,dst.parent,'history');compile_wat(wat(d,'quotient'),dst)
    return dict(stats,recovery_ms=(time.perf_counter()-begin)*1000,original_y_recovered=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();print(json.dumps(transform(a.source,a.output) if a.action=='transform' else recover(a.source,a.output)))
if __name__=='__main__':main()
