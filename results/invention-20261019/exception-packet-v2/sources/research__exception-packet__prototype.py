"""Exception-reference transport experiment; no secrecy or novelty claim."""
import argparse, hashlib, importlib.util, json, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('packet_common',ROOT/'research/connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
s=importlib.util.spec_from_file_location('packet_flat',ROOT/'research/stack-cycle/transform.py')
sf=importlib.util.module_from_spec(s);s.loader.exec_module(sf)
OPS2=set('add sub mul and or xor shl shr_u shr_s rotl rotr eq ne lt_u le_u gt_u ge_u lt_s le_s gt_s ge_s'.split())
OPS1=set('eqz clz ctz popcnt'.split())
MODES=('plain','helper','fresh','shared')
class Node(tuple):
    def __new__(cls,items):
        obj=super().__new__(cls,items);obj.cached_hash=hash(tuple(items));return obj
    def __hash__(self):return self.cached_hash
POOL={}
def node(*xs):
    key=tuple(xs)
    if key not in POOL:POOL[key]=Node(xs)
    return POOL[key]
def const(v):return node('i32.const',int(v)&0xffffffff)
def expr(op,*a):
    if op=='select':
        x,y,c=a
        if x==y:return x
        if c[0]=='i32.const':return x if c[1] else y
        if c[0]=='i32.eqz':return expr('select',y,x,c[1])
        # A boolean normalization is irrelevant to select truth.
        if c[0]=='i32.ne' and c[2]==const(0):return expr('select',x,y,c[1])
    if op=='i32.eqz' and a[0][0]=='i32.const':return const(not a[0][1])
    if op=='i32.eqz' and a[0][0]=='i32.eqz':return truth(a[0][1])
    if op=='i32.eqz' and a[0][0]=='i32.ne' and a[0][2]==const(0):return expr('i32.eqz',a[0][1])
    if op=='i32.ne' and a[1]==const(0):return truth(a[0])
    return node(op,*a)
def truth(x):
    if x[0]=='i32.const':return const(bool(x[1]))
    if x[0] in ('i32.eqz','i32.eq','i32.ne','i32.lt_u','i32.lt_s','i32.le_u','i32.le_s','i32.gt_u','i32.gt_s','i32.ge_u','i32.ge_s','tagis'):return x
    return node('i32.ne',x,const(0))
def walk(t,seen=None):
    if seen is None:seen=set()
    if t in seen:return
    seen.add(t)
    yield t
    for x in t[1:]:
        if isinstance(x,tuple):yield from walk(x,seen)
def compile(text,dst):
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.with_suffix('.wat').write_text(text,encoding='utf-8')
    w.tool('wat2wasm',[dst.with_suffix('.wat'),'--enable-all','-o',dst])
    w.tool('wasm-validate',[dst,'--enable-all'])
def read(src):
    w.tool('wasm-validate',[src,'--enable-all'])
    m=w.parse(w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names','--enable-all']))
    if any(x[0] not in ('type','func','export') for x in m[1:]):raise ValueError('No imports/memory/global/table/tag accepted')
    fs=[x for x in m[1:] if x[0]=='func'];es=[x for x in m[1:] if x[0]=='export']
    if len(fs)!=1 or len(es)!=1 or es[0][2]!=['func','0']:raise ValueError('One function/export required')
    f=fs[0];ps=[p for x in f[1:] if isinstance(x,list) and x[0]=='param' for p in x[1:]]
    ls=[p for x in f[1:] if isinstance(x,list) and x[0]=='local' for p in x[1:]]
    if not 1<=len(ps)<=16 or any(x!='i32' for x in ps+ls) or len(ls)>128:raise ValueError('i32 profile exceeded')
    if [x for x in f[1:] if isinstance(x,list) and x[0]=='result']!=[['result','i32']]:raise ValueError('i32 result required')
    body=[x for x in f[1:] if not isinstance(x,list) or x[0] not in ('type','param','local','result')]
    flat=[i for b in body for i in sf.flat(b)]
    if len(flat)>4096:raise ValueError('Instruction budget exceeded')
    env=[('arg',i) for i in range(len(ps))]+[const(0)]*len(ls);stack=[]
    for ins in flat:
        op=ins[0]
        if op=='i32.const':stack.append(const(ins[1]))
        elif op=='local.get':stack.append(env[int(ins[1])])
        elif op in ('local.set','local.tee'):
            env[int(ins[1])]=stack.pop()
            if op=='local.tee':stack.append(env[int(ins[1])])
        elif op=='drop':stack.pop()
        elif op=='nop':pass
        else:
            arity=3 if op=='select' else 2 if op[4:] in OPS2 and op.startswith('i32.') else 1 if op[4:] in OPS1 and op.startswith('i32.') else -1
            if arity<0 or len(stack)<arity:raise ValueError('Unsupported instruction: '+str(ins))
            a=stack[-arity:];del stack[-arity:];stack.append(expr(op,*a))
    if len(stack)!=1:raise ValueError('Wrong result count')
    return len(ps),es[0][1],stack[0]
CAPTURE='''(func $capture (param $c i32) (result exnref)
 (block $caught (result exnref)
  (try_table (catch_all_ref $caught)
   (if (local.get $c) (then (throw $t)) (else (throw $f))))
  (unreachable)))'''
def force(reverse):
    t,f=('$f','$t') if reverse else ('$t','$f')
    return f'''(func $force{int(reverse)} (param $p exnref) (param $a i32) (param $b i32) (result i32)
 (block $false (block $true
  (try_table (catch {t} $true) (catch {f} $false) (throw_ref (local.get $p))) (unreachable))
  (return (local.get $a))) (local.get $b))'''
def wat(n,name,root,mode):
    decl=[];code=[];memo={};packets={};selects=0;captures=0
    def emit(t):
        nonlocal selects,captures
        if t in memo:return memo[t]
        if t[0]=='arg':return f'(local.get {t[1]})'
        if t[0]=='i32.const':return f'(i32.const {t[1]})'
        args=[emit(x) for x in t[1:]];v=f'$v{len(decl)}';decl.append(f'(local {v} i32)')
        if t[0]=='select':
            selects+=1;a,b,c=args
            if mode in ('fresh','shared'):
                key=t[3] if mode=='shared' else ('use',selects)
                if key not in packets:
                    p=f'$p{captures}';captures+=1;packets[key]=p;decl.append(f'(local {p} exnref)')
                    code.append(f'(local.set {p} (call $capture {c}))')
                rev=selects%2
                if rev:a,b=b,a
                value=f'(call $force{rev} (local.get {packets[key]}) {a} {b})'
            elif mode=='helper':value=f'(call $choose {a} {b} {c})'
            else:value=f'(select {a} {b} {c})'
        else:value=f'({t[0]} {" ".join(args)})'
        code.append(f'(local.set {v} {value})');memo[t]=f'(local.get {v})';return memo[t]
    output=emit(root)
    helpers=''
    if mode in ('fresh','shared'):helpers='(tag $t) (tag $f)'+CAPTURE+force(False)+force(True)
    if mode=='helper':helpers='(func $choose (param i32 i32 i32) (result i32) (select (local.get 0) (local.get 1) (local.get 2)))'
    text=f'(module {helpers} (func $run (export {name}) (param {" ".join(["i32"]*n)}) (result i32) {" ".join(decl)} {" ".join(code)} {output}))'
    return text,dict(selects=selects,captures=captures,scalar_temporaries=len(memo),linear_memory_bytes=0)
def transform(src,dst,mode):
    t=time.perf_counter();n,name,r=read(src);text,info=wat(n,name,r,mode);compile(text,dst)
    return dict(info,mode=mode,elapsed_ms=(time.perf_counter()-t)*1000,bytes=Path(dst).stat().st_size)
def optimize(src,dst):
    # Enable only required features. --all-features adds non-null block types
    # that WABT 1.0.42 cannot read; this issue is recorded, never protection.
    w.tool('wasm-opt',[src,'--enable-exception-handling','--enable-reference-types','-O3','-o',dst])
    w.tool('wasm-validate',[dst,'--enable-all'])
def binaryen_tree(src):
    return w.parse(w.tool('wasm-opt',[src,'--all-features','--print','-o','NUL']))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--mode',choices=MODES,default='shared');a=p.parse_args()
    print(json.dumps(transform(a.input,a.output,a.mode)))
