"""Verify bounded Q artifacts and rebuild WAT; does not audit the whole repo."""
import argparse,hashlib,json,statistics,subprocess,tempfile
from pathlib import Path
from oracle import ROOT,w
from fixtures import fixtures
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
    out.mkdir(parents=True,exist_ok=False);base=ROOT/'results/choice-scope';errors=[];hashed=0;rebuilt=0
    groups=['screen-v1','screen-v2','independent-v1','independent-v2','minimal-v1','performance-v1','performance-v2']
    for group in groups:
        p=base/group;manifest=json.loads((p/'manifest.json').read_text())
        for name,h in manifest.items():
            hashed+=1
            if sha(p/name)!=h:errors.append('hash '+group+'/'+name)
    prior_count=0
    for group in ('priors-v2','priors-v3'):
        p=base/group
        for row in json.loads((p/'manifest.json').read_text()):
            if row['status']=='downloaded':
                prior_count+=1
                if sha(p/row['file'])!=row['sha256']:errors.append('prior '+row['file'])
    for group in ('screen-v1','screen-v2','minimal-v1','independent-v1','independent-v2'):
        for p in (base/group).glob('*.wat'):
            dst=out/(group+'-'+p.stem+'.wasm');w.tool('wat2wasm',[p,'--enable-all','-o',dst]);rebuilt+=1
            if dst.read_bytes()!=p.with_suffix('.wasm').read_bytes():errors.append('rebuild '+str(p))
    generated=0
    for fixture in fixtures():
        for group in ('screen-v1','screen-v2'):
            if (base/group/(fixture['name']+'.wat')).read_text()!=fixture['wat']:errors.append('generator '+fixture['name'])
            generated+=1
    source_equivalence={f.name:sha(f)==sha(base/'screen-v2'/f.name) for f in (base/'screen-v1').glob('*.wasm')}
    if not all(source_equivalence.values()):errors.append('screen bytes differ')
    medians=0
    for group in ('performance-v1','performance-v2'):
        p=base/group;rows=json.loads((p/'processes.json').read_text());summary=json.loads((p/'summary.json').read_text())
        for r in rows:
            if r['code']==0:
                medians+=1
                if statistics.median(r['millisecondsPerCase'])!=r['medianMillisecondsPerCase']:errors.append('process median '+group)
        for mode,s in summary.items():
            vals=[r['medianMillisecondsPerCase'] for r in rows if r['mode']==mode and r['code']==0];medians+=1
            if statistics.median(vals)!=s['medianOfProcessMedians']:errors.append('group median '+group+'/'+mode)
    traces=json.loads((base/'independent-v2/traces.json').read_text());classification={}
    for mode in ('joint','pointwise','independent-site','enumerated'):
        rs=[r for r in traces if r['mode']==mode]
        classification[mode]=dict(legal=sum(r['expected_legal'] for r in rs),illegal=sum(not r['expected_legal'] for r in rs),accepted_illegal=sum(not r['expected_legal'] and r['status']=='sat' for r in rs),rejected_legal=sum(r['expected_legal'] and r['status']=='unsat' for r in rs),unknown=sum(r['status']=='unknown' for r in rs))
    report=dict(manifests=len(groups),file_hashes=hashed,primary_source_hashes=prior_count,wat_rebuilds=rebuilt,generator_text_checks=generated,screen_binary_byte_comparisons=source_equivalence,median_recomputations=medians,classification=classification,errors=errors,
                sources={g:sha(base/g/'manifest.json') for g in groups},paper_hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'paper/main.tex',ROOT/'paper/README.md')})
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('sources','screen_binary_byte_comparisons','paper_hashes')}))
    if errors:raise SystemExit(1)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();main(a.out.resolve())
