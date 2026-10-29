"""RNC compatibility gate for Wasm word arithmetic; known constructions."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('residue_common',HERE.parent/'isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
MASK=(1<<32)-1
MODULI={'odd':(65537,65539),'repair':(65537,65539),'aligned':(1<<32,65537)}


def wat(e):
    if e[0]=='p':return f'(local.get {e[1]})'
    if e[0]=='c':return f'(i32.const {e[1]})'
    return f'(i32.{e[0]} {wat(e[1])} {wat(e[2])})'


def plain(e):return '(module (func (export "run") (param i32 i32) (result i32) '+wat(e)+'))'


def source(src):
    m=q.read(src)
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise ValueError('pure source module only')
    fs=[x for x in m[1:] if x[0]=='func'];es=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or es!=[['export','"run"',['func','0']]]:raise ValueError('single run required')
    f=fs[0]
    if [x for x in f[1:] if x[0]=='param']!=[['param','i32','i32']]:raise ValueError('two i32 parameters')
    if [x for x in f[1:] if x[0]=='result']!=[['result','i32']]:raise ValueError('one i32 result')
    body=[x for x in f[1:] if x[0] not in ('type','param','result')]
    if len(body)!=1:raise ValueError('expression source only')
    def parse(e):
        if e[0]=='local.get' and len(e)==2 and e[1] in ('0','1'):return ('p',int(e[1]))
        if e[0]=='i32.const' and len(e)==2:return ('c',int(e[1],0)&MASK)
        if e[0] in ('i32.add','i32.sub','i32.mul') and len(e)==3:return (e[0][4:],parse(e[1]),parse(e[2]))
        raise ValueError('unsupported source expression')
    return parse(body[0])


def render(e,mode):
    m0,m1=MODULI[mode];inverse=pow(m0,-1,m1);sets=[];nextlocal=2
    g=lambda i:f'(local.get {i})';c=lambda x:f'(i64.const {x})'
    rem=lambda x,m:f'(i64.rem_u {x} {c(m)})'
    def allocate(expr):
        nonlocal nextlocal
        i=nextlocal;nextlocal+=1;sets.append(f'(local.set {i} {expr})');return i
    def decode(pair):
        a,b=map(g,pair)
        difference=f'(i64.sub (i64.add {b} {c(m1)}) {rem(a,m1)})'
        t=rem(f'(i64.mul {difference} {c(inverse)})',m1)
        return f'(i64.add {a} (i64.mul {c(m0)} {t}))'
    def build(t):
        if t[0] in ('p','c'):
            x=f'(i64.extend_i32_u {wat(t)})'
            return tuple(allocate(rem(x,m)) for m in (m0,m1))
        a,b=build(t[1]),build(t[2]);op=t[0]
        if mode=='repair':
            x=f'(i32.{op} (i32.wrap_i64 {decode(a)}) (i32.wrap_i64 {decode(b)}))'
            temp=allocate(f'(i64.extend_i32_u {x})')
            return tuple(allocate(rem(g(temp),m)) for m in (m0,m1))
        values=[]
        for ai,bi,m in zip(a,b,(m0,m1)):
            left=g(ai) if op!='sub' else f'(i64.add {g(ai)} {c(m)})'
            values.append(allocate(rem(f'(i64.{op} {left} {g(bi)})',m)))
        return tuple(values)
    pair=build(e)
    return '(module (func (export "run") (param i32 i32) (result i32) (local '+ ' '.join(['i64']*(nextlocal-2))+') '+' '.join(sets)+' (i32.wrap_i64 '+decode(pair)+')))' 


def transform(src,dst,mode):
    start=time.perf_counter();e=source(src);q.compile(render(e,mode),dst)
    return dict(mode=mode,ms=(time.perf_counter()-start)*1000,bytes=Path(dst).stat().st_size)


def project(src,dst):
    """Abstract a supported, pure, straight-line binary into Z/(2^32).

    Odd remainders cannot in general be projected: they are deliberately opaque.
    Dead terms are discarded in a domain restricted to total, pure operations.
    """
    start=time.perf_counter();m=q.read(src)
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise ValueError('pure module only')
    fs=[x for x in m[1:] if x[0]=='func'];es=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or es!=[['export','"run"',['func','0']]]:raise ValueError('single function only')
    f=fs[0];body=[x for x in f[1:] if x[0] not in ('type','param','result','local')]
    if [x for x in f[1:] if x[0]=='param']!=[['param','i32','i32']]:raise ValueError('two i32 parameters')
    if [x for x in f[1:] if x[0]=='result']!=[['result','i32']]:raise ValueError('one i32 result')
    # Reject effects and possible traps even when a ring projection would erase
    # their value. Only constant nonzero unsigned remainders are opaque atoms.
    allowed={'local.get','local.set','local.tee','i32.const','i64.const','i32.wrap_i64',
             'i64.extend_i32_u','i64.extend_i32_s','i32.add','i32.sub','i32.mul',
             'i64.add','i64.sub','i64.mul','i64.rem_u','i64.and','i64.shl'}
    for root in body:
        for node in q.walk(root):
            if node[0] not in allowed:raise ValueError('unsupported or potentially effectful instruction')
            if node[0]=='i64.rem_u' and not (len(node)==3 and node[2][0]=='i64.const' and int(node[2][1],0)%2**64):
                raise ValueError('remainder may trap')
            if node[0]=='i64.shl' and node[2][0]!='i64.const':raise ValueError('dynamic i64 shift unsupported')
    locals_={0:('p',0),1:('p',1)}
    count=sum(len(x)-1 for x in f[1:] if x[0]=='local')
    locals_.update({i:('c',0) for i in range(2,2+count)})
    def ring(e):
        if isinstance(e,tuple):return e
        op=e[0]
        if op=='local.get':return locals_[int(e[1])]
        if op=='local.tee':
            value=ring(e[2]);locals_[int(e[1])]=value;return value
        if op in ('i32.const','i64.const'):return ('c',int(e[1],0)&MASK)
        if op in ('i32.wrap_i64','i64.extend_i32_u','i64.extend_i32_s'):return ring(e[1])
        if op in ('i64.add','i32.add','i64.sub','i32.sub','i64.mul','i32.mul'):
            a,b=ring(e[1]),ring(e[2]);name=op[4:]
            if name=='mul' and (a==('c',0) or b==('c',0)):return ('c',0)
            if a[0]==b[0]=='c':return ('c',{'add':lambda:a[1]+b[1],'sub':lambda:a[1]-b[1],'mul':lambda:a[1]*b[1]}[name]()&MASK)
            if b==('c',0) and name in ('add','sub'):return a
            if a==('c',0) and name=='add':return b
            return (name,a,b)
        if op=='i64.rem_u' and e[2]==['i64.const','4294967296']:return ring(e[1])
        if op=='i64.rem_u':
            # Even a projected-away remainder may contain local.tee definitions
            # consumed later. Traverse its operand in Wasm evaluation order.
            value=ring(e[1]);return ('opaque',repr(('rem',value,int(e[2][1],0))))
        if op=='i64.and':
            a,b=ring(e[1]),ring(e[2])
            if a==('c',MASK):return b
            if b==('c',MASK):return a
            if a==('c',0) or b==('c',0):return ('c',0)
        if op=='i64.shl':
            shift=int(e[2][1],0)&63
            value=ring(e[1])
            if shift>=32:return ('c',0)
            return value if shift==0 else ('mul',value,('c',1<<shift))
        raise ValueError('unsupported projection operation: '+op)
    # i64 locals are interpreted only modulo 2^32; this is sound for the permitted
    # ring operations and a remainder by 2^32, not for arbitrary remainder nodes.
    result=None
    for e in body:
        if e[0]=='local.set':locals_[int(e[1])]=ring(e[2])
        else:
            if result is not None:raise ValueError('multiple results/effects')
            result=ring(e)
    def clean(e):return e[0]!='opaque' and (len(e)==2 or clean(e[1]) and clean(e[2]))
    if result is None or not clean(result):raise ValueError('projection contains unsupported operations')
    q.compile(plain(result),dst)
    return dict(ms=(time.perf_counter()-start)*1000,expression=result)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['transform','project']);a.add_argument('source');a.add_argument('output');a.add_argument('--mode',choices=list(MODULI),default='odd');v=a.parse_args()
    print(json.dumps(transform(v.source,v.output,v.mode) if v.command=='transform' else project(v.source,v.output)))
