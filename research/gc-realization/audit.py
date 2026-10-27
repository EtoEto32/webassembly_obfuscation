"""Hash, regeneration, independent state-space and statistic audit for S artifacts."""
import argparse,json,statistics
from pathlib import Path
from realize import ROOT,HERE,generate,enumerated
from experiment import dump,digest,wt,fixtures
from benchmark import cases as benchcases
def main(out):
    out.mkdir(parents=True,exist_ok=False);base=ROOT/'results/gc-realization';errors=[];hashes=0;manifests=0
    for p in base.glob('*/manifest.json'):
        manifests+=1
        for r in json.loads(p.read_text()):
            if r.get('status')=='unavailable':continue
            f=Path(r['path']) if 'path' in r and Path(r['path']).is_absolute() else p.parent/r['file']
            hashes+=1
            if not f.exists() or digest(f)!=r['sha256']:errors.append(dict(kind='hash',path=str(f)))
    screen=base/'screen-v1';fx={f['name']:f for f in json.loads((screen/'cases.json').read_text())};rebuilt=0;states=0
    if set(f['name'] for f in fixtures())!=set(fx):errors.append(dict(kind='fixture-set'))
    for f in fx.values():
        ok,n=enumerated(f['model'],f['nodes']);states+=n
        if dict(reachable=ok,states=n)!=f['enumeration']:errors.append(dict(kind='enumeration',name=f['name']))
    for r in json.loads((screen/'generation.json').read_text()):
        if r['status']!='generated':continue
        f=fx[r['name']];g=generate(f['model'],f['nodes'],r['mode']);rebuilt+=1
        if wt.wat2wasm(g['wat'])!=(screen/r['file']).read_bytes():errors.append(dict(kind='binary',file=r['file']))
    perf=base/'performance-v4';summary=json.loads((perf/'summary.json').read_text());prs=json.loads((perf/'generation.json').read_text());guest=json.loads((perf/'guest.json').read_text());medians=0;perf_rebuilt=0;identical_pairs=0
    for mode,s in summary.items():
        rs=[r for r in prs if r['mode']==mode]
        for r in rs:
            medians+=1
            if statistics.median(r['samples_ms'])!=r['median_ms']:errors.append(dict(kind='process-median',mode=mode))
        if statistics.median(r['median_ms'] for r in rs)!=s['median_generation_ms']:errors.append(dict(kind='generation-median',mode=mode))
        for c in benchcases():
            g=generate(c['model'],c['nodes'],mode,return_nodes=True);stem=c['name']+'-'+mode
            for key,suffix in [('wat','.wasm'),('observer_wat','-observer.wasm')]:
                perf_rebuilt+=1
                if wt.wat2wasm(g[key])!=(perf/(stem+suffix)).read_bytes():errors.append(dict(kind='benchmark-binary',file=stem+suffix))
            vals=[]
            for r in guest:
                if r['mode']!=mode:continue
                cr=next(x for x in r['cases'] if x['file']==stem+'.wasm');medians+=1;value=statistics.median(cr['samples_ns']);vals.append(value)
                if value!=cr['median_ns']:errors.append(dict(kind='guest-process-median',file=stem))
            if statistics.median(vals)!=s['guest_case_medians_ns'][c['name']]:errors.append(dict(kind='guest-median',file=stem))
    for c in benchcases():
        for suffix in ['.wasm','-observer.wasm']:
            if (perf/(c['name']+'-staged'+suffix)).read_bytes()==(perf/(c['name']+'-dfs-staged'+suffix)).read_bytes():identical_pairs+=1
    protected=digest(ROOT/'paper/main.tex')=='7d31f76903832dc6923895a3342361349ddbeb646c863089f5ec2adfb22b851c'
    result=dict(manifests=manifests,hashed_files=hashes,rebuilt_main_binaries=rebuilt,recomputed_state_visits=states,rebuilt_benchmark_binaries=perf_rebuilt,benchmark_identical_pairs=identical_pairs,recomputed_medians=medians,paper_unchanged_this_turn=protected,errors=errors);dump(out/'report.json',result);print(json.dumps(result,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
