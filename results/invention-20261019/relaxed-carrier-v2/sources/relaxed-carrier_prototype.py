"""Restricted experimental Wasm carrier; not a security or novelty claim."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('common_wasm',HERE.parent/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
U32=(1<<32)-1
U128=(1<<128)-1

def num(s):
    return int(s,16) if s.lower().lstrip('-').startswith('0x') else int(s)
def c(n):return ['i32.const',str(n & U32)]
def get(n):return ['local.get',str(n)]
def op(name,*xs):return [name,*xs]
def compile_wat(text,path):
    path=Path(path)
    if path.exists() or path.with_suffix('.wat').exists():raise FileExistsError(path)
    path.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[path.with_suffix('.wat'),'-o',path])
    w.tool('wasm-validate',[path])
def read(path):
    w.tool('wasm-validate',[path])
    return w.parse(w.tool('wasm2wat',[path,'--fold-exprs']))
def function(mod):
    if any(x[0] not in ('type','func','export') for x in mod[1:]):raise ValueError('Unsupported module effect or declaration')
    fs=[x for x in mod[1:] if x[0]=='func'];es=[x for x in mod[1:] if x[0]=='export']
    if len(fs)!=1 or es!=[['export','"run"',['func','0']]]:raise ValueError('Expected one exported run')
    f=fs[0]
    ps=[p for x in f[1:] if isinstance(x,list) and x[0]=='param' for p in x[1:]]
    ls=[p for x in f[1:] if isinstance(x,list) and x[0]=='local' for p in x[1:]]
    if ps!=['i32']*3 or [x for x in f[1:] if isinstance(x,list) and x[0]=='result']!=[['result','i32']]:raise ValueError('Expected 3 i32 -> i32')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')]
    return f,ls,body
def transform(src,dst,mode):
    start=time.perf_counter();mod=read(src);f,ls,body=function(mod)
    if any(x!='i32' for x in ls):raise ValueError('Only i32 source locals')
    total=3+len(ls);mask=3+total;nextlocal=mask+1
    code=[]
    def put(x):
        nonlocal nextlocal
        n=nextlocal;nextlocal+=1;code.append(['local.set',str(n),x]);return get(n)
    m=get(mask)
    def lower(x):
        name=x[0]
        if name=='local.get' and len(x)==2 and 0<=num(x[1])<total:return get(3+num(x[1]))
        if name=='i32.const' and len(x)==2:return put(op('i32.xor',c(num(x[1])),m))
        if name in ('i32.and','i32.or','i32.xor') and len(x)==3:
            a=lower(x[1]);b=lower(x[2]);v=op(name,a,b)
            return put(op('i32.xor',v,m if name=='i32.xor' else op('i32.and',op('i32.xor',a,b),m)))
        if name in ('i32.rotl','i32.rotr','i32.shl','i32.shr_u') and len(x)==3 and x[2][0]=='i32.const':
            a=lower(x[1]);k=c(num(x[2][1]));return put(op('i32.xor',op('i32.xor',op(name,a,k),op(name,m,k)),m))
        raise ValueError('Unsupported source expression: '+w.emit(x))
    if mode=='relaxed':
        vec=lambda n:['v128.const','i32x4',*([hex(n)]*4)]
        index=op('v128.or',op('v128.and',op('i32x4.splat',get(0)),vec(0x0f0f0f0f)),vec(0x10101010))
        value=['i32x4.extract_lane','0',op('i8x16.relaxed_swizzle',vec(U32),index)]
    elif mode=='dynamic':value=op('i32.xor',get(0),op('i32.rotl',get(1),c(7)))
    elif mode in ('zero','ones','pattern'):value=c({'zero':0,'ones':U32,'pattern':0xff00a55a}[mode])
    else:raise ValueError('Unknown mode')
    code.append(['local.set',str(mask),value])
    for i in range(total):code.append(['local.set',str(3+i),op('i32.xor',get(i) if i<3 else c(0),m)])
    if not body:raise ValueError('Empty function')
    for x in body[:-1]:
        if x[0]!='local.set' or len(x)!=3 or not 0<=num(x[1])<total:raise ValueError('Only sequential local.set statements')
        value=lower(x[2]);code.append(['local.set',str(3+num(x[1])),value])
    result=lower(body[-1]);code.append(op('i32.xor',result,m))
    target=['module',['func',['export','"run"'],['param','i32','i32','i32'],['result','i32'],['local',*(['i32']*(nextlocal-3))],*code]]
    compile_wat(w.emit(target),dst)
    return dict(mode=mode,transform_ms=(time.perf_counter()-start)*1000,declared_i32_locals=nextlocal-3)

# Known bits for the pure straight-line recovery scope. No effectful operands
# may be erased. Unknown bits are never assumed zero.
PURE={'i32.const','local.get','local.set','local.tee','drop','i32.and','i32.or','i32.xor','i32.rotl','i32.rotr','i32.shl','i32.shr_u','i32.shr_s','i32.add','i32.sub','i32.mul','v128.const','v128.and','v128.or','v128.xor','v128.not','i32x4.splat','i32x4.extract_lane','i8x16.swizzle','i8x16.relaxed_swizzle'}
def simplify(mod):
    f,ls,body=function(mod)
    if any(t not in ('i32','v128') for t in ls):raise ValueError('Unsupported local type')
    def check(x):
        if not isinstance(x,list) or x[0] not in PURE:raise ValueError('Outside pure recovery scope: '+str(x))
        for v in x[1:]:
            if isinstance(v,list):check(v)
    for x in body:check(x)
    env={i:(0,0) for i in range(3)}
    for i,t in enumerate(ls,3):env[i]=(0,U128 if t=='v128' else U32)
    found=0
    def visit(x):
        nonlocal found
        n=x[0];new=[n];bits=[]
        for a in x[1:]:
            if isinstance(a,list):z,b=visit(a);new.append(z);bits.append(b)
            else:new.append(a)
        known=(0,0)
        if n=='i32.const':v=num(x[1])&U32;known=(v,U32^v)
        elif n=='v128.const':
            widths={'i8x16':8,'i16x8':16,'i32x4':32,'i64x2':64}
            if x[1] not in widths:raise ValueError('Integer vector constants only')
            width=widths[x[1]];v=sum((num(a)&((1<<width)-1))<<(width*i) for i,a in enumerate(x[2:]));known=(v,U128^v)
        elif n=='local.get':known=env[num(x[1])]
        elif n in ('local.set','local.tee'):env[num(x[1])]=bits[0];known=bits[0]
        elif n in ('i32.and','v128.and'):known=(bits[0][0]&bits[1][0],bits[0][1]|bits[1][1])
        elif n in ('i32.or','v128.or'):known=(bits[0][0]|bits[1][0],bits[0][1]&bits[1][1])
        elif n in ('i32.xor','v128.xor'):
            a,b=bits;known=((a[0]&b[1])|(a[1]&b[0]),(a[0]&b[0])|(a[1]&b[1]))
        elif n=='v128.not':known=bits[0][::-1]
        elif n=='i32x4.splat':known=tuple(sum((b&U32)<<(32*i) for i in range(4)) for b in bits[0])
        elif n=='i32x4.extract_lane':known=tuple((b>>(32*num(x[1])))&U32 for b in bits[0])
        elif n in ('i8x16.swizzle','i8x16.relaxed_swizzle'):
            if all(((bits[1][0]>>(8*i))&255)>=16 for i in range(16)):
                # A legal strict refinement; equivalent for this mask-independent
                # carrier, not equal to arbitrary relaxed result sets.
                found+=n=='i8x16.relaxed_swizzle';new=['v128.const','i32x4','0','0','0','0'];known=(0,U128)
        return new,known
    fresh=[visit(x)[0] for x in body]
    header=[x for x in f[1:] if isinstance(x,list) and x[0] in ('type','param','result','local')]
    result=['module',*[(['func',*header,*fresh] if x is f else x) for x in mod[1:]]]
    return result,found
def recover(src,dst):
    begin=time.perf_counter();mod=read(src);loaded=time.perf_counter();result,count=simplify(mod);done=time.perf_counter()
    if count!=1:raise ValueError('Expected one range-proven relaxed carrier, found '+str(count))
    intermediate=Path(dst).with_name(Path(dst).stem+'.refinement.wasm');compile_wat(w.emit(result),intermediate)
    w.tool('wasm-opt',[intermediate,'-O3','--all-features','-o',dst]);w.tool('wasm-validate',[dst])
    return dict(proven_swizzles=count,read_ms=(loaded-begin)*1000,simplify_ms=(done-loaded)*1000,total_ms=(time.perf_counter()-begin)*1000)

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
    a=sub.add_parser('transform');a.add_argument('src');a.add_argument('dst');a.add_argument('--mode',default='relaxed',choices=['relaxed','dynamic','zero','ones','pattern'])
    a=sub.add_parser('recover');a.add_argument('src');a.add_argument('dst')
    a=ap.parse_args();print(json.dumps(transform(a.src,a.dst,a.mode) if a.command=='transform' else recover(a.src,a.dst)))
if __name__=='__main__':main()
