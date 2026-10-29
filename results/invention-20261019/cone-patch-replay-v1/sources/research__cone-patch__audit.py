"""Audit reproducibility, negative controls, timing protocol and local links."""
import argparse,json,re,statistics,subprocess
from pathlib import Path
import prototype as p

def load(d,n):return json.loads((d/n).read_text(encoding='utf-8'))

def main(data,replay,perf,verify,model,exposure,report,out):
    data,replay,perf,verify,model,exposure,report,out=map(Path,(data,replay,perf,verify,model,exposure,report,out))
    out.mkdir(parents=True,exist_ok=False);a=load(data,'manifest.json');b=load(replay,'manifest.json');hashes=[]
    assert len(a)==len(b)==48
    for x,y in zip(a,b):
        assert x['file']==y['file']
        for key,h in [('file','sha256'),('probe','probe_sha256')]:
            value=p.digest(data/x[key]);assert value==x[h]==y[h]==p.digest(replay/y[key])
            hashes.append(dict(file=x[key],sha256=value))
    checks=load(data,'checks.json');assert checks==load(replay,'checks.json')
    assert checks['wasm_calls']==32256 and checks['traps']==9216 and checks['mismatches']==0 and checks['attack_snapshots']==36
    negative=load(data,'negative.json');assert negative==load(replay,'negative.json') and len(negative)==6
    assert all(r['witness']['name']=='peek' and r['witness']['expected']!=r['witness']['got'] for r in negative)
    assert load(verify,'summary.json')==dict(files=48,binaryen_checks=336,all_pass=True)
    ms=load(model,'summary.json');assert ms['scalar_model_comparisons']==202752 and ms['mismatches']==0 and len(ms['refusals'])==5
    assert load(exposure,'summary.json')==dict(snapshots=96,required_reads_decoded=True)
    assert all(r['vector_multiplies']==r['expected'] for r in load(report,'census.json'))
    native=load(perf,'native.json');assert len(native)==216
    for r in native:assert (r['warmup'],r['batch'],r['repeats'])==(100000,50000,9) and len(r['ns'])==9 and r['linear_memory_bytes']==65536
    for n in (8,32,128):
        for k in ('bump','coupled','spread'):
            assert len({r['checksum'] for r in native if r['file'].startswith('n'+str(n)+'-') and r['kernel']==k})==1
    analysis=load(perf,'analysis.json');assert len(analysis)==36 and all(r['recovered'] and len(r['runs'])==7 for r in analysis)
    for r in load(replay,'sources.json'):assert p.digest(p.ROOT/r['path'])==r['sha256']==p.digest(replay/'sources'/r['snapshot'])
    timing=[]
    for r in load(perf,'summary.json'):
        z=r['process_medians_ns'];timing.append(dict(file=r['file'],kernel=r['kernel'],minimum_ns=min(z),median_ns=statistics.median(z),maximum_ns=max(z),max_over_min=max(z)/min(z)))
    links=0
    for f in Path(__file__).parent.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if target.startswith(('http:','https:','#')):continue
            assert (f.parent/target.split('#')[0]).exists(),(f,target);links+=1
    env=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model,logical_cpus:require("os").cpus().length}))'],text=True))
    p.save(out/'runtime-environment.json',env);p.save(out/'binary-hashes.json',hashes);p.save(out/'timing-spread.json',timing)
    summary=dict(passed=True,reproduced_targets=48,reproduced_probes=48,main_calls=32256,expected_traps=9216,binaryen_checks=336,scalar_model_comparisons=202752,performance_processes=216,analysis_runs=252,recovered_snapshots=36,negative_witnesses=6,local_links=links,goal_complete=False)
    p.save(out/'summary.json',summary);print(json.dumps(summary))

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for name in ('data','replay','performance','verify','model','exposure','report','output'):a.add_argument(name)
    v=a.parse_args();main(v.data,v.replay,v.performance,v.verify,v.model,v.exposure,v.report,v.output)
