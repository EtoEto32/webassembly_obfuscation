import argparse,json,re,subprocess
from pathlib import Path
import prototype as p
def load(d,f):return json.loads((d/f).read_text(encoding='utf-8'))
def main(data,replay,perf,verify,model,controls,out):
    data,replay,perf,verify,model,controls,out=map(Path,(data,replay,perf,verify,model,controls,out));out.mkdir(parents=True,exist_ok=False);a=load(data,'manifest.json');b=load(replay,'manifest.json');assert len(a)==len(b)==90;hashes=[]
    for x,y in zip(a,b):
        assert x['file']==y['file'] and x['term_match'] and y['term_match']
        for k,h in [('file','sha256'),('recovered','recovered_sha256')]:
            value=p.digest(data/x[k]);assert value==x[h]==y[h]==p.digest(replay/y[k]);hashes.append(dict(file=x[k],sha256=value))
        base=next(z for z in a if (z['n'],z['kind'],z['mode'],z['opt'])==(x['n'],x['kind'],'plain','raw'));assert x['recovered_sha256']==base['recovered_sha256']
    checks=load(data,'checks.json');assert checks==load(replay,'checks.json')==dict(wasm_calls=574830,cases_per_target=2129,mismatches=0,unexpected_traps=0,negative_witnesses=9)
    assert load(data,'negative.json')==load(replay,'negative.json')
    assert load(verify,'summary.json')==dict(files=180,checks=1260,all_pass=True)
    vr=load(verify,'records.json');assert len(vr)==180
    for r in vr:assert r['sha256']==p.digest(data/r['file']) and r['checks']==7
    mod=load(model,'summary.json');assert (mod['carry_save_comparisons'],mod['partition_comparisons'],mod['mismatches'],len(mod['profile_refusals']))==(37448,87380,0,4)
    cc=load(controls,'summary.json');assert cc['targets']==cc['term_matches']==40 and cc['wasm_calls']==255480 and cc['mismatches']==0 and len(cc['refusals'])==2
    cr=load(controls,'manifest.json')
    for r in cr:
        assert r['term_match'] and p.digest(controls/r['file'])==r['sha256'] and p.digest(controls/r['recovered'])==r['recovered_sha256']
        base=next(z for z in cr if (z['n'],z['mode'],z['opt'])==(r['n'],'plain','raw'));assert r['recovered_sha256']==base['recovered_sha256']
    for r in load(replay,'sources.json'):assert p.digest(p.ROOT/r['path'])==r['sha256']==p.digest(replay/'sources'/r['snapshot'])
    native=load(perf,'native.json');assert len(native)==135
    for r in native:assert (r['warmup'],r['batch'],r['repeats'])==(50000,20000,9) and len(r['ns'])==9 and r['linear_memory_bytes']==0
    for n in (16,32,64):
        for k in range(3):assert len({r['checksum'] for r in native if (r['n'],r['kind'])==(n,k)})==1
    protocol=load(perf,'protocol.json');assert protocol['bench_sha256']==p.digest(Path(__file__).parent/'bench.cjs') and protocol['extractor_sha256']==p.digest(Path(__file__).parent/'prototype.py')
    assert len(load(perf,'analysis.json'))==90 and protocol['analysis_runs']==450
    env=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model,logical_cpus:require("os").cpus().length}))'],text=True));p.save(out/'environment.json',env);p.save(out/'binary-hashes.json',hashes)
    links=[]
    for f in Path(__file__).parent.glob('*.md'):
        for s in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if not s.startswith(('https:','http:','#')):links.append((f,f.parent/s.split('#')[0]))
    summary=dict(passed=False,targets=90,recovered=90,reproduced_binaries=len(hashes),canonical_recovery_matches=90,main_wasm_calls=574830,control_targets=40,control_wasm_calls=255480,binaryen_checks=1260,model_comparisons=37448+87380,negative_witnesses=9,fresh_processes=135,analysis_runs=450,links=len(links),goal_complete=False)
    p.save(out/'summary.json',summary)
    for f,target in links:assert target.exists(),(f,target)
    summary['passed']=True;p.save(out/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for s in ('data','replay','performance','verify','model','controls','output'):a.add_argument(s)
    v=a.parse_args();main(v.data,v.replay,v.performance,v.verify,v.model,v.controls,v.output)
