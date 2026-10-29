"""Finite pure-i32 dataflow scheduler. A falsification prototype, not a novelty claim."""
import argparse, hashlib, importlib.util, json, random, struct, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('packet_base',ROOT/'research/exception-packet/prototype.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
OPS=['i32.'+x for x in sorted(p.OPS1|p.OPS2)]+['select']
ARITY={op:(3 if op=='select' else 1 if op[4:] in p.OPS1 else 2) for op in OPS}
BASE=256;STRIDE=32;LIMIT=1024

def graph(root,n,seed):
    nodes=list(p.walk(root));random.Random(seed).shuffle(nodes);ids={x:i for i,x in enumerate(nodes)}
    if len(nodes)>LIMIT:raise ValueError('At most 1024 DAG nodes')
    data=bytearray(BASE+STRIDE*len(nodes));ops=0
    struct.pack_into('<4I',data,0,len(nodes),n,ids[root],0)
    for i,x in enumerate(nodes):
        if x[0]=='i32.const':row=[0,0,0,0,x[1],3,0xffffffff,0]
        elif x[0]=='arg':row=[1,x[1],0,0,0,3,0xffffffff,0]
        else:
            deps=[ids[a] for a in x[1:]];deps+=deps[:1]*(3-len(deps));ops+=1
            row=[OPS.index(x[0])+2,*deps,0,0,0xffffffff,0]
        struct.pack_into('<8I',data,BASE+STRIDE*i,*row)
    struct.pack_into('<I',data,12,ops)
    return bytes(data),dict(nodes=len(nodes),operations=ops,arity=n,root=ids[root])

def scheduler(data,atomic=True):
    ld='i32.atomic.load' if atomic else 'i32.load';st='i32.atomic.store' if atomic else 'i32.store'
    # All addresses naturally aligned; only scalar-total instructions are dispatched.
    claim='(i32.eqz (i32.atomic.rmw.cmpxchg (local.get 0) (i32.const 0) (i32.const 1)))' if atomic else '''
      (if (result i32) (i32.eqz (i32.load (local.get 0)))
       (then (i32.store (local.get 0) (i32.const 1)) (i32.const 1)) (else (i32.const 0)))'''
    done='(drop (i32.atomic.rmw.add (i32.const 64) (i32.const 1)))' if atomic else '(i32.store (i32.const 64) (i32.add (i32.load (i32.const 64)) (i32.const 1)))'
    dispatch=''.join(f'(if (i32.eq (local.get $op) (i32.const {j+2})) (then (return ({op} '+ ' '.join(f'(local.get {a})' for a in ('$a','$b','$c')[:ARITY[op]])+'))))' for j,op in enumerate(OPS))
    args=' '.join('(param i32)' for _ in range(16))
    fill=''.join(f'({st} (i32.const {128+4*i}) (local.get {i}))' for i in range(16))
    ready=[f'(i32.eq ({ld} offset=20 (local.get ${x})) (i32.const 3))' for x in ('a','b','c')]
    check=f'(i32.and (i32.and {ready[0]} {ready[1]}) {ready[2]})'
    loaddeps=''.join(f'(local.set ${x} (call $addr ({ld} offset={4*(j+1)} (local.get $p))))' for j,x in enumerate(('a','b','c')))
    callargs=' '.join(f'({ld} offset=16 (local.get ${x}))' for x in ('a','b','c'))
    return f'''(module
 (import "env" "memory" (memory 1 1 shared))
 (func $addr (param i32) (result i32) (i32.add (i32.const 256) (i32.shl (local.get 0) (i32.const 5))))
 (func $claim (param i32) (result i32) {claim})
 (func $eval (param $op i32) (param $a i32) (param $b i32) (param $c i32) (result i32) {dispatch} (unreachable))
 (func $init (export "init") {args} (local $i i32) (local $p i32) (local $op i32)
  {fill} ({st} (i32.const 64) (i32.const 0))
  (loop $next
   (local.set $p (call $addr (local.get $i)))
   (local.set $op ({ld} (local.get $p)))
   ({st} offset=20 (local.get $p) (select (i32.const 3) (i32.const 0) (i32.lt_u (local.get $op) (i32.const 2))))
   ({st} offset=24 (local.get $p) (i32.const -1))
   (if (i32.eq (local.get $op) (i32.const 1)) (then
    ({st} offset=16 (local.get $p) ({ld} (i32.add (i32.const 128) (i32.shl ({ld} offset=4 (local.get $p)) (i32.const 2)))))))
   (if (i32.ge_u (local.get $op) (i32.const 2)) (then ({st} offset=16 (local.get $p) (i32.const 0))))
   (local.set $i (i32.add (local.get $i) (i32.const 1)))
   (br_if $next (i32.lt_u (local.get $i) ({ld} (i32.const 0))))))
 (func $attempt (export "attempt") (param $i i32) (param $worker i32) (result i32)
  (local $p i32) (local $op i32) (local $a i32) (local $b i32) (local $c i32) (local $v i32)
  (local.set $p (call $addr (local.get $i)))
  (local.set $op ({ld} (local.get $p)))
  (if (i32.lt_u (local.get $op) (i32.const 2)) (then (return (i32.const 0))))
  (if ({ld} offset=20 (local.get $p)) (then (return (i32.const 0))))
  {loaddeps}
  (if (i32.eqz {check}) (then (return (i32.const 0))))
  (if (i32.eqz (call $claim (i32.add (local.get $p) (i32.const 20)))) (then (return (i32.const 0))))
  (local.set $v (call $eval (local.get $op) {callargs}))
  ({st} offset=16 (local.get $p) (local.get $v))
  ({st} offset=24 (local.get $p) (local.get $worker))
  ({st} offset=20 (local.get $p) (i32.const 3))
  {done} (i32.const 1))
 (func $work (export "work") (param $worker i32) (local $i i32) (local $n i32)
  (local.set $n ({ld} (i32.const 0)))
  (local.set $i (i32.rem_u (i32.mul (local.get $worker) (i32.const 73)) (local.get $n)))
  (block $end (loop $scan
   (br_if $end (i32.eq ({ld} (i32.const 64)) ({ld} (i32.const 12))))
   (drop (call $attempt (local.get $i) (local.get $worker)))
   (local.set $i (i32.rem_u (i32.add (local.get $i) (i32.const 1)) (local.get $n))) (br $scan))))
 (func $result (export "result") (result i32) ({ld} offset=16 (call $addr ({ld} (i32.const 8)))))
 (func (export "run") {args} (result i32)
  (call $init {' '.join(f'(local.get {i})' for i in range(16))}) (call $work (i32.const 0)) (call $result))
 (data (i32.const 0) "{''.join(chr(92)+format(x,'02x') for x in data)}"))'''

def transform(src,dst,seed=20261019,atomic=True):
    start=time.perf_counter();n,name,root=p.read(src);data,info=graph(root,n,seed)
    p.compile(scheduler(data,atomic),dst)
    return dict(info,source_export=name,atomic=atomic,seed=seed,linear_memory_bytes=65536,
                used_memory_bytes=len(data),bytes=Path(dst).stat().st_size,elapsed_ms=(time.perf_counter()-start)*1000)

def optimize(src,dst):
    p.w.tool('wasm-opt',[src,'--enable-threads','-O3','-o',dst]);p.w.tool('wasm-validate',[dst,'--enable-threads'])

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');a.add_argument('--seed',type=int,default=20261019);a.add_argument('--serial-nonatomic',action='store_true');v=a.parse_args()
    print(json.dumps(transform(v.input,v.output,v.seed,not v.serial_nonatomic)))
