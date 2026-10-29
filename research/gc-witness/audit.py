"""Verify saved data hashes and re-emit every successful controlled fixture."""
import argparse,json,hashlib,statistics
from pathlib import Path
from experiment import ROOT,HERE,wt,dump,digest
from witness import generate
def main(out):
    out.mkdir(parents=True,exist_ok=False);base=ROOT/'results/gc-witness';errors=[];checked=0;manifests=0;prior_files=0
    for p in sorted(base.glob('*/manifest.json')):
        records=json.loads(p.read_text());manifests+=1
        for r in records:
            if 'path' in r:file=Path(r['path'])
            elif r['status']=='downloaded':file=p.parent/r['file'];prior_files+=1
            else:continue
            checked+=1
            if not file.exists() or digest(file)!=r['sha256']:errors.append(dict(kind='hash',file=str(file)))
    source=base/'screen-v1';models={m['name']:m['model'] for m in json.loads((source/'models.json').read_text())};rows=json.loads((source/'generation.json').read_text());rebuilt=0;pairs=0
    bykey={(r['name'],r['task'],r['mode']):r for r in rows}
    for r in rows:
        if r['status']!='generated':continue
        g=generate(models[r['name']],r['target'],r['path'],r['mode'],node_budget=2048,depth_budget=64);data=wt.wat2wasm(g['wat']);rebuilt+=1
        if data!=(source/r['file']).read_bytes():errors.append(dict(kind='binary-rebuild',file=r['file']))
        if r['mode']=='worklist':
            m=bykey[r['name'],r['task'],'memo'];pairs+=1
            if data!=(source/m['file']).read_bytes():errors.append(dict(kind='memo-binary',file=r['file']))
    perf=base/'performance-v1';prs=json.loads((perf/'rows.json').read_text());sm=json.loads((perf/'summary.json').read_text());medians=0
    for mode,s in sm.items():
        vals=[]
        for r in prs:
            if r['mode']==mode:
                value=statistics.median(r['batch_ms_per_plan']);medians+=1;vals.append(value)
                if value!=r['median_ms_per_plan']:errors.append(dict(kind='process-median',mode=mode))
        if statistics.median(vals)!=s['median_ms']:errors.append(dict(kind='aggregate-median',mode=mode))
    protected={'paper/main.tex':'77c1815502634c4ee555d454eaeff469035ffb7b8391233de1469aea7e1f724e','paper/README.md':'10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'}
    status={p:digest(ROOT/p)==h for p,h in protected.items()}
    result=dict(manifests=manifests,hashed_files=checked,downloaded_priors=prior_files,rebuilt_binaries=rebuilt,memo_worklist_identical_pairs=pairs,recomputed_process_medians=medians,unrelated_files_unchanged=status,errors=errors)
    dump(out/'report.json',result);print(json.dumps(result,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
