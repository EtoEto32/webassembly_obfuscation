import argparse,json,re,subprocess
from pathlib import Path
import prototype as p
def load(d,f):return json.loads((d/f).read_text(encoding='utf-8'))
def main(data,replay,perf,verify,model,report,graph,out):
    data,replay,perf,verify,model,report,graph,out=map(Path,(data,replay,perf,verify,model,report,graph,out));out.mkdir(parents=True,exist_ok=False);a=load(data,'manifest.json');b=load(replay,'manifest.json');assert len(a)==len(b)==72;hashes=[]
    for x,y in zip(a,b):
        assert x['file']==y['file']
        for k,h in [('file','sha256'),('probe','probe_sha256')]+([('recovered','recovered_sha256'),('recovered_probe','recovered_probe_sha256')] if 'recovered' in x else []):
            value=p.digest(data/x[k]);assert value==x[h]==y[h]==p.digest(replay/y[k]);hashes.append(dict(file=x[k],sha256=value))
        if 'recovered' in x:assert p.digest(data/x['source'])==x['recovered_sha256']
    checks=load(data,'checks.json');assert checks==load(replay,'checks.json');assert checks['wasm_calls']==34560 and checks['traps']==2160 and checks['mismatches']==0 and checks['negative_witnesses']==9
    assert load(data,'negative.json')==load(replay,'negative.json')
    assert load(verify,'summary.json')==dict(files=108,checks=756,all_pass=True)
    mod=load(model,'summary.json');assert mod['mismatches']==0 and len(mod['profile_refusals'])==4 and len(mod['recovery_refusals'])==2
    for r in load(replay,'sources.json'):assert p.digest(p.ROOT/r['path'])==r['sha256']==p.digest(replay/'sources'/r['snapshot'])
    native=load(perf,'native.json');assert len(native)==216
    for r in native:assert (r['warmup'],r['batch'],r['repeats'])==(20000,2000,9) and len(r['ns'])==9 and r['linear_memory_bytes']==65536
    for n in (4,8,16):
        for k in range(3):
            for t in (8,256):assert len({r['checksum'] for r in native if (r['n'],r['kind'],r['rounds'])==(n,k,t)})==1
    protocol=load(perf,'protocol.json');assert protocol['bench_sha256']==p.digest(Path(__file__).parent/'bench.cjs') and protocol['extractor_sha256']==p.digest(Path(__file__).parent/'prototype.py')
    assert len(load(perf,'analysis.json'))==36 and protocol['analysis_runs']==252
    assert all(r['bitselects']==r['expected'] for r in load(report,'census.json'))
    gs=load(graph,'summary.json');gr=load(graph,'records.json');assert len(gr)==gs['targets']==gs['byte_identical_to_source']==36 and gs['runs']==252 and gs['mask_values_used'] is False
    assert gs['source_sha256']==p.digest(Path(__file__).parent/'phase_graph.py')
    for r in gr:
        target=next(x for x in a if x['file']==r['file']);assert len(r['runs'])==7
        assert p.digest(graph/r['recovered'])==r['recovered_sha256']==p.digest(data/target['source'])
        for run in r['runs']:
            assert run['mask_values_used'] is False and all(run[k]==target[k] for k in ('n','kind','r','coeff'))
    env=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model,logical_cpus:require("os").cpus().length}))'],text=True));p.save(out/'environment.json',env);p.save(out/'binary-hashes.json',hashes)
    links=[]
    for f in Path(__file__).parent.glob('*.md'):
        for s in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
            if not s.startswith(('https:','http:','#')):links.append((f,f.parent/s.split('#')[0]))
    summary=dict(passed=False,targets=72,recovered=36,reproduced_binaries=len(hashes),byte_identical_to_source=36,wasm_calls=34560,expected_traps=2160,binaryen_checks=756,model_comparisons=mod['model_comparisons'],negative_witnesses=9,fresh_processes=216,analysis_runs=252,graph_recoveries=36,graph_analysis_runs=252,links=len(links),goal_complete=False)
    p.save(out/'summary.json',summary)
    for f,target in links:assert target.exists(),(f,target)
    summary['passed']=True;p.save(out/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for s in ('data','replay','performance','verify','model','report','graph','output'):a.add_argument(s)
    v=a.parse_args();main(v.data,v.replay,v.performance,v.verify,v.model,v.report,v.graph,v.output)
