"""Actual upstream Wizer execution; explicitly separate unsupported inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime
CLI=ROOT/'.tools/state-witness-wasmtime-cli-v50.0.0/wasmtime.exe'
WAT=ROOT/'.tools/wabt-1.0.42/bin/wat2wasm.exe'
VALIDATE=ROOT/'.tools/wabt-1.0.42/bin/wasm-validate.exe'
def digest(data):return hashlib.sha256(data).hexdigest()
def command(args):
    run=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf8',timeout=60)
    return dict(command=[str(x) for x in args],returncode=run.returncode,stdout=run.stdout,stderr=run.stderr)

def sources():
    for active_first in (False,True):
        for nonzero_memory in (False,True):
            segments='(data $a (i32.const 0) "A") (data $p "XYZ")' if active_first else '(data $p "XYZ") (data $a (i32.const 0) "A")'
            initialize='i32.const 0 i32.const 99 i32.store8' if nonzero_memory else ''
            source=f'''(module (memory (export "memory") 1 2)
              {segments}
              (func (export "wizer-initialize") {initialize})
              (func (export "read") (result i32) i32.const 0 i32.load8_u)
              (func (export "passive") (result i32) i32.const 8 i32.const 1 i32.const 2 memory.init $p i32.const 8 i32.load8_u)
              (func (export "active_zero") i32.const 0 i32.const 0 i32.const 0 memory.init $a)
              (func (export "active_bounds") i32.const 0 i32.const 1 i32.const 0 memory.init $a))'''
            yield f'accepted-{int(active_first)}-{int(nonzero_memory)}',source,'accepted',['read','passive','active_zero','active_bounds','read']
    yield 'drop-init','''(module (memory (export "memory") 1) (data $p "X")
      (func (export "wizer-initialize") data.drop $p))''','unsupported-data.drop',[]
    yield 'drop-later','''(module (memory (export "memory") 1) (data $p "X")
      (func (export "wizer-initialize")) (func (export "later") data.drop $p))''','unsupported-data.drop',[]
    yield 'drop-unreachable','''(module (memory (export "memory") 1) (data $p "X")
      (func (export "wizer-initialize")) (func $hidden data.drop $p))''','unsupported-data.drop',[]
    yield 'table-later','''(module (table 1 funcref) (func $f) (elem $p func $f)
      (func (export "wizer-initialize"))
      (func (export "later") i32.const 0 i32.const 0 i32.const 1 table.init $p))''','unsupported-table.init',[]

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    records=[];accepted=[]
    for name,source,expected,actions in sources():
        (out/(name+'.wat')).write_text(source)
        original=out/(name+'.wasm');snapshot=out/(name+'-snapshot.wasm')
        build=command([WAT,out/(name+'.wat'),'-o',original]);assert build['returncode']==0,build
        run=command([CLI,'wizer',original,'-o',snapshot])
        if run['returncode']==0:actual='accepted'
        elif 'unsupported `data.drop` instruction' in run['stderr']:actual='unsupported-data.drop'
        elif 'unsupported `table.init` instruction' in run['stderr']:actual='unsupported-table.init'
        else:actual='unexpected-failure'
        item=dict(name=name,expected=expected,actual=actual,run=run)
        if actual=='accepted':
            validation=command([VALIDATE,snapshot]);assert validation['returncode']==0,validation
            accepted.append(dict(name=name,original=str(original.resolve()),snapshot=str(snapshot.resolve()),actions=actions))
            item['snapshotBytes']=snapshot.stat().st_size
        records.append(item)
    specification=dict(accepted=accepted)
    (out/'replay.json').write_text(json.dumps(specification,indent=2))
    node=command(['node',HERE/'wizer-comparison.mjs',out/'replay.json']);assert node['returncode']==0,node
    node_result=json.loads(node['stdout']);(out/'node.json').write_text(json.dumps(node_result,indent=2))
    engine=wasmtime.Engine();rows=[]
    for pair in accepted:
        runs=[]
        for side in ('original','snapshot'):
            store=wasmtime.Store(engine);module=wasmtime.Module.from_file(engine,pair[side]);instance=wasmtime.Instance(store,module,[]);exports=instance.exports(store)
            if side=='original':exports['wizer-initialize'](store)
            observations=[]
            for name in pair['actions']:
                try:result=dict(type='return',value=exports[name](store))
                except wasmtime.Trap:result=dict(type='trap')
                observations.append(dict(name=name,result=result,memorySha256=digest(bytes(exports['memory'].read(store)))))
            runs.append(observations)
        rows.append(dict(name=pair['name'],same=runs[0]==runs[1],runs=runs))
    assert rows==node_result['rows'],'Engine observations differ'
    summary=dict(cliVersion=command([CLI,'--version'])['stdout'].strip(),cases=records,
                 accepted=len(accepted),unsupported=sum(x['actual'].startswith('unsupported-') for x in records),
                 originalApiCallsPerEngine=sum(len(x['actions'])*2 for x in accepted),
                 observationPairsPerEngine=sum(len(x['actions']) for x in accepted),
                 initializersPerEngine=len(accepted),mismatchesPerEngine=sum(not x['same'] for x in rows),
                 contract='original after initializer vs pre-initialized output; same original API and public memory',
                 generalEquivalenceProof=False,naturalBug=False)
    assert all(x['actual']==x['expected'] for x in records) and summary['mismatchesPerEngine']==0
    (out/'wasmtime.json').write_text(json.dumps(dict(rows=rows),indent=2))
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    for name in ('wizer-comparison-plan.md','wizer-comparison.py','wizer-comparison.mjs','wasmtime-cli-fetch.py','wizer-source-fetch.py'):
        shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file() and p.name!='sha256.json'},indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('out',type=Path);main(parser.parse_args().out)
