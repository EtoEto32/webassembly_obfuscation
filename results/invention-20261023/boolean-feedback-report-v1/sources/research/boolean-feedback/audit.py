import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import attack
import prototype as p
from shared import h,a,load
saved=sys.modules.get('prototype');sys.modules['prototype']=h
verify=load('bf_verify',h.HERE/'verify.py')
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved
z3=verify.z3


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);exp=json.loads((base/'experiment.json').read_text());proofs=[];diagnostics=[];replays=0
    args=[z3.BitVec('x',32),z3.BitVec('y',32)]
    for row in exp['attacks']:
        original=verify.symbolic(base/(row['name']+'-plain.wasm'),args);recovered=verify.symbolic(row['output'],args);s=z3.Solver();s.set(timeout=15000);s.add(original!=recovered);status=str(s.check());proofs.append({'name':row['name'],'mode':row['mode'],'optimization':row['optimization'],'status':status})
        if status!='unsat':raise AssertionError(proofs[-1])
    for row in exp['transformations']:
        src=base/(row['name']+'-plain.wasm');dest=out/(row['name']+'-'+row['mode']+'-replay.wasm');p.transform(src,dest,row['mode']);assert dest.read_bytes()==(base/(row['name']+'-'+row['mode']+'.wasm')).read_bytes();replays+=1
        for opt in ('','-O3'):
            file=base/(row['name']+'-'+row['mode']+opt+'.wasm');r,ms=a.read(file);mod=h.w.parse(h.w.tool('wasm2wat',[file,'--fold-exprs']));mod.append(['export','"memory"',['memory','0']]);d=out/(file.stem+'-diagnostic.wasm');h.save(h.w.emit(mod),d);ap,old,new,cache,end,pages=h.layout(r);diagnostics.append({'file':str(d),'name':row['name'],'old':old,'end':end,'prefix':ap,'d':r['d']})
    (out/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2));check=subprocess.run(['node',str(h.HERE/'scratch.cjs'),str(out/'diagnostics.json')],capture_output=True,text=True,timeout=180);(out/'scratch.stdout.log').write_text(check.stdout);(out/'scratch.stderr.log').write_text(check.stderr)
    if check.returncode:raise RuntimeError(check.stderr)
    # N^2=0 does not imply universal convergence when inserted into residuals.
    n=1;f=[set(),set(),h.mul(h.var(n),h.add({()},h.var(n+1)))];badN=[0,0,0,4,0,2,1,0];err=[h.add(h.var(n+i),f[i]) for i in range(3)];maps=[h.add(f[i],h.sub(poly,err)) for i,poly in enumerate(p.anf(badN,3))];r={'n':n,'d':3,'depth':7,'maps':[[list(m) for m in sorted(poly)] for poly in maps]}
    bad=out/'known-nilpotent-counterexample.wasm';h.save(h.render(r),bad)
    try:attack.run(bad,out/'bad-recovered.wasm')
    except ValueError as e:rejection=str(e)
    else:raise AssertionError('Nonconvergent example accepted')
    mod=h.w.parse(h.w.tool('wasm2wat',[bad,'--fold-exprs']));old=h.layout(r)[1]
    # State 1 -> 6 -> 1. Return the state word even though run exports slot 2.
    for j in (0,1,2):
        text=f'(module (func (export "probe{j}") (result i32) (i32.store (i32.const {old}) (i32.const 1)) (i32.store (i32.const {old+4}) (i32.const 0)) (i32.store (i32.const {old+8}) (i32.const 0)) (drop (call 0 (i32.const 0))) (i32.load (i32.const {old+4*j}))))';mod.append(h.w.parse(text)[1])
    probe=out/'known-nilpotent-probe.wasm';h.save(h.w.emit(mod),probe);log=h.w.tool('wasm-interp',[probe,'--run-all-exports']);(out/'counterexample.log').write_text(log)
    for j,v in enumerate((0,1,1)):assert f'probe{j}() => i32:{v}' in log,log
    # A one-round counterfeit has a unique fixed point but no flush guarantee.
    r,_=a.read(base/'mix8-feedback.wasm');r['depth']=1;short=out/'insufficient-rounds.wasm';h.save(h.render(r),short)
    try:attack.run(short,out/'short-recovered.wasm')
    except ValueError as e:short_rejection=str(e)
    else:raise AssertionError('Insufficient rounds accepted')
    result={'byte_replays':replays,'SMT':proofs,'scratch':json.loads(check.stdout),'known_nilpotent_rejection':rejection,'known_nilpotent_after7':[0,1,1],'expected_fixedpoint':[0,0,0],'short_round_rejection':short_rejection}
    (out/'audit.json').write_text(json.dumps(result,indent=2));(out/'pins.json').write_text(json.dumps({str(f.relative_to(h.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2));print(json.dumps(result))

if __name__=='__main__':main(*sys.argv[1:])
