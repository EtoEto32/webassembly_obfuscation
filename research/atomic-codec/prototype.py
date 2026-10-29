"""Atomic representation compatibility experiment; no secrecy/novelty claim."""
import argparse, copy, importlib.util, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('atomic_base',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
OPS=['load','store','add','sub','and','or','xor','xchg','cmpxchg']
OP={x:'i32.atomic.'+('rmw.' if x not in ('load','store') else '')+x for x in OPS}
REV={v:k for k,v in OP.items()}
A=0x9e3779b1;B=0x7f4a7c15;INV=pow(A,-1,1<<32)
MODES=['auto','plain','native-neg','cas-neg','cas-affine','native-affine','bad-and','bad-split']
def c(x):return f'(i32.const {x & 0xffffffff})'
def compile(wat,dst):
    dst=Path(dst)
    if dst.exists() or dst.with_suffix('.wat').exists():raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);dst.with_suffix('.wat').write_text(wat,encoding='utf-8')
    q.w.tool('wat2wasm',[dst.with_suffix('.wat'),'--enable-threads','-o',dst])
    q.w.tool('wasm-validate',[dst,'--enable-threads'])
def read(src):
    q.w.tool('wasm-validate',[src,'--enable-threads'])
    return q.w.parse(q.w.tool('wasm2wat',[src,'--enable-threads','--fold-exprs','--no-debug-names']))
def codec(mode):
    if mode=='plain':return 1,0
    return (A,B) if 'affine' in mode else (0xffffffff,0xffffffff)
def enc(x,mode):
    a,b=codec(mode)
    if a==0xffffffff and b==0xffffffff:return f'(i32.xor {x} {c(-1)})'
    return f'(i32.add (i32.mul {x} {c(a)}) {c(b)})'
def dec(x,mode):
    a,b=codec(mode)
    if a==0xffffffff and b==0xffffffff:return enc(x,mode)
    return f'(i32.mul (i32.sub {x} {c(b)}) {c(pow(a,-1,1<<32))})'
def helper(kind,offset,name,mode):
    n=1 if kind=='load' else 3 if kind=='cmpxchg' else 2
    params=' '.join('(param i32)' for _ in range(n));result='' if kind=='store' else '(result i32)'
    p='(local.get 0)';v='(local.get 1)';mem=f'offset={offset}'
    def atom(op,*args):return f'({OP[op]} {mem} {p} '+ ' '.join(args)+')'
    if kind=='load':body=dec(atom(kind),mode)
    elif kind=='store':body=atom(kind,enc(v,mode))
    elif kind in ('cmpxchg','xchg'):
        args=[enc(v,mode)]+([enc('(local.get 2)',mode)] if kind=='cmpxchg' else [])
        body=dec(atom(kind,*args),mode)
    elif mode.startswith('native') or mode=='bad-and':
        if mode=='native-affine':
            if kind not in ('add','sub'):raise ValueError('native-affine requires only add/sub RMW')
            target=kind;arg=f'(i32.mul {v} {c(A)})'
        else:
            target={'add':'sub','sub':'add','and':'or','or':'and','xor':'xor'}[kind]
            arg=enc(v,mode) if kind in ('and','or') else v
            if mode=='bad-and' and kind=='and':target='and'
        body=dec(atom(target,arg),mode)
    else:
        # Read/calculate/CAS uses the observed physical word as the expected value.
        # On failure it retries with the returned physical value; no shared plaintext.
        old='(local.get $old)';new=enc(f'(i32.{kind} {dec(old,mode)} {v})',mode)
        if mode=='bad-split':
            body=f'(local $old i32) (local.set $old {atom("load")}) {atom("store",new)} {dec(old,mode)}'
        else:
            body=f'''(local $old i32) (local $seen i32)
              (local.set $old {atom('load')})
              (loop $retry
                (local.set $seen {atom('cmpxchg',old,new)})
                (if (i32.eq (local.get $seen) {old}) (then (return {dec(old,mode)})))
                (local.set $old (local.get $seen)) (br $retry)) (unreachable)'''
    return f'(func ${name} {params} {result} {body})'
