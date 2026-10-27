"""Restricted native-wait-compatible pair encoding. No novelty/security claim."""
import argparse, importlib.util, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('wait_base',ROOT/'research/connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
OPS=('load','store','add','sub','and','or','xor','xchg','cmpxchg')
OP={k:'i32.atomic.'+('rmw.' if k not in ('load','store') else '')+k for k in OPS}
REV={v:k for k,v in OP.items()}

def walk(x):
    if isinstance(x,list):
        yield x
        for y in x[1:]:yield from walk(y)

def compile(wat,dst):
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);dst.with_suffix('.wat').write_text(wat,encoding='utf8')
    w.tool('wat2wasm',[dst.with_suffix('.wat'),'--enable-threads','-o',dst])
    w.tool('wasm-validate',[dst,'--enable-threads'])

def read(src):
    w.tool('wasm-validate',[src,'--enable-threads'])
    return w.parse(w.tool('wasm2wat',[src,'--enable-threads','--fold-exprs','--no-debug-names']))

def memarg(x):
    off=0
    for a in x[1:]:
        if isinstance(a,str):
            if a.startswith('offset='):off=int(a.split('=')[1],0)
            elif not a.startswith('align='):raise ValueError('memory immediate '+a)
    return off,[a for a in x[1:] if isinstance(a,list)]

def residues(x):
    if x[0]=='i32.const':return {int(x[1],0)&7}
    if x[0] in ('i32.and','i32.add','i32.or','i32.xor'):
        a,b=residues(x[1]),residues(x[2]);f={'i32.and':lambda a,b:a&b,'i32.add':lambda a,b:a+b,'i32.or':lambda a,b:a|b,'i32.xor':lambda a,b:a^b}[x[0]]
        return {f(i,j)&7 for i in a for j in b}
    return set(range(8))

def choose(m):
    seen=set()
    for x in walk(m):
        if x[0]=='memory.atomic.wait32':
            off,args=memarg(x);seen|={(r+off)&7 for r in residues(args[0])}&{0,4}
    return {frozenset():'wide',frozenset({0}):'low',frozenset({4}):'high',frozenset({0,4}):'both'}[frozenset(seen)],sorted(seen)

def codecs(kind):
    # Two public elementary shears; the inverse reverses their order.
    steps={'identity':[],'both':[],'low':['v'],'high':['u'],'wide':['u','v']}[kind]
    pieces=[]
    for name,order in (('enc',steps),('dec',list(reversed(steps)))):
        body=''
        for s in order:
            i,j,r=('a','b',7) if s=='u' else ('b','a',13)
            body+=f'(local.set ${i} (i32.xor (local.get ${i}) (i32.rotl (local.get ${j}) (i32.const {r}))))'
        pieces.append(f'''(func $wp_{name} (param i64) (result i64) (local $a i32) (local $b i32)
          (local.set $a (i32.wrap_i64 (local.get 0)))
          (local.set $b (i32.wrap_i64 (i64.shr_u (local.get 0) (i64.const 32)))) {body}
          (i64.or (i64.extend_i32_u (local.get $a)) (i64.shl (i64.extend_i32_u (local.get $b)) (i64.const 32))))''')
    return ''.join(pieces)

def helper(kind,offset,name):
    n=1 if kind=='load' else 3 if kind=='cmpxchg' else 2
    result='' if kind=='store' else '(result i32)'
    pre=f'''(local $addr i64) (local $shift i64) (local $word i64) (local $seen i64) (local $d i64)
      (local $base i32) (local $old i32) (local $new i32)
      (local.set $addr (i64.add (i64.extend_i32_u (local.get 0)) (i64.const {offset})))
      (if (i32.or (i64.gt_u (local.get $addr) (i64.const 65532))
          (i64.ne (i64.and (local.get $addr) (i64.const 3)) (i64.const 0))) (then (unreachable)))
      (local.set $base (i32.and (i32.wrap_i64 (local.get $addr)) (i32.const -8)))
      (local.set $shift (i64.and (i64.shl (local.get $addr) (i64.const 3)) (i64.const 32)))
      (local.set $word (i64.atomic.load (local.get $base)))'''
    decode='''(local.set $d (call $wp_dec (local.get $word)))
      (local.set $old (i32.wrap_i64 (i64.shr_u (local.get $d) (local.get $shift))))'''
    if kind=='load':body=pre+decode+'(local.get $old)'
    else:
        value='(local.get 2)' if kind=='cmpxchg' else '(local.get 1)' if kind in ('store','xchg') else f'(i32.{kind} (local.get $old) (local.get 1))'
        cond='(if (i32.ne (local.get $old) (local.get 1)) (then (return (local.get $old))))' if kind=='cmpxchg' else ''
        patched='''(i64.or (i64.and (local.get $d) (i64.xor (i64.shl (i64.const 4294967295) (local.get $shift)) (i64.const -1)))
          (i64.shl (i64.extend_i32_u (local.get $new)) (local.get $shift)))'''
        ret='(return)' if kind=='store' else '(return (local.get $old))'
        body=pre+f'''(loop $retry {decode} {cond} (local.set $new {value})
          (local.set $seen (i64.atomic.rmw.cmpxchg (local.get $base) (local.get $word) (call $wp_enc {patched})))
          (if (i64.eq (local.get $seen) (local.get $word)) (then {ret}))
          (local.set $word (local.get $seen)) (br $retry)) (unreachable)'''
    return f'(func ${name} '+ '(param i32)'*n+result+body+')'

