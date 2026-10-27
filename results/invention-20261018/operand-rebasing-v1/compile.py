"""Pure four-input Wasm expression -> fused residual Mealy transducer.

This is a candidate compiler, not a validated security claim.
"""
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
import transform as wasm

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return wasm.parse(wasm.tool('wasm2wat',[p,'--fold-exprs']))
def items(n,k):return [a for a in n if isinstance(a,list) and a[0]==k]
def write(p,wat):
    if p.exists() or Path(str(p)+'.wat').exists():raise ValueError('Refuse overwrite')
    Path(str(p)+'.wat').write_text(wat,encoding='utf-8')
    wasm.tool('wat2wasm',[str(p)+'.wat','-o',p]);wasm.tool('wasm-validate',[p])
def count(n,p):return (int(n[1])==p) if n[0]=='local.get' else sum(count(a,p) for a in n[1:] if isinstance(a,list))
def pivot_ok(n,p):
    if count(n,p)!=1:return False
    if n[0]=='local.get':return True
    if n[0] not in ('i32.add','i32.sub','i32.xor'):return False
    return any(count(a,p)==1 and pivot_ok(a,p) for a in n[1:] if isinstance(a,list))
def recognize(path):
    m=read(path);fs=items(m,'func')
    if len(fs)!=1 or items(m,'export')!=[['export','"run"',['func','0']]]:raise ValueError('only one run function supported')
    if any(a[0] not in ('type','func','export') for a in m[1:] if isinstance(a,list)):raise ValueError('module effects not supported')
    f=fs[0]
    if items(f,'param')!=[['param','i32','i32','i32','i32']] or items(f,'result')!=[['result','i32']] or items(f,'local'):raise ValueError('four i32 parameters, one result, no locals')
    body=[a for a in f[1:] if isinstance(a,list) and a[0] not in ('type','param','result')]
    if len(body)!=1:raise ValueError('single expression required')
    root=body[0]
    pivots=[p for p in (1,2,3) if pivot_ok(root,p)]
    if not pivots:raise ValueError('no certified non-anchor bijective pivot')
    return root,pivots

def machine(root,minimize=True):
    carry=0
    def lower(n):
        nonlocal carry
        if n[0]=='local.get' and 0<=int(n[1])<4:return ('input',int(n[1]))
        if n[0]=='i32.const' and int(n[1]) in (0,-1):return ('constant',int(n[1])&1)
        if n[0] not in ('i32.add','i32.sub','i32.xor','i32.and','i32.or') or len(n)!=3:raise ValueError('unsupported expression '+n[0])
        a,b=lower(n[1]),lower(n[2]);slot=-1
        if n[0] in ('i32.add','i32.sub'):slot=carry;carry+=1
        return (n[0][4:],slot,a,b)
    ir=lower(['i32.sub',root,['local.get','0']])
    if carry>7:raise ValueError('prototype limit: at most seven carry/borrow bits')
    def transition(state,symbol):
        new=0
        def bit(n):
            nonlocal new
            if n[0]=='input':return (symbol>>n[1])&1
            if n[0]=='constant':return n[1]
            a,b=bit(n[2]),bit(n[3]);kind=n[0]
            if kind in ('add','sub'):
                old=(state>>n[1])&1;v=a+b+old if kind=='add' else a-b-old
                c=(v>>1) if kind=='add' else int(v<0)
                new|=c<<n[1];return v&1
            return {'xor':a^b,'and':a&b,'or':a|b}[kind]
        value=bit(ir);return new,value
    reachable={0};front=[0];table={}
    while front:
        state=front.pop();table[state]=[transition(state,s) for s in range(16)]
        for dest,_ in table[state]:
            if dest not in reachable:reachable.add(dest);front.append(dest)
    states=sorted(reachable);partition={q:i for i,q in enumerate(states)}
    if minimize:
        partition={q:0 for q in states}
        while True:
            signatures={};updated={}
            for q in states:
                signature=tuple((o,partition[t]) for t,o in table[q])
                updated[q]=signatures.setdefault(signature,len(signatures))
            if updated==partition:break
            partition=updated
    classes=max(partition.values())+1;reps={}
    for q in states:reps.setdefault(partition[q],q)
    perm=list(range(classes));random.Random(20261018).shuffle(perm)
    encoded=[0]*(classes*16)
    for group,q in reps.items():
        for symbol,(target,output) in enumerate(table[q]):encoded[perm[group]*16+symbol]=(perm[partition[target]]<<1)|output
    return encoded,perm[partition[0]],{'carry_bits':carry,'reachable_states':len(states),'states':classes,
                                     'transition_entries':len(encoded),'minimized':minimize}

