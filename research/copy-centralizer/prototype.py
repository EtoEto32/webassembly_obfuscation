"""Restricted Wasm constructor for copy-compatible linear memory encodings."""
import argparse,importlib.util,json,random,tempfile,time
from pathlib import Path
import model as m
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('cc_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)

def xor(xs):
    v='(i32.const 0)'
    for x in xs:v=f'(i32.xor {v} {x})'
    return v
def load(i):return f'(i32.load8_u (i32.const {i}))'
def linear(row,local=False):return xor([f'(local.get {i})' if local else load(i) for i in m.bits(row)])
def blob(data):return ''.join('\\'+format(x,'02x') for x in data)
def wat(data,ops,b=None,mode='plain',probe=False):
    n=len(data);b=b or m.ident(n);inv=m.inverse(b)
    if inv is None:raise ValueError('singular encoding')
    if mode not in ('plain','uniform','conjugate','native'):raise ValueError('mode')
    coupled=mode in ('conjugate','native');physical=m.apply(b,data) if coupled else bytes(x^173 for x in data) if mode=='uniform' else data
    read='(i32.load8_u (local.get 0))';write='(i32.store8 (local.get 0) (local.get 1))'
    if coupled:
        read=' '.join(f'(if (i32.eq (local.get 0) (i32.const {i})) (then (return {linear(inv[i])})))' for i in range(n))+' '+read
        branches=[]
        for i in range(n):
            stores=' '.join(f'(i32.store8 (i32.const {j}) (i32.xor {load(j)} (local.get 2)))' for j in range(n) if (b[j]>>i)&1)
            branches.append(f'(if (i32.eq (local.get 0) (i32.const {i})) (then (local.set 2 (i32.xor (local.get 1) {linear(inv[i])})) {stores} (return)))')
        write='(local i32) '+' '.join(branches)+' '+write
    elif mode=='uniform':
        read=f'(i32.xor {read} (select (i32.const 173) (i32.const 0) (i32.lt_u (local.get 0) (i32.const {n}))))'
        write=f'(i32.store8 (local.get 0) (i32.xor (local.get 1) (select (i32.const 173) (i32.const 0) (i32.lt_u (local.get 0) (i32.const {n})))))'
    funcs=[f'(func (export "read") (param i32) (result i32) {read})',f'(func (export "write") (param i32 i32) {write})']
    for j,(d,s,l) in enumerate(ops):
        cp=f'(memory.copy (i32.const {d}) (i32.const {s}) (i32.const {l}))'
        if mode=='conjugate':
            decode=' '.join(f'(local.set {i} {linear(inv[i])})' for i in range(n))+' '+' '.join(f'(i32.store8 (i32.const {i}) (local.get {i}))' for i in range(n))
            encode=' '.join(f'(local.set {i} {load(i)})' for i in range(n))+' '+' '.join(f'(i32.store8 (i32.const {i}) {linear(b[i],True)})' for i in range(n))
            cp=f'(local {" ".join(["i32"]*n)}) {decode} {cp} {encode}'
        funcs.append(f'(func (export "copy{j}") {cp})')
    return '(module (memory 1 1) '+('(export "memory" (memory 0)) ' if probe else '')+' '.join(funcs)+f' (data (i32.const 0) "{blob(physical)}"))'

def data_image(module):
    ds=[x for x in module[1:] if x[0]=='data']
    if len(ds)!=1 or ds[0][1]!=['i32.const','0']:raise ValueError('one active zero-offset segment')
    raw=[]
    for text in ds[0][2:]:
        if not isinstance(text,str) or not text.startswith('"'):raise ValueError('data string')
        i=1
        while i<len(text)-1:
            if text[i]=='\\':
                if text[i+1] in '0123456789abcdefABCDEF' and text[i+2] in '0123456789abcdefABCDEF':raw.append(int(text[i+1:i+3],16));i+=3
                else:raw.append({'t':9,'n':10,'r':13,'"':34,"'":39,'\\':92}[text[i+1]]);i+=2
            else:raw.append(ord(text[i]));i+=1
    return bytes(raw)
def copy_ops(module):
    fs=[x for x in module[1:] if x[0]=='func'];exports={x[1][1:-1]:int(x[2][1]) for x in module[1:] if x[0]=='export' and x[2][0]=='func'}
    names=sorted((k for k in exports if k.startswith('copy')),key=lambda k:int(k[4:]))
    if names!=['copy'+str(j) for j in range(len(names))] or not names:raise ValueError('consecutive copy exports')
    ops=[]
    for name in names:
        body=[e for e in fs[exports[name]][1:] if e[0] not in ('type','param','result','local')]
        if len(body)!=1:raise ValueError('copy function not a single copy operation')
        e=body[0]
        if e[0]=='memory.copy' and len(e)==4:
            if any(x[0]!='i32.const' for x in e[1:]):raise ValueError('constant copy parameters')
            ops.append(tuple(int(x[1],0) for x in e[1:]))
        else:
            sizes={'i32.store8':('i32.load8_u',1),'i32.store16':('i32.load16_u',2),'i32.store':('i32.load',4),'i64.store':('i64.load',8)}
            if e[0] not in sizes:raise ValueError('unsupported lowered copy')
            op,width=sizes[e[0]];args=[x for x in e[1:] if isinstance(x,list)];attrs=[x for x in e[1:] if isinstance(x,str)]
            if len(args)!=2 or args[0][0]!='i32.const' or args[1][0]!=op or any(not a.startswith('align=') for a in attrs):raise ValueError('unsupported copy store')
            loadargs=[x for x in args[1][1:] if isinstance(x,list)];loadattrs=[x for x in args[1][1:] if isinstance(x,str)]
            if len(loadargs)!=1 or loadargs[0][0]!='i32.const' or any(not a.startswith('align=') for a in loadattrs):raise ValueError('unsupported copy load')
            ops.append((int(args[0][1],0),int(loadargs[0][1],0),width))
    return ops
def parse(src):
    module=q.read(src);data=data_image(module);ops=copy_ops(module)
    if not 2<=len(data)<=32:raise ValueError('window 2..32 bytes')
    for op in ops:m.copy_map(len(data),op)
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='cc-profile-') as td:
        f=Path(td)/'reference.wasm';q.compile(wat(data,ops),f)
        if q.read(f)!=module:raise ValueError('exact closed read/write/constant-copy profile required')
    return data,ops
def transform(src,dst,mode,seed=211041):
    t=time.perf_counter();data,ops=parse(src);b,info=m.choose(len(data),ops,seed)
    q.compile(wat(data,ops,b,mode),dst)
    return dict(mode=mode,n=len(data),copies=ops,matrix=b,inverse=m.inverse(b),elapsed_ms=1000*(time.perf_counter()-t),**info)
def probe(src,dst):
    module=q.read(src)
    if any(e[0]=='export' and e[1]=='"memory"' for e in module[1:]):raise ValueError('already exported')
    module.append(['export','"memory"',['memory','0']]);q.compile(q.w.emit(module),dst)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--mode',choices=['uniform','conjugate','native'],default='native');ap.add_argument('--seed',type=int,default=211041);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.seed)))
