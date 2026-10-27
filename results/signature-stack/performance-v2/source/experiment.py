"""Bounded validator differential tests and synthetic workloads; no remote targets."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime
CHECKER=ROOT/'.tools/signature-stack-target/release/signature-stack.exe'
WABT=ROOT/'.tools/wabt-1.0.42/bin/wasm-validate.exe'
TYPES=['i32','i64','f32','f64']
def const(t): return f'{t}.const 0'
def module(body,result='',locals=''):
    return f'(module (func {"(result "+result+")" if result else ""} {locals} {body}))'
def command(args):
    t=time.perf_counter();p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=60)
    return dict(args=[str(x) for x in args],code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def boundary_cases():
    return [
        ('empty',module(''),True),('result',module('i32.const 1','i32'),True),
        ('missing-result',module('','i32'),False),('extra',module('i32.const 0'),False),
        ('wrong-result',module('i64.const 0','i32'),False),('dead-result',module('unreachable','i32'),True),
        ('dead-wrong-push',module('unreachable i64.const 0','i32'),False),
        ('bottom-select',module('unreachable select','i64'),True),
        ('bottom-select-refines',module('unreachable i32.const 0 i32.const 0 select','i64'),False),
        ('v128-select',module('v128.const i32x4 0 0 0 0 v128.const i32x4 0 0 0 0 i32.const 0 select','v128'),True),
        ('typed-select',module('unreachable select (result i32)','i32'),True),
        ('dead-local-tee',module('unreachable local.tee 0','i64','(local i32)'),False),
        ('bad-local',module('unreachable local.get 1 drop','', '(local i32)'),False),
        ('local-get-set',module('i64.const 0 local.tee 0 local.set 0 local.get 0','i64','(local i64)'),True),
        ('if-no-else-ok',module('i32.const 7 i32.const 0 if (param i32) (result i32) end','i32'),True),
        ('if-no-else-bad',module('i32.const 0 if (result i32) i32.const 1 end','i32'),False),
        ('dead-if-no-else-bad',module('unreachable if (result i32) unreachable end','i32'),False),
        ('if-else-ok',module('i32.const 7 i32.const 0 if (param i32) (result i64) drop i64.const 1 else drop i64.const 2 end','i64'),True),
        ('if-else-extra',module('i32.const 0 if i32.const 1 else end'),False),
        ('duplicate-else',module('i32.const 0 if else else end'),False),
        ('else-block',module('block else end'),False),
        ('outer-stack-not-visible',module('i32.const 0 block drop end'),False),
        ('dead-inner-underflow',module('unreachable block drop end'),False),
        ('loop-param-label',module('i32.const 1 loop (param i32) (result i64) br 0 end','i64'),True),
        ('loop-wrong-label',module('i32.const 1 loop (param i32) (result i64) drop i64.const 0 br 0 end','i64'),False),
        ('br-if-refines',module('block (result i32) unreachable br_if 0 i64.add drop i32.const 0 end','i32'),False),
        ('br-if-ok',module('i32.const 8 block (param i32) (result i32) i32.const 0 br_if 0 end','i32'),True),
        ('br-depth-bad',module('unreachable br 1'),False),
        ('br-root',module('i32.const 1 br 0','i32'),True),
        ('return-dead-tail',module('i32.const 1 return drop','i32'),True),
        ('table-polymorphic',module('block (result i32) block (result i64) unreachable br_table 0 1 end drop i32.const 0 end','i32'),True),
        ('table-known-wrong',module('block (result i32) block (result i64) i64.const 0 i32.const 0 br_table 0 1 end drop i32.const 0 end','i32'),False),
        ('table-arity-wrong',module('block (result i32) block unreachable br_table 0 1 end i32.const 0 end','i32'),False),
        ('table-bottom-prefix',module('block (result i64 i32) block (result f32 i32) unreachable i32.const 7 i32.const 0 br_table 0 1 end drop drop i64.const 0 i32.const 0 end','i64 i32'),True),
        ('table-known-prefix',module('block (result i64 i32) block (result f32 i32) f32.const 0 i32.const 7 i32.const 0 br_table 0 1 end drop drop i64.const 0 i32.const 0 end','i64 i32'),False),
        ('call-import','(module (import "a" "b" (func $f (param i32 i64) (result f64))) (func (result f64) i32.const 0 i64.const 0 call $f))',True),
        ('call-dead', '(module (func (param i64) (result i32) unreachable call 0))',True),
        ('call-index',module('unreachable call 5'),False),
        ('start-bad','(module (func $f (param i32)) (start $f))',False),
        ('export-index','(module (export "f" (func 4)))',False),
        ('reference-unsupported','(module (func (result externref) ref.null extern))',None),
        ('memory-unsupported','(module (memory 1) (func i32.const 0 i32.load drop))',None),
    ]
def wide(width,reps,family='block',mixed=True):
    ts=[TYPES[i%4] if mixed else 'i32' for i in range(width)]
    vector=' '.join(ts);initial=' '.join(map(const,ts));drops=' drop'*width
    declarations=f'(type $v (func (param {vector}) (result {vector})))'
    helper=''
    if family=='alternating':
        other=[TYPES[(i+1)%4] for i in range(width)];v2=' '.join(other)
        declarations=f'(type $ab (func (param {vector}) (result {v2}))) (type $ba (func (param {v2}) (result {vector})))'
        helper=f'(func $ab (type $ab) '+ ' '.join(map(const,other))+f') (func $ba (type $ba) '+initial+')'
        step='call $ab call $ba'
    elif family=='call':
        helper=f'(func $id (type $v) '+ ' '.join(f'local.get {i}' for i in range(width))+')'
        step='call $id'
    elif family=='if':step='i32.const 0 if (type $v) else end'
    elif family=='br-if':step='block (type $v) i32.const 0 br_if 0 end'
    else:step='block (type $v) end'
    return f'(module {declarations} {helper} (func (export "run") {initial} '+(' '+step)*reps+drops+'))'
def generated_cases():
    rng=random.Random(261026)
    cases=[]
    for i in range(80):
        width=rng.randint(1,32);ts=[rng.choice(TYPES) for _ in range(width)]
        sig=' '.join(ts);body=' '.join(map(const,ts));locals=' '.join(TYPES)
        for _ in range(rng.randint(2,16)):
            top=ts[-1];choice=rng.randrange(6)
            if choice==0:body+=f' block (param {sig}) (result {sig}) end'
            elif choice==1:body+=f' i32.const 0 if (param {sig}) (result {sig}) else end'
            elif choice==2:body+=f' block (param {sig}) (result {sig}) i32.const 0 br_if 0 end'
            elif choice==3:body+=f' drop {const(top)}'
            elif choice==4:body+=f' local.set {TYPES.index(top)} local.get {TYPES.index(top)}'
            else:body+=f' {const(top)} i32.const 0 select'
        full=module(body+' drop'*width,locals=f'(local {locals})')
        cases.append((f'generated-valid-{i}',full,True))
        # Mutations may remain valid; expected class is assigned by differential
        # validators, never silently inferred from the mutation operator.
        # Mutate whole instructions, preserving text grammar and binary shape.
        mutation=rng.choice(['drop','i64.const 0','local.get 9','i32.add','unreachable','i32.const 1'])
        cases.append((f'generated-mutant-{i}',module(mutation+' '+body+' drop'*width,locals=f'(local {locals})'),'differential'))
    alphabet=['i32.const 0','i64.const 0','f32.const 0','f64.const 0','drop','select','unreachable',
              'i32.add','i64.eqz','local.get 0','local.set 1','br_if 0','return','nop']
    for i in range(160):
        body=' '.join(rng.choice(alphabet) for _ in range(rng.randint(1,32)))
        cases.append((f'random-{i}',module(body,locals='(local i32 i64)'),'differential'))
    return cases
def main(out):
    out.mkdir(parents=True,exist_ok=False);commands=[];rows=[];files=[]
    for name,wat,expected in boundary_cases()+generated_cases():
        text=out/(name+'.wat');path=out/(name+'.wasm');text.write_text(wat)
        try:path.write_bytes(wasmtime.wat2wasm(wat))
        except Exception as e:
            raise RuntimeError(f'generator error {name}: {e}')
        files.append(str(path.resolve()));rows.append(dict(name=name,path=str(path.resolve()),expected=expected,sha256=digest(path)))
    paths=out/'paths.json';paths.write_text(json.dumps(files))
    c=command(['node',HERE/'independent.mjs',paths]);commands.append(c);assert c['code']==0,c
    node=json.loads(c['stdout']);node_by={x['path']:x['valid'] for x in node['rows']}
    actual={}
    for k in range(0,len(files),25):
        c=command([CHECKER,'check',*files[k:k+25]]);commands.append(c);assert c['code']==0,c
        for line in c['stdout'].splitlines():
            row=json.loads(line);actual[row['path']]=row
    errors=[]
    for row in rows:
        c=command([WABT,row['path']]);commands.append(c)
        result=actual[row['path']];row.update(checker=result,node=node_by[row['path']],wabt=c['code']==0)
        stock=result['stock']['status']=='valid'
        if row['node']!=stock or row['wabt']!=stock or (result['stock-current']['status']=='valid')!=stock:errors.append(dict(name=row['name'],reason='reference disagreement'))
        expected=row['expected']
        if isinstance(expected,bool) and expected!=stock:errors.append(dict(name=row['name'],reason='hand/generated expected mismatch'))
        for mode in ['flat','segment','cached']:
            status=result[mode]['status']
            if expected is None:
                if status!='unsupported':errors.append(dict(name=row['name'],reason='unsupported category',mode=mode))
            elif status!=('valid' if stock else 'invalid'):errors.append(dict(name=row['name'],reason='kernel disagreement',mode=mode))
    summary=dict(cases=len(rows),reference_valid=sum(r['node'] for r in rows),unsupported=sum(r['expected'] is None for r in rows),errors=errors,
        node=node['node'],v8=node['v8'],python=sys.version,platform=platform.platform())
    (out/'rows.json').write_text(json.dumps(rows,indent=2));(out/'commands.json').write_text(json.dumps(commands,indent=2))
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    sources=[HERE/'experiment.py',HERE/'independent.mjs',HERE/'checker/src/main.rs',HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock',CHECKER]
    snapshots=out/'source';snapshots.mkdir()
    for p in sources:shutil.copyfile(p,snapshots/p.name)
    sources=list(snapshots.iterdir())
    (out/'manifest.json').write_text(json.dumps([dict(path=str(p.resolve()),sha256=digest(p)) for p in sources]+[dict(path=r['path'],sha256=r['sha256']) for r in rows],indent=2))
    print(json.dumps(summary,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);args=ap.parse_args();main(args.out)