def emit_machine(data,start):
    blob=''.join('\\%02x'%b for v in data for b in struct.pack('<I',v))
    alphabet='(i32.or (i32.or '+ ' '.join(f'(i32.shl (i32.and (i32.shr_u (local.get {j}) (local.get 4)) (i32.const 1)) (i32.const {j}))' for j in (0,1))+') (i32.or '+' '.join(f'(i32.shl (i32.and (i32.shr_u (local.get {j}) (local.get 4)) (i32.const 1)) (i32.const {j}))' for j in (2,3))+'))'
    return f'''(module
      (memory 1 1) (data (i32.const 0) "{blob}")
      (func (param i32 i32) (result i32) (i32.add (local.get 0) (local.get 1)))
      (func (param i32 i32 i32 i32) (result i32 i32) (local i32 i32 i32 i32)
        (local.set 5 (i32.const {start}))
        (loop
          (local.set 7 (i32.load (i32.shl (i32.or (i32.shl (local.get 5) (i32.const 4)) {alphabet}) (i32.const 2))))
          (local.set 6 (i32.or (local.get 6) (i32.shl (i32.and (local.get 7) (i32.const 1)) (local.get 4))))
          (local.set 5 (i32.shr_u (local.get 7) (i32.const 1)))
          (local.set 4 (i32.add (local.get 4) (i32.const 1)))
          (br_if 0 (i32.lt_u (local.get 4) (i32.const 32))))
        (local.get 0) (local.get 6))
      (func (export "run") (param i32 i32 i32 i32) (result i32)
        (call 1 (local.get 0) (local.get 1) (local.get 2) (local.get 3)) (call 0)))'''

def transform(src,out,minimize=True):
    root,pivots=recognize(src);data,start,info=machine(root,minimize)
    write(out,emit_machine(data,start))
    return {**info,'pivots':pivots,'inputSHA256':sha(src),'outputSHA256':sha(out),'initial_state':start}

def build(out):
    out.mkdir();bench={
      'add-xor': '(i32.xor (i32.add (local.get 0) (local.get 1)) (i32.add (local.get 2) (local.get 3)))',
      'xor-add': '(i32.add (i32.xor (local.get 0) (local.get 1)) (i32.xor (local.get 2) (local.get 3)))',
      'nested': '(i32.sub (i32.xor (i32.add (local.get 0) (local.get 1)) (local.get 2)) (local.get 3))',
      'reused-anchor': '(i32.xor (i32.add (local.get 0) (i32.xor (local.get 1) (local.get 2))) (i32.add (local.get 3) (local.get 0)))'}
    records=[]
    for name,expression in bench.items():
        plain=out/(name+'-plain.wasm');write(plain,'(module (func (export "run") (param i32 i32 i32 i32) (result i32) '+expression+'))')
        records.append({'kernel':name,'mode':'plain','file':plain.name,'sha256':sha(plain),'bytes':plain.stat().st_size})
        for mode,mini in [('fused',True),('unminimized',False)]:
            target=out/(name+'-'+mode+'.wasm');info=transform(plain,target,mini)
            records.append({'kernel':name,'mode':mode,'file':target.name,'sha256':sha(target),'bytes':target.stat().st_size,**info})
    (out/'manifest.json').write_text(json.dumps({'artifacts':records,'sourceSHA256':sha(Path(__file__)),'note':'Initial construction validation only; no resistance result.'},indent=2),encoding='utf-8')
    (out/'compile.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(records,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','transform']);ap.add_argument('source',type=Path);ap.add_argument('output',type=Path,nargs='?');a=ap.parse_args()
    if a.command=='build':build(a.source.resolve())
    else:print(json.dumps(transform(a.source,a.output),indent=2))
