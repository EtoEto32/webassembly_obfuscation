"""Finite-state token experiment: canonical source Wasm -> raw GC type groups."""
import argparse,hashlib,importlib.util,json,random,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('type_packet',ROOT/'research/exception-packet/prototype.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
BIN=ROOT/'.tools/binaryen-version_133/bin'
FEATURES=['--mvp-features','--enable-reference-types','--enable-gc']
def tool(name,args):
    r=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(r.stderr)
    return r.stdout
def u(n):
    out=bytearray()
    while True:
        b=n&127;n>>=7;out.append(b|(128 if n else 0))
        if not n:return bytes(out)
def si(n):
    out=bytearray()
    while True:
        b=n&127;n>>=7;done=(n==0 and not b&64) or (n==-1 and b&64)
        out.append(b|(0 if done else 128))
        if done:return bytes(out)
def vec(xs):return u(len(xs))+b''.join(xs)
def section(k,v):return bytes([k])+u(len(v))+v
def name(x):b=x.encode();return u(len(b))+b
def digest(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def save(f,x):Path(f).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def walk(e):
    if isinstance(e,list):
        yield e
        for x in e[1:]:yield from walk(x)

def packed(rows):
    n=len(rows)
    if not 1<=n<=16 or any(len(r)!=3 or any(not 0<=t<n for t in r[:2]) or r[2] not in (0,1) for r in rows):raise ValueError('Invalid DFA')
    a=[sum(row[b]<<(4*i) for i,row in enumerate(rows)) for b in (0,1)]
    a=[v-(1<<64) if v>>63 else v for v in a];final=sum(row[2]<<i for i,row in enumerate(rows))
    # State count is not hidden: a constant result-free marker is checked in source().
    return f'''(module (func (export "run") (param i32 i32) (result i32) (local i32 i32)
     (drop (i32.const {n}))
     (block (loop (br_if 1 (i32.ge_u (local.get 2) (i32.and (local.get 1) (i32.const 31))))
      (local.set 3 (i32.and (i32.wrap_i64 (i64.shr_u
       (select (i64.const {a[1]}) (i64.const {a[0]}) (i32.and (i32.shr_u (local.get 0) (local.get 2)) (i32.const 1)))
       (i64.extend_i32_u (i32.shl (local.get 3) (i32.const 2))))) (i32.const 15)))
      (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0)))
     (i32.and (i32.shr_u (i32.const {final}) (local.get 3)) (i32.const 1))))'''

def source(f,folder):
    def read(f):
        p.w.tool('wasm-validate',[f]);return p.w.parse(p.w.tool('wasm2wat',[f,'--fold-exprs','--no-debug-names']))
    m=read(f);fs=[x for x in m[1:] if x[0]=='func']
    if len(fs)!=1:raise ValueError('One function required')
    drops=[x for x in walk(fs[0]) if x[0]=='drop'];cs=[int(x[1])&((1<<64)-1) for x in walk(fs[0]) if x[0]=='i64.const']
    if len(drops)!=1 or drops[0][1][0]!='i32.const' or len(cs)!=2:raise ValueError('Canonical packed scanner required')
    n=int(drops[0][1][1]);last=fs[0][-1]
    try:final=int(last[1][1][1]);rows=[[(cs[1]>>(4*i))&15,(cs[0]>>(4*i))&15,(final>>i)&1] for i in range(n)]
    except (IndexError,TypeError,ValueError):raise ValueError('Invalid scanner expression')
    with tempfile.TemporaryDirectory(prefix='profile-',dir=folder) as td:
        ref=Path(td)/'source.wasm';p.compile(packed(rows),ref)
        if read(ref)!=m:raise ValueError('Source differs from canonical scanner')
    return rows

def branch(rows):
    step='(unreachable)'
    for i,row in reversed(list(enumerate(rows))):
        step=f'(if (result i32) (i32.eq (local.get 0) (i32.const {i})) (then (select (i32.const {row[1]}) (i32.const {row[0]}) (local.get 1))) (else {step}))'
    acc='(i32.const 0)'
    for i,row in enumerate(rows):
        if row[2]:acc=f'(i32.or {acc} (i32.eq (local.get 0) (i32.const {i})))'
    return f'''(module (func $step (param i32 i32) (result i32) {step}) (func $accept (param i32) (result i32) {acc})
     (func (export "run") (param i32 i32) (result i32) (local i32 i32)
      (block (loop (br_if 1 (i32.ge_u (local.get 2) (i32.and (local.get 1) (i32.const 31))))
       (local.set 3 (call $step (local.get 3) (i32.and (i32.shr_u (local.get 0) (local.get 2)) (i32.const 1))))
       (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) (call $accept (local.get 3))))'''

def gc_binary(rows,groups=1,siblings=0,seed=7,broken=False):
    n=len(rows);width=n+siblings;perm=list(range(width));random.Random(seed).shuffle(perm)
    # Identical rec groups intentionally remain distinct in the raw encoding.
    rec=b'\x4e'+vec([b'\x5f\x00']*width)
    # Negative control changes the last sibling in group 1, breaking all its identities.
    recs=[rec]*groups
    if broken:
        if groups<2 or not siblings:raise ValueError('negative control requires siblings')
        unused=next(i for i in range(width) if i not in perm[:n])
        bodies=[b'\x5f\x00']*width;bodies[unused]=b'\x5f\x01\x7f\x00';recs[1]=b'\x4e'+vec(bodies)
    eq=b'\x6d';i32=b'\x7f'
    ft=[b'\x60'+vec([eq,i32])+vec([eq]),b'\x60'+vec([eq])+vec([i32]),b'\x60'+vec([i32,i32])+vec([i32])]
    types=section(1,vec(recs+ft));base=groups*width
    funcs=section(3,vec([u(base+i) for i in range(3)]))
    allocated=[(i%groups)*width+perm[i] for i in range(n)]
    tests=[((i+1)%groups)*width+perm[i] for i in range(n)]
    globs=section(6,vec([eq+b'\x00\xfb\x01'+u(t)+b'\x0b' for t in allocated]))
    exports=section(7,vec([name('run')+b'\x00\x02']))
    lg=lambda k:b'\x20'+u(k);gg=lambda k:b'\x23'+u(k);c=lambda v:b'\x41'+si(v)
    test=lambda i:lg(0)+b'\xfb\x14'+si(tests[i])
    body=b''
    for i,row in enumerate(rows):
        body+=test(i)+b'\x04\x40'+gg(row[1])+gg(row[0])+lg(1)+b'\x1c\x01\x6d\x0f\x0b'
    body+=b'\x00' # all generated tokens must match one test
    accept=c(0)
    for i,row in enumerate(rows):
        if row[2]:accept+=test(i)+b'\x72'
    run=gg(0)+b'\x21\x03\x02\x40\x03\x40'+lg(2)+lg(1)+c(31)+b'\x71\x4f\x0d\x01'
    run+=lg(3)+lg(0)+lg(2)+b'\x76'+c(1)+b'\x71\x10\x00\x21\x03'
    run+=lg(2)+c(1)+b'\x6a\x21\x02\x0c\x00\x0b\x0b'+lg(3)+b'\x10\x01'
    bodies=[b'\x00'+body+b'\x0b',b'\x00'+accept+b'\x0b',b'\x02\x01\x7f\x01\x6d'+run+b'\x0b']
    code=section(10,vec([u(len(x))+x for x in bodies]))
    return b'\x00asm\x01\x00\x00\x00'+types+funcs+globs+exports+code

def transform(src,dst,mode='groups',groups=2,siblings=32,seed=7):
    begin=time.perf_counter();dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():raise FileExistsError(dst)
    rows=source(src,dst.parent)
    if mode=='plain':p.compile(packed(rows),dst)
    elif mode=='branch':p.compile(branch(rows),dst)
    elif mode in ('gc','groups'):
        if mode=='gc':groups,siblings=1,0
        if not 1<=groups<=32 or not 0<=siblings<=512:raise ValueError('Type budget')
        dst.write_bytes(gc_binary(rows,groups,siblings,seed))
        # Read and validate, preserving the original manually emitted bytes.
        tool('wasm-dis',[dst,'-o',dst.with_suffix('.wat')])
    else:raise ValueError(mode)
    return dict(mode=mode,states=len(rows),groups=groups if mode in ('gc','groups') else 0,siblings=siblings if mode in ('gc','groups') else 0,seed=seed,bytes=dst.stat().st_size,transform_ms=(time.perf_counter()-begin)*1000,sha256=digest(dst))

def lower(src,dst):
    begin=time.perf_counter();m=p.w.parse(tool('wasm-dis',[src]));read_ms=(time.perf_counter()-begin)*1000;t=time.perf_counter()
    # Binaryen has already canonicalized equivalent recursion groups on read.
    decl=[]
    for x in m[1:]:
        if x[0]=='type':decl.append(x)
        elif x[0]=='rec':decl.extend(x[1:])
    ids={};structs=set()
    for ty in decl:
        if len(ty)!=3:raise ValueError('Unsupported type definition')
        if ty[2]==['struct']:structs.add(ty[1])
        elif ty[2][0]!='func':raise ValueError('Only final empty structs and function types supported')
    allocated=[];used=set();ops={}
    for e in walk(m):ops[e[0]]=ops.get(e[0],0)+1
    for x in m[1:]:
        if x[0]=='global' and x[-1][0]=='struct.new_default':allocated.append(x[-1][1])
    for ty in allocated:ids.setdefault(ty,len(ids))
    for ty in sorted(structs):ids.setdefault(ty,len(ids))
    if not allocated: # scalar baseline: no type-sensitive lowering required
        if any(k.startswith(('ref.','struct.','array.')) for k in ops):raise ValueError('Unsupported reference operation')
    def rw(x):
        if not isinstance(x,list):return 'i32' if x=='eqref' else x
        if x and x[0]=='ref':
            if x in (['ref','null','eq'],['ref','eq']):return 'i32'
            raise ValueError('Unsupported value type')
        op=x[0]
        if op=='struct.new_default':
            if x[1] not in ids:raise ValueError('Non-empty struct allocation')
            used.add(x[1]);return ['i32.const',str(ids[x[1]])]
        if op=='ref.test':
            ty=x[1]
            if not isinstance(ty,list) or ty[0]!='ref' or ty[-1] not in ids:raise ValueError('Unsupported ref.test')
            if 'null' in ty and x[2][0] not in ('local.get','global.get','ref.null'):raise ValueError('Nullable test needs a pure operand')
            used.add(ty[-1]);value=rw(x[2]);eq=['i32.eq',value,['i32.const',str(ids[ty[-1]])]]
            return ['i32.or',eq,['i32.eq',value,['i32.const','-1']]] if 'null' in ty else eq
        if op=='ref.null':return ['i32.const','-1']
        if op=='ref.is_null':return ['i32.eq',rw(x[1]),['i32.const','-1']]
        if op.startswith(('ref.','struct.','array.')):raise ValueError('Unsupported reference operation '+op)
        return [rw(v) for v in x if not isinstance(v,list) or v[0]!='type']
    out=['module']+[rw(x) for x in m[1:] if x[0] not in ('type','rec')]
    # Scalar lowering accepts a narrow token profile, no reference imports or exports.
    if any(x[0] in ('import','table','memory','data','start','elem') for x in m[1:]):raise ValueError('Unsupported module effects')
    funcs={x[1]:x for x in m[1:] if x[0]=='func'}
    for ex in (x for x in m[1:] if x[0]=='export'):
        if ex[2][0]!='func':raise ValueError('Reference globals cannot escape')
        f=funcs[ex[2][1]]
        if any(isinstance(y,list) or y=='eqref' for x in f[2:] if x[0] in ('param','result') for y in x[1:]):raise ValueError('Reference ABI is unsupported')
    normalize_ms=(time.perf_counter()-t)*1000
    if dst is not None:
        p.compile(p.w.emit(out),dst)
    return dict(read_canonicalize_ms=read_ms,lower_ms=normalize_ms,canonical_empty_types=len(ids),allocated_token_types=len(set(allocated)),used_types=len(used),gc_operations=sum(v for k,v in ops.items() if k.startswith(('ref.','struct.','array.'))),output=out)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['transform','lower']);a.add_argument('input');a.add_argument('output');a.add_argument('--mode',choices=['plain','branch','gc','groups'],default='groups');a.add_argument('--groups',type=int,default=2);a.add_argument('--siblings',type=int,default=32);a.add_argument('--seed',type=int,default=7);v=a.parse_args()
    r=lower(v.input,Path(v.output)) if v.action=='lower' else transform(v.input,v.output,v.mode,v.groups,v.siblings,v.seed);r.pop('output',None);print(json.dumps(r))
