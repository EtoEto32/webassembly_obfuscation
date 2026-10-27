"""Independent controls, algebra checks, canonical comparison, WABT engine."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import time
import prototype as p
import attack as a
from run import save,command,HERE

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);opt=ap.parse_args();out=opt.output;out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((opt.input/'manifest.json').read_text());rng=random.Random(90817)
    algebra=0
    for i in range(120):
        for j in range(120):
            for d in (0,1):
                x,y=p.move(p.factor((),(i,)),p.factor((),(j,)),d)
                assert p.M[x.table[0]][y.table[0]]==p.M[i][j];algebra+=1
    variable_checks=0
    for _ in range(128):
        left=p.factor((0,1,2),[rng.randrange(120) for _ in range(8)]);right=p.factor((2,3,4),[rng.randrange(120) for _ in range(8)])
        for d in (0,1):
            x,y=p.move(left,right,d)
            for k in range(32):assert p.M[p.value(left,k)][p.value(right,k)]==p.M[p.value(x,k)][p.value(y,k)];variable_checks+=1
    canonical=[];interpreter=[];analysis=[]
    for name in manifest['models']:
        src=opt.input/f'{name}.source.raw.wasm';t=p.source(src);b=a.BDD();root=b.source(t);code=b.wasm(root)
        for row in manifest['files']:
            if row['model']==name and '.' in row['mode']:
                assert (opt.input/row['path']).with_suffix('.wat').read_text(encoding='utf-8')==code
                canonical.append(row['path'])
        for mode in ('source','base','basis','fused','braid'):
            path=opt.input/f'{name}.{mode}.O3.wasm';word=a.extract(path) if mode!='source' else None
            times=[];ns=[]
            for _ in range(5):
                gc.collect();bb=a.BDD();start=time.perf_counter();rr=bb.source(t) if mode=='source' else bb.recover(word);times.append((time.perf_counter()-start)*1000);ns.append(len(bb.nodes));assert bb.wasm(rr)==code
            analysis.append(dict(model=name,mode=mode,samples_ms=times,median_ms=statistics.median(times),range_ms=[min(times),max(times)],bdd_allocated=ns[0],apply_calls=bb.calls,output_nodes=len(bb.reachable(rr))))
    probes=[(0,0),(1,1),(0xffffffff,0),(0x80000000,0x7fffffff),(0x55555555,0xaaaaaaaa),(0xffffffff,0xffffffff)]
    for row in manifest['files']:
        text=p.w.tool('wasm2wat',[opt.input/row['path']]);extra=''
        for j,(x,y) in enumerate(probes):extra+=f'(func (export "check{j}") (result i32) (call 0 (i32.const {x}) (i32.const {y})))'
        target=out/('interp.'+row['path']);p.c.compile_wat(text.rstrip()[:-1]+extra+')',target)
        log=p.w.tool('wasm-interp',[target,'--run-all-exports']);(target.with_suffix('.log')).write_text(log)
        got=[int(v) for v in re.findall(r'check\d+\(\) => i32:(\d+)',log)]
        t=manifest['models'][row['model']]
        expected=[p.eval_formula(t,x|(y<<32)) for x,y in probes]
        assert got==expected,(row,got,expected);interpreter.append(dict(path=row['path'],values=got))
    # Incorrect un-conjugated exchange: locate an actual semantic witness.
    t=p.source(opt.input/'alternating8.source.raw.wasm');word=p.barrington(t);vs=sorted(p.variables(t));negative=None
    def result(ws,x):
        r=0
        for f in reversed(ws):r=p.PERMS[p.value(f,x)][r]
        return int(r!=0)
    for j in range(len(word)-1):
        bad=list(word);bad[j:j+2]=reversed(bad[j:j+2])
        for k in range(1<<len(vs)):
            x=sum(((k>>n)&1)<<v for n,v in enumerate(vs))
            if result(bad,x)!=p.eval_formula(t,x):negative=dict(index=j,x=x&MASK,y=x>>32,expected=p.eval_formula(t,x),actual=result(bad,x));break
        if negative:
            p.c.compile_wat(p.wasm(bad),out/'wrong-swap.wasm');break
    assert negative
    actual=command(['node','-e','const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(JSON.stringify(e.run(Number(process.argv[2]),Number(process.argv[3]))));',out/'wrong-swap.wasm',negative['x'],negative['y']]);assert actual==negative['actual']
    refusals=[]
    for label,expr in [('unmasked','(local.get 0)'),('division','(i32.div_u (local.get 0) (local.get 1))'),('trap','(block (result i32) (drop (i32.div_u (i32.const 1) (i32.const 0))) (i32.const 0))')]:
        src=out/(label+'.wasm');p.c.compile_wat('(module (func (export "run") (param i32 i32) (result i32) '+expr+'))',src)
        try:p.source(src);raise AssertionError('Accepted '+label)
        except ValueError as e:refusals.append(dict(label=label,error=str(e)))
    # A mutable memory must not be silently treated as the original data segment.
    text=p.w.tool('wasm2wat',[opt.input/'alternating8.braid.raw.wasm']);pos=text.index('    v128.const');text=text[:pos]+'    i32.const 0\n    i32.const 255\n    i32.store8\n'+text[pos:]
    p.c.compile_wat(text,out/'mutable.wasm')
    try:a.extract(out/'mutable.wasm');raise AssertionError('Accepted mutable memory')
    except ValueError as e:refusals.append(dict(label='mutable',error=str(e)))
    save(out/'verification.json',dict(status='completed',constant_pair_move_checks=algebra,input_dependent_move_checks=variable_checks,canonical_equal=canonical,interpreter_calls=len(interpreter)*len(probes),interpreter=interpreter,wrong_swap_witness=negative,refusals=refusals))
    save(out/'analysis-timing.json',analysis)
    print(json.dumps(dict(status='completed',canonical=len(canonical),interpreter_calls=len(interpreter)*len(probes),refusals=len(refusals))))

MASK=(1<<32)-1
if __name__=='__main__':main()