def transform(src,dst,mode):
    t=time.perf_counter();m=read(src);requested=mode
    imports=[x for x in m[1:] if x[0]=='import']
    if imports!=[['import','"env"','"memory"',['memory','1','1','shared']]]:raise ValueError('one fixed shared env.memory import required')
    if any(x[0] not in ('type','import','func','export') for x in m[1:]):raise ValueError('unsupported module section')
    if any(x[2][0]!='func' for x in m[1:] if x[0]=='export'):raise ValueError('only function exports')
    for x in q.walk(m):
        op=x[0]
        if op in REV:continue
        if op.startswith(('memory.','table.','ref.','global.','i64.','f32.','f64.','v128.')) or '.load' in op or '.store' in op or '.atomic.' in op or op in ('call_indirect','call_ref'):
            raise ValueError('unsupported instruction '+op)
        if op in ('param','result','local') and any(isinstance(v,str) and not v.startswith('$') and v!='i32' for v in x[1:]):raise ValueError('only i32 types')
    if mode=='auto':
        bitwise=any(x[0] in (OP['and'],OP['or'],OP['xor']) for x in q.walk(m))
        mode='native-neg' if bitwise else 'native-affine'
    specs={};count=0
    def rewrite(e):
        nonlocal count
        if not isinstance(e,list):return e
        if e[0] in REV:
            count+=1;kind=REV[e[0]];offset=0
            for v in e[1:]:
                if isinstance(v,str):
                    if v.startswith('offset='):offset=int(v.split('=')[1],0)
                    elif v!='align=4':raise ValueError('unsupported memory immediate '+v)
            if mode=='plain':return copy.deepcopy(e)
            if mode=='native-affine' and kind in ('and','or','xor'):raise ValueError('native-affine incompatible footprint')
            key=(kind,offset);name=specs.setdefault(key,'ac'+str(len(specs)))
            return ['call','$'+name,*[rewrite(v) for v in e[1:] if isinstance(v,list)]]
        return [rewrite(v) for v in e]
    out=rewrite(m)
    for (kind,offset),name in specs.items():out.append(q.w.parse('(module '+helper(kind,offset,name,mode)+')')[1])
    compile(q.w.emit(out),dst)
    return dict(mode=mode,requested_mode=requested,sites=count,helpers=len(specs),transform_ms=(time.perf_counter()-t)*1000,bytes=Path(dst).stat().st_size,a=codec(mode)[0],b=codec(mode)[1])
def fixture(counter=False):
    ops=['load','store','add','sub','xchg','cmpxchg'] if counter else OPS
    fs=[]
    for op in ops:
        n=1 if op=='load' else 3 if op=='cmpxchg' else 2
        fs.append(f'(func ${op} (export "{op}") '+ '(param i32) '*n+('' if op=='store' else '(result i32)')+f'({OP[op]} '+' '.join(f'(local.get {i})' for i in range(n))+'))')
    for off in (4,65532,0xfffffffc):
        fs.append(f'(func (export "offset{off}") (param i32 i32) (result i32) (i32.atomic.rmw.add offset={off} (local.get 0) (local.get 1)))')
    fs.append('''(func (export "bench") (param $n i32) (param $p i32) (result i32)
       (local $i i32) (local $sum i32)
       (block $done (loop $next (br_if $done (i32.ge_u (local.get $i) (local.get $n)))
         (local.set $sum (i32.xor (local.get $sum) (call $add (local.get $p) (i32.const 1))))
         (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $sum))''')
    return '(module (import "env" "memory" (memory 1 1 shared))\n'+'\n'.join(fs)+')'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--mode',choices=MODES,required=True);a=p.parse_args()
    print(json.dumps(transform(a.input,a.output,a.mode),indent=2))
