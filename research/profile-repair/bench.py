import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import prototype as p
import importlib.util
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('symbolic-audit.py'));audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

HERE=Path(__file__).resolve().parent


def main(source,optimized,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();(out/'wasm').mkdir()
    for name in ('bench.py','bench.cjs','prototype.py','symbolic-audit.py','performance-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    request=json.loads((source/'request.json').read_text());records=json.loads((source/'results.json').read_text())['rows']
    modes=('all','slice','independent','aware','manual');tasks=[(mode,rep) for mode in modes for rep in range(5)];random.Random(2026102422).shuffle(tasks);raw=[]
    bench={'directory':str(out/'wasm'),'inputs':request['inputs'],'rows':[]};validation=[]
    try:
        for row in records:
            name=row['name'];files={}
            for mode in modes[:-1]:
                file=name+'-'+mode+'-O3.wasm';shutil.copy2(optimized/file,out/'wasm'/file);files[mode]=file
            value=p.c(0)
            if name=='pair_equal_guard':value=p.c(1)
            elif name=='dead_site':value=p.g(0)
            elif name=='in_range':value=p.op('i32.and',p.g(0),p.c(255))
            elif name=='unconstrained_index':value=p.op('select',p.op('i32.and',p.g(0),p.c(255)),p.c(0),p.op('i32.lt_u',p.op('i32.and',p.g(1),p.c(255)),p.c(16)))
            mod=['module',['func',['export','"run"'],['param','i32','i32'],['result','i32'],value]]
            manual=out/'wasm'/(name+'-manual.wasm');p.compile_mod(mod,manual);files['manual']=manual.name
            eq=audit.equivalence(audit.evaluate(source/(name+'-source.wasm'),audit.z.BoolVal(False)),audit.evaluate(manual,audit.R));assert eq['status']=='unsat',(name,eq)
            validation.append({'name':name,**eq});bench['rows'].append({'name':name,'files':files})
        (out/'manual-validation.json').write_text(json.dumps(validation,indent=2),encoding='utf8')
        (out/'input.json').write_text(json.dumps(bench),encoding='utf8')
        for mode,rep in tasks:
            command=['node',str(HERE/'bench.cjs'),str(out/'input.json'),mode];run=subprocess.run(command,capture_output=True,text=True,timeout=60)
            raw.append({'mode':mode,'replicate':rep,'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr});(out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if run.returncode:raise RuntimeError(run.stderr)
        data=[json.loads(r['stdout']) for r in raw];rows=[]
        for row in records:
            record={'name':row['name']}
            for mode in modes:
                medians=[next(r['medianNs'] for r in process['rows'] if r['name']==row['name']) for process in data if process['mode']==mode]
                q=statistics.quantiles(medians,n=4,method='inclusive');record[mode]={'medianNs':statistics.median(medians),'q1':q[0],'q3':q[2],'processMedians':medians}
            rows.append(record)
        (out/'results.json').write_text(json.dumps({'processes':len(raw),'seed':2026102422,'rows':rows,'limitation':'Small mostly constant-output fixtures; manual simplifications independently checked. Weights in synthesis are logical site costs, not fitted runtime measurements.'},indent=2),encoding='utf8');print(json.dumps({'processes':len(raw),'rows':len(rows)}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('optimized',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.optimized.resolve(),a.output.resolve())
