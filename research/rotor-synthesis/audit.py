import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import prototype as p

def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];manifest=[];wabt=0;replays=0
    for name in ('and3','majority3','mux3'):
        n,_,source=p.w.source(base/(name+'-plain.wasm'))
        for opt in ('raw','O3'):
            src=base/(name+'-rotor'+('-O3' if opt=='O3' else '')+'.wasm');r=p.read(src)
            f,a=p.symbolic_recover(r);assert all(p.evaluate(f,x)==p.evaluate(source,x) for x in range(8));a.update(name=name,optimization=opt);rows.append(a)
            dest=out/(name+'-'+opt+'-symbolic.wasm');p.save(p.w.plain_wat(n,'"run"',f),dest)
            manifest.append({'name':name,'mode':'symbolic','file':dest.name})
            replay=out/(name+'-'+opt+'-replay.wasm');p.save(p.render(r),replay)
            if opt=='O3':p.w.tool('wasm-opt',[replay,'-O3','--enable-bulk-memory','-o',replay.with_suffix('.opt.wasm')]);replay=replay.with_suffix('.opt.wasm')
            assert replay.read_bytes()==src.read_bytes();replays+=1
            mod=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs']))
            args=[(0,0,0),(-1,-1,-1),(0x12345678,-1,0x87654321),(-1,0,-1)]
            for j,xs in enumerate(args):
                text=f'(module (func (export "probe{j}") (result i32) (call 0 '+ ' '.join(f'(i32.const {x})' for x in xs)+')))' ;mod.append(p.w.parse(text)[1])
            wrapper=out/(name+'-'+opt+'-interpreter.wasm');p.save(p.w.emit(mod),wrapper);raw=p.w.tool('wasm-interp',[wrapper,'--run-all-exports']);(out/(name+'-'+opt+'-interpreter.txt')).write_text(raw)
            found=[int(v) for v in re.findall(r'probe\d+\(\) => i32:(\d+)',raw)];assert len(found)==4
            for x,y in zip(args,found):
                expected={'and3':lambda:a0&a1&a2,'majority3':lambda:(a0&a1)|(a0&a2)|(a1&a2),'mux3':lambda:(a0&a1)|(~a0&a2)}
                a0,a1,a2=x;assert y==expected[name]()&p.MASK;wabt+=1
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));run=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=60)
    (out/'check.stdout.txt').write_text(run.stdout);(out/'check.stderr.txt').write_text(run.stderr)
    if run.returncode:raise RuntimeError(run.stderr)
    controls=[]
    r=p.read(base/'majority3-rotor.wasm');short=copy.deepcopy(r);short['bound']=1;p.save(p.render(short),out/'short.wasm')
    for method in (p.recover,p.symbolic_recover):
        try:method(short)
        except ValueError:controls.append(method.__name__+' short bound rejected')
        else:raise AssertionError('short bound accepted')
    text=p.render(r).replace('(i32.xor (local.get $active) (local.get $rotor))','(local.get $rotor)');p.save(text,out/'forged.wasm')
    try:p.read(out/'forged.wasm')
    except ValueError:controls.append('forged evaluator rejected')
    else:raise AssertionError('forged evaluator accepted')
    summary={'byte_replays':replays,'wabt_calls':wabt,'symbolic_attacks':rows,'negative_controls':controls,'correctness':json.loads((out/'correctness.json').read_text())}
    (out/'audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='correctness'}))

if __name__=='__main__':main(*sys.argv[1:])