def transform(src,dst,mode='auto'):
    t=time.perf_counter();m=read(src)
    if [x for x in m[1:] if x[0]=='import']!=[['import','"env"','"memory"',['memory','1','1','shared']]]:raise ValueError('fixed one-page shared memory import required')
    if any(x[0] not in ('type','import','func','export') for x in m[1:]):raise ValueError('unsupported module section')
    if any(x[2][0]!='func' for x in m[1:] if x[0]=='export'):raise ValueError('only function exports')
    allowed={'module','type','import','memory','func','export','param','result','local','local.get','local.set','local.tee','call','block','loop','if','then','else','br','br_if','br_table','return','drop','select','unreachable','nop','memory.atomic.wait32','memory.atomic.wait64','memory.atomic.notify'}|set(REV)
    for x in walk(m):
        op=x[0]
        if op in ('param','result','local') and any(isinstance(a,str) and not a.startswith('$') and a not in ('i32','i64') for a in x[1:]):raise ValueError('only integer types')
        pure=op.startswith(('i32.','i64.')) and not any(s in op for s in ('load','store','atomic'))
        if op not in allowed and not pure:raise ValueError('unsupported instruction '+op)
    selected,footprint=choose(m);kind=selected if mode=='auto' else 'identity';specs={};sites=0
    def rw(x):
        nonlocal sites
        if not isinstance(x,list):return x
        if x[0] in REV:
            sites+=1;off,args=memarg(x);key=(REV[x[0]],off);name=specs.setdefault(key,'wp_op'+str(len(specs)))
            return ['call','$'+name,*map(rw,args)]
        y=[rw(v) for v in x]
        if x[0]=='memory.atomic.wait64':
            # Rebuild using original memarg strings; operands are evaluated once.
            args=[i for i,v in enumerate(y) if isinstance(v,list)];y[args[1]]=['call','$wp_enc',y[args[1]]]
        return y
    out=rw(m)
    out+=w.parse('(module '+codecs(kind)+''.join(helper(k,o,n) for (k,o),n in specs.items())+')')[1:]
    compile(w.emit(out),dst)
    return dict(mode=mode,codec=kind,wait32_residues=footprint,sites=sites,helpers=len(specs),bytes=Path(dst).stat().st_size,transform_ms=1000*(time.perf_counter()-t))

def fixture(profile):
    fs=[]
    for kind in OPS:
        n=1 if kind=='load' else 3 if kind=='cmpxchg' else 2
        fs.append(f'(func ${kind} (export "{kind}") '+ '(param i32)'*n+('' if kind=='store' else '(result i32)')+f'({OP[kind]} '+ ' '.join(f'(local.get {i})' for i in range(n))+'))')
    for off in (4,65532,4294967292):
        fs.append(f'(func (export "offset{off}") (param i32 i32) (result i32) (i32.atomic.rmw.add offset={off} (local.get 0) (local.get 1)))')
    for field in ([0] if profile=='low' else [4] if profile=='high' else [0,4] if profile=='both' else []):
        fs.append(f'''(func (export "wait{field}") (param i32 i32 i64) (result i32)
          (memory.atomic.wait32 offset={field} (i32.and (local.get 0) (i32.const -8)) (local.get 1) (local.get 2)))''')
    fs.extend(['''(func (export "wait64") (param i32 i64 i64) (result i32) (memory.atomic.wait64 (local.get 0) (local.get 1) (local.get 2)))''',
       '''(func (export "notify") (param i32 i32) (result i32) (memory.atomic.notify (local.get 0) (local.get 1)))''',
       '''(func (export "edge") (param i32 i32) (result i32) (call $store (i32.const 0) (local.get 1)) (i32.atomic.rmw.add offset=4294967292 (local.get 0) (local.get 1)))''',
       '''(func (export "bench") (param $n i32) (param $p i32) (result i32) (local $i i32) (local $sum i32)
       (block $done (loop $next (br_if $done (i32.ge_u (local.get $i) (local.get $n)))
       (local.set $sum (i32.xor (local.get $sum) (call $add (local.get $p) (i32.const 1))))
       (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $sum))'''])
    return '(module (import "env" "memory" (memory 1 1 shared))'+''.join(fs)+')'

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--mode',choices=['auto','identity'],default='auto');a=ap.parse_args()
    print(json.dumps(transform(a.input,a.output,a.mode),indent=2))
