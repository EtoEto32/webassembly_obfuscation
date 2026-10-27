import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import prototype as p

HERE=Path(__file__).resolve().parent
WRAPPER='''(module (func (export "bench") (param i32) (result i32) (local i32 i32)
 (local.set 1 (i32.const 123456789))
 (block (loop
  (br_if 1 (i32.eqz (local.get 0)))
  (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
  (local.set 2 (i32.add (local.get 2) (call 0 (local.get 1) (i32.rotr (local.get 1) (i32.const 9)))))
  (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (local.get 2)))'''


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();(out/'wasm').mkdir()
    for name in ('internal-bench.py','internal-bench.cjs','prototype.py','performance-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    source_input=json.loads((source/'input.json').read_text());request={'directory':str(out/'wasm'),'rows':[]};raw=[]
    try:
        for row in source_input['rows']:
            files={}
            for mode in ('all','aware','manual'):
                mod=p.w.parse(p.w.tool('wasm2wat',[source/'wasm'/row['files'][mode],'--fold-exprs']))
                mod.append(copy.deepcopy(p.w.parse(WRAPPER)[1]));dest=out/'wasm'/(row['name']+'-'+mode+'.wasm');p.compile_mod(mod,dest);files[mode]=dest.name
            files['allCopy']=files['all'];request['rows'].append({'name':row['name'],'files':files})
        (out/'input.json').write_text(json.dumps(request),encoding='utf8')
        for replicate in range(7):
            cmd=['node','--no-liftoff',str(HERE/'internal-bench.cjs'),str(out/'input.json'),str(replicate)];run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            raw.append({'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr});(out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if run.returncode:raise RuntimeError(run.stderr)
        data=[json.loads(r['stdout']) for r in raw];rows=[]
        for item in request['rows']:
            per_process=[next(r for r in process['rows'] if r['name']==item['name']) for process in data];row={'name':item['name']}
            for mode in ('all','aware','manual','allCopy'):
                medians=[r['medians'][mode] for r in per_process];q=statistics.quantiles(medians,n=4,method='inclusive');row[mode]={'medianNs':statistics.median(medians),'q1':q[0],'q3':q[2],'processMedians':medians}
            row['pairedAwareAll']=[r['medians']['aware']/r['medians']['all'] for r in per_process]
            row['pairedCopyAll']=[r['medians']['allCopy']/r['medians']['all'] for r in per_process];rows.append(row)
        (out/'results.json').write_text(json.dumps({'processes':7,'rows':rows,'note':'200000 internal calls per sample, 15 paired randomized rounds, two warmups, optimizing compiler forced. Same-binary allCopy calibration. Synthetic pure kernels.'},indent=2),encoding='utf8');print(json.dumps({'processes':7,'rows':len(rows)}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
