"""Fixed-rotation observation-history compiler; restricted actual-Wasm profile."""
import argparse
import importlib.util
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('rotation_common',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
MASK=(1<<32)-1


def rot(x,k,w=32):
    k%=w;mask=(1<<w)-1
    return ((x<<k)|(x>>(w-k)))&mask


def schedule(k,mask,w=32):
    if not 0<mask<1<<w or not 0<=k<w:raise ValueError('rotation / observation mask')
    need=rot(mask,-k,w);remaining=need;parts=[]
    for age in range(w):
        take=remaining&rot(mask,age*k,w)
        parts.append(rot(take,k,w));remaining^=take
        if not remaining:break
    assert not remaining
    inputs=[mask]+[sum(parts[j:]) for j in range(1,len(parts))]
    assert sum(parts)==mask
    return dict(rotation=k,mask=mask,history=len(parts),output_masks=parts,input_masks=inputs)


def source(k,mask,dynamic=False):
    turn='(i32.and (local.get 5) (i32.const 31))' if dynamic else f'(i32.const {k})'
    inject=f'(i32.and (local.get 5) (i32.const {MASK^mask}))' if dynamic else '(local.get 5)'
    return f'''(module (memory (export "memory") 1 1)
      (func (export "run") (param i32 i32 i32) (result i32) (local i32 i32 i32)
        (local.set 4 (local.get 0))
        (block (loop (br_if 1 (i32.ge_u (local.get 3) (local.get 2)))
          (local.set 5 (i32.load (i32.add (local.get 1) (i32.shl (local.get 3) (i32.const 2)))))
          (local.set 4 (i32.xor (i32.rotl (local.get 4) {turn}) {inject}))
          (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0)))
        (i32.and (local.get 4) (i32.const {mask}))))'''


def history(k,mask):
    s=schedule(k,mask);h=s['history'];outs=list(range(6,6+h));ins=list(range(6+h,6+2*h-1))
    def rotated(expr,amount):
        return f'(i32.rotl {expr} (i32.const {amount%32}))' if amount%32 else expr
    def term(index,amount,m):
        return f'(i32.and {rotated(f"(local.get {index})",amount)} (i32.const {m}))'
    terms=[term(4,0,mask)]
    terms += [term(outs[a],(a+1)*k,m) for a,m in enumerate(s['output_masks']) if m]
    terms += [term(ins[j-1],j*k,m) for j,m in enumerate(s['input_masks']) if j and m]
    expr=terms[0]
    for t in terms[1:]:expr=f'(i32.xor {expr} {t})'
    init=' '.join(f'(local.set {i} (i32.and {rotated("(local.get 0)",-a*k)} (i32.const {mask})))' for a,i in enumerate(outs))
    shift=' '.join(f'(local.set {outs[j]} (local.get {outs[j-1]}))' for j in range(h-1,0,-1))
    shift+=f' (local.set {outs[0]} (local.get 5))'
    shift+=' '+' '.join(f'(local.set {ins[j]} (local.get {ins[j-1]}))' for j in range(h-2,0,-1))
    if ins:shift+=f' (local.set {ins[0]} (local.get 4))'
    return f'''(module (memory (export "memory") 1 1)
      (func (export "run") (param i32 i32 i32) (result i32) (local {' '.join(['i32']*(2*h+2))})
        {init}
        (block (loop (br_if 1 (i32.ge_u (local.get 3) (local.get 2)))
          (local.set 4 (i32.load (i32.add (local.get 1) (i32.shl (local.get 3) (i32.const 2)))))
          (local.set 5 {expr}) {shift}
          (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0)))
        (local.get {outs[0]})))'''


def transform(src,dst):
    start=time.perf_counter_ns();m=q.read(src)
    rots=[e for e in q.walk(m) if e[0]=='i32.rotl']
    masks=[e for e in q.walk(m) if e[0]=='i32.and']
    if len(rots)!=1 or len(masks)!=1 or rots[0][2][0]!='i32.const' or masks[0][2][0]!='i32.const':
        raise q.Unsupported('fixed rotate / mask source profile required')
    k=int(rots[0][2][1])&31;mask=int(masks[0][2][1])&MASK
    config=schedule(k,mask)
    proof=Path(dst).with_name(Path(dst).stem+'-source-profile.wasm')
    q.compile(source(k,mask),proof)
    if q.read(proof)!=m:raise q.Unsupported('source must match the complete public scan profile')
    read_end=time.perf_counter_ns();q.compile(history(k,mask),dst);end=time.perf_counter_ns()
    return dict(**config,read_profile_ms=(read_end-start)/1e6,generate_compile_ms=(end-read_end)/1e6,total_ms=(end-start)/1e6)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('src');ap.add_argument('dst');a=ap.parse_args()
    print(json.dumps(transform(a.src,a.dst)))
