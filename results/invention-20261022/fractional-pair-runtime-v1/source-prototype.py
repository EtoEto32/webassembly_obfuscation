"""Experimental unsigned div/rem fusion. No novelty or security claim."""
import argparse, copy, importlib.util, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('fp_tools', ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
MASK=(1<<32)-1
def c(n,w=32):return [f'i{w}.const',str(n)]
def get(i):return ['local.get',str(i)]
def ext(x):return ['i64.extend_i32_u',x]
def wrap(x):return ['i32.wrap_i64',x]
def op(n,a,b):return [n,a,b]
def pack(a,b):return op('i64.or',op('i64.shl',ext(a),c(32,64)),ext(b))
def native(x,d):return pack(op('i32.div_u',x,d),op('i32.rem_u',x,d))
def noise(x,d):return op('i32.rotl',op('i32.xor',x,d),c(13))
def bound(d,bad=False):
    neg=op('i32.sub',c(0),d)
    return op('i32.sub',op('i32.add',neg,op('i32.and',d,neg)),c(0 if bad else 1))
def numerator(x,d,mode):
    t=c(0) if mode=='zero' else bound(d,True) if mode=='bad' else op('i32.and',bound(d),noise(x,d))
    return op('i64.or',op('i64.shl',ext(x),c(32,64)),ext(t))
def decode(z,d):
    frac=op('i64.and',z,c(MASK,64))
    rem=op('i64.shr_u',op('i64.add',op('i64.mul',ext(d),frac),ext(op('i32.sub',d,c(1)))),c(32,64))
    return op('i64.or',op('i64.and',z,c(-1<<32,64)),rem)
def physical(x,d,mode,i):
    z=get(i)
    if mode=='qsub':
        return ['block',['result','i64'],['local.set',str(i),ext(op('i32.div_u',x,d))],pack(wrap(z),op('i32.sub',x,op('i32.mul',d,wrap(z))))]
    return ['block',['result','i64'],['local.set',str(i),op('i64.div_u',numerator(x,d,mode),ext(d))],decode(z,d)]

def norm(e):
    """Canonicalize only exact modular associative/commutative identities."""
    if not isinstance(e,list):return str(e)
    op0=e[0]
    if op0=='local.tee':return ('local.get',e[1])
    if op0 in ('i32.const','i64.const'):
        w=int(op0[1:3]);return (op0,int(e[1],0)&((1<<w)-1))
    if op0 in ('i32.sub','i64.sub'):
        w=int(op0[1:3]);return norm([f'i{w}.add',e[1],[f'i{w}.mul',c(-1,w),e[2]]])
    xs=[norm(x) for x in e[1:]]
    if op0=='i64.extend_i32_u' and xs[0][0]=='i32.const':return ('i64.const',xs[0][1])
    if op0 in ('i32.add','i64.add','i32.mul','i64.mul','i32.or','i64.or','i32.and','i64.and','i32.xor','i64.xor'):
        flat=[]
        for x in xs:
            flat.extend(x[1:] if isinstance(x,tuple) and x[0]==op0 else [x])
        w=int(op0[1:3]);m=(1<<w)-1;cn=f'i{w}.const';vals=[x[1] for x in flat if isinstance(x,tuple) and x[0]==cn];other=[x for x in flat if not(isinstance(x,tuple) and x[0]==cn)]
        if vals:
            v=1 if op0.endswith('.mul') else m if op0.endswith('.and') else 0
            for x in vals:
                if op0.endswith('.add'):v=(v+x)&m
                elif op0.endswith('.mul'):v=(v*x)&m
                elif op0.endswith('.or'):v|=x
                elif op0.endswith('.and'):v&=x
                else:v^=x
            identity=1 if op0.endswith('.mul') else m if op0.endswith('.and') else 0
            if v!=identity or not other:other.append((cn,v))
        if len(other)==1:return other[0]
        return (op0,*sorted(other,key=repr))
    return (op0,*xs)

ALLOWED={'module','func','type','param','result','local','export','block','loop','if','then','else','br','br_if','return','drop','call','select','nop','unreachable','local.get','local.set','local.tee'}
ALLOWED.update('i'+str(w)+'.'+s for w in (32,64) for s in ('const','add','sub','mul','and','or','xor','shl','shr_u','rotl','eqz','eq','ne','lt_u','le_u','gt_u','ge_u','div_u','rem_u'))
ALLOWED.update(('i64.extend_i32_u','i32.wrap_i64'))
def profile(m):
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise ValueError('pure scalar module: no memory/import/global/table/start')
    if not any(x[0]=='func' for x in m[1:]):raise ValueError('no functions')
    for e in q.walk(m):
        if e[0] not in ALLOWED:raise ValueError('unsupported operation '+str(e[0]))
        if e[0] in ('param','result','local') and any(t not in ('i32','i64') for t in e[1:]):raise ValueError('integer types only')
def leaf(e):return isinstance(e,list) and len(e)==2 and e[0] in ('local.get','i32.const')
def source_pair(e):
    if not isinstance(e,list) or e[:1]!=['i64.or']:return None
    if any(v[0] in ('local.tee','local.set','call','block','loop','if') for v in q.walk(e)):return None
    for div in q.walk(e):
        if div[:1]!=['i32.div_u'] or len(div)!=3 or not all(leaf(v) for v in div[1:]):continue
        x,d=div[1:]
        if norm(e)==norm(native(x,d)):return x,d
    return None
def transform(src,dst,mode='fraction'):
    if mode not in ('plain','qsub','zero','fraction','bad'):raise ValueError(mode)
    t0=time.perf_counter();m=q.read(src);profile(m);t1=time.perf_counter();count=0
    for f in [x for x in m[1:] if x[0]=='func']:
        n=sum(len(e)-1 for e in f[1:] if isinstance(e,list) and e[0] in ('param','local'))
        extra=[]
        def visit(e):
            nonlocal count
            pair=source_pair(e)
            if pair:
                count+=1
                if mode=='plain':return e
                i=n+len(extra);extra.append('i64');return physical(*pair,mode,i)
            return [visit(x) if isinstance(x,list) else x for x in e] if isinstance(e,list) else e
        body=[visit(e) if isinstance(e,list) and e[0] not in ('type','param','result','local') else e for e in f[1:]]
        if extra:
            pos=0
            while pos<len(body) and isinstance(body[pos],list) and body[pos][0] in ('type','param','result','local'):pos+=1
            body.insert(pos,['local',*extra])
        f[:]=['func',*body]
    if not count:raise ValueError('no supported paired unsigned div/rem')
    t2=time.perf_counter();q.compile(q.w.emit(m),dst);t3=time.perf_counter()
    return dict(pairs=count,read_ms=(t1-t0)*1000,build_ms=(t2-t1)*1000,compile_ms=(t3-t2)*1000,total_ms=(t3-t0)*1000)

def identify(div):
    if not isinstance(div,list) or div[:1]!=['i64.div_u'] or len(div)!=3:return None
    den=div[2]
    if den[:1]!=['i64.extend_i32_u'] or not leaf(den[1]):return None
    d=den[1]
    for sh in q.walk(div[1]):
        if sh[:1]!=['i64.shl'] or norm(sh[2])!=norm(c(32,64)) or sh[1][:1]!=['i64.extend_i32_u'] or not leaf(sh[1][1]):continue
        x=sh[1][1]
        for mode in ('zero','fraction'):
            if norm(div[1])==norm(numerator(x,d,mode)):return x,d,mode
    return None
def recover(src,dst):
    """Known-family rewrite; refuses escaping packets or unmatched code."""
    t0=time.perf_counter();m=q.read(src);profile(m);t1=time.perf_counter();found=[]
    for f in [x for x in m[1:] if x[0]=='func']:
        parents={id(v):e for e in q.walk(f) for v in e[1:] if isinstance(v,list)}
        expression_replacements={}
        def expand(e,env,writes):
            if not isinstance(e,list):return e
            if e[0]=='local.get':return copy.deepcopy(env.get(e[1],e))
            if e[0] in ('local.set','local.tee'):
                value=expand(e[2],env,writes);env[e[1]]=value;writes.add(e[1]);return value
            if e[0]=='block' and e[1:2]==[['result','i64']] and len(e)==4 and e[2][0]=='local.set':
                expand(e[2],env,writes);return expand(e[3],env,writes)
            if e[0].startswith(('i32.','i64.')):return [e[0],*[expand(v,env,writes) if isinstance(v,list) else v for v in e[1:]]]
            raise ValueError('not a closed arithmetic expression')
        for e in q.walk(f):
            if e[0] not in ('i64.or','block'):continue
            env={};writes=set()
            try:value=expand(e,env,writes)
            except ValueError:continue
            for div in q.walk(value):
                info=identify(div)
                if not info:continue
                x,d,mode=info
                if norm(value)!=norm(decode(div,d)):continue
                inside={id(v) for v in q.walk(e)};parent=parents.get(id(e));safe=True
                for i in writes:
                    external=[v for v in q.walk(f) if v[0]=='local.get' and v[1]==i and id(v) not in inside]
                    overwritten=parent is not None and parent[:2] in (['local.tee',i],['local.set',i]) and parent[2] is e
                    if external and not overwritten:safe=False
                if safe:
                    expression_replacements[id(e)]=native(x,d);found.append(dict(mode=mode,proof='closed expression with nonescaping or immediately overwritten temporaries'));break
        def replace_expression(e):
            if id(e) in expression_replacements:return expression_replacements[id(e)]
            return [replace_expression(v) if isinstance(v,list) else v for v in e] if isinstance(e,list) else e
        f[:]=replace_expression(f)
        definitions={}
        for e in q.walk(f):
            if e[0] in ('local.set','local.tee'):definitions.setdefault(e[1],[]).append(e)
        repl={}
        for i,defs in definitions.items():
            if len(defs)!=1:continue
            definition=defs[0];info=identify(definition[2])
            if not info:continue
            x,d,mode=info;expected=norm(decode(get(i),d))
            for e in q.walk(f):
                target=None
                # Raw compiler-generated block: no intervening side effects.
                if e[:2]==['block',['result','i64']] and len(e)==4 and e[2] is definition and norm(e[3])==expected:target=e
                # O3 often sinks the definition into the first use.
                elif norm(e)==expected and any(v is definition for v in q.walk(e)) and definition[0]=='local.tee':target=e
                if target is None:continue
                inside={id(v) for v in q.walk(target)}
                uses=[v for v in q.walk(f) if v[0]=='local.get' and v[1]==i]
                if any(id(v) not in inside for v in uses):continue
                repl[id(target)]=native(x,d);found.append(dict(local=i,mode=mode));break
        def visit(e):
            if id(e) in repl:return repl[id(e)]
            return [visit(x) if isinstance(x,list) else x for x in e] if isinstance(e,list) else e
        f[:]=visit(f)
    if not found:raise ValueError('no certified nonescaping fractional packet')
    t2=time.perf_counter();q.compile(q.w.emit(m),dst);t3=time.perf_counter()
    return dict(rewrites=found,read_ms=(t1-t0)*1000,rewrite_ms=(t2-t1)*1000,compile_ms=(t3-t2)*1000)

def fixture(name):
    pair=q.w.emit(native(get(0),get(1)))
    if name=='pair':return f'(module (func (export "run") (param i32 i32) (result i64) {pair}))'
    if name=='chain':
        body=f'''(local.set 2 {pair})
        (local.set 4 (i32.add (i32.mul (local.get 4) (i32.const 33)) (i32.wrap_i64 (i64.shr_u (local.get 2) (i64.const 32)))))
        (local.set 0 (i32.xor (i32.rotl (local.get 0) (i32.const 7)) (i32.wrap_i64 (local.get 2))))
        (local.set 1 (i32.or (i32.add (local.get 1) (local.get 4)) (i32.const 1)))'''
        cond='(i32.ge_u (local.get 3) (i32.const 16))'
    elif name=='euclid':
        body=f'''(local.set 2 {pair})
        (local.set 4 (i32.add (i32.mul (local.get 4) (i32.const 33)) (i32.wrap_i64 (i64.shr_u (local.get 2) (i64.const 32)))))
        (local.set 0 (local.get 1)) (local.set 1 (i32.wrap_i64 (local.get 2)))'''
        cond='(i32.or (i32.eqz (local.get 1)) (i32.ge_u (local.get 3) (i32.const 64)))'
    else:raise ValueError(name)
    return f'''(module (func (export "run") (param i32 i32) (result i64) (local i64 i32 i32)
    (block (loop (br_if 1 {cond}) {body} (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0)))
    {q.w.emit(pack(get(0),get(4)))}))'''

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('src');ap.add_argument('dst');ap.add_argument('--mode',default='fraction');a=ap.parse_args()
    print(transform(a.src,a.dst,a.mode) if a.action=='transform' else recover(a.src,a.dst))
