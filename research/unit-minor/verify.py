"""Audit saved evidence, producer snapshots and the documented local links."""
import ast
import json
import re
import subprocess
from pathlib import Path
import prototype as p


def run():
    base=p.ROOT/'results/invention-20261022'
    dirs={k:base/v for k,v in dict(main='unit-minor-v2',audit='unit-minor-audit-v1',runtime='unit-minor-runtime-v2',report='unit-minor-report-v1').items()}
    counts={}
    for name,d in dirs.items():
        pins=json.loads((d/'pins.json').read_text(encoding='utf-8'))
        for rel,h in pins.items():
            assert p.digest(d/rel)==h,(name,rel)
        counts[name]=len(pins)
    for f,h in json.loads((dirs['report']/'input-pins.json').read_text(encoding='utf-8')).items():
        assert p.digest(f)==h,f
    producer_files={
      'main':['prototype.py','recover.py','run.py','check.cjs','kernel.wat'],
      'audit':['prototype.py','recover.py','run.py','audit.py','kernel.wat'],
      'runtime':['prototype.py','recover.py','run.py','performance.py','bench.cjs','kernel.wat']}
    producer_checks=[]
    for name,files in producer_files.items():
        for f in files:
            assert p.digest(dirs[name]/('source-'+f))==p.digest(Path(__file__).with_name(f)),(name,f)
            producer_checks.append([name,f])
    checks=json.loads((dirs['main']/'checks.json').read_text())
    assert checks['positiveConditions']==42 and checks['positiveCalls']==214032 and checks['inputs']==5096
    assert all(r['traps']==0 and (r['mismatch']>0 if r['negative'] else r['mismatch']==0) for r in checks['results'])
    analysis=json.loads((dirs['main']/'analysis.json').read_text())
    assert len(analysis)==18 and all(x['status']=='recovered' and x['parity_inputs_certified']==8 for x in analysis)
    replay=json.loads((dirs['audit']/'replay.json').read_text())
    assert len(replay)==42 and all(x['byte_equal'] for x in replay)
    controls=json.loads((dirs['audit']/'controls.json').read_text())
    assert len(controls)==9 and all(x['status']=='rejected' for x in controls)
    assert next(x for x in controls if x['file']=='insufficient-rank.wasm')['runtime']['trapped']
    runtime=json.loads((dirs['runtime']/'runtime.json').read_text())
    assert len(runtime)==45 and sum(len(x['measurement']['batches']) for x in runtime)==405
    assert all(x['measurement']['warmup']==16384 for x in runtime)
    for name in ('bilinear','horner','product'):
        assert len({x['measurement']['verification'] for x in runtime if x['name']==name})==1
    syntax=[]
    for f in Path(__file__).parent.glob('*.py'):
        ast.parse(f.read_text(encoding='utf-8'),filename=str(f)); syntax.append(f.name)
    for f in Path(__file__).parent.glob('*.cjs'):
        subprocess.run(['node','--check',str(f)],capture_output=True,text=True,check=True); syntax.append(f.name)
    links=[]
    for f in Path(__file__).parent.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'): continue
            q=(f.parent/target.split('#')[0]).resolve(); assert q.exists(),(str(f),target); links.append([f.name,target])
    common=p.ROOT/'research/connectivity-elimination/prototype.py'
    facts=json.loads((dirs['report']/'report.json').read_text())['facts']
    assert facts['positive_calls']==214032 and facts['recoveries']==18 and facts['regenerated']==42
    assert facts['interpreter_calls']==336 and facts['model_cases']==7488 and facts['short_batches']==25
    output=base/'unit-minor-verification-v1.json'
    if output.exists(): raise FileExistsError(output)
    p.save(output,dict(status='passed',pin_checks=counts,producer_checks=producer_checks,syntax=syntax,local_links=links,
                       facts=facts,common_parser=dict(path=str(common),sha256=p.digest(common)),
                       source_hashes={f.name:p.digest(f) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.cjs','.wat','.md')}))
    print(json.dumps(dict(status='passed',pin_checks=counts,producer_checks=len(producer_checks),syntax=len(syntax),local_links=len(links))))


if __name__=='__main__': run()
