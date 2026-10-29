"""Fresh-process measurements; performance and permission precision are separate."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def median(xs):return statistics.median(xs)
def main(source,out):
    expected=json.loads((source/'sha256.json').read_text())
    for relative,digest in expected.items():assert sha(source/relative)==digest
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('fence-runtime.cjs','fence-performance.py','fence-performance.cjs','fence-performance-plan.md'):
        shutil.copy2(HERE/name,out/'sources'/name)
    modes=('generated-operation','manual-operation','generated-object','generated-global')
    jobs=[(rep,mode) for rep in range(5) for mode in modes];random.Random(20261024).shuffle(jobs)
    (out/'jobs.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
    results=[]
    for rep,mode in jobs:
        target=out/(str(rep)+'-'+mode+'.json')
        r=subprocess.run(['node',str(HERE/'fence-performance.cjs'),str(source),mode,str(target)],capture_output=True,text=True,timeout=60)
        (out/(target.stem+'.log')).write_text(r.stdout+r.stderr,encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        results.append({'rep':rep,**json.loads(target.read_text())})
    rows=[]
    for name in [r['name'] for r in results[0]['rows']]:
        baseline={x['rep']:median(next(r['samples_us'] for r in x['rows'] if r['name']==name)) for x in results if x['mode']=='manual-operation'}
        for mode in modes:
            chosen=[x for x in results if x['mode']==mode]
            samples=[median(next(r['samples_us'] for r in x['rows'] if r['name']==name)) for x in chosen]
            ratios=[samples[i]/baseline[x['rep']] for i,x in enumerate(chosen)]
            quart=statistics.quantiles(samples,n=4,method='inclusive')
            rows.append({'case':name,'mode':mode,'median_us':median(samples),'iqr_us':quart[2]-quart[0],
                         'processMedians_us':samples,'medianRatioToManual':median(ratios),'pairedRatios':ratios})
    precision=[]
    for mode in modes:
        chosen=[x for x in results if x['mode']==mode]
        assert len({(x['unsafe'],x['falseRejects'],x['decisions']) for x in chosen})==1
        x=chosen[0];precision.append({k:x[k] for k in ('mode','unsafe','falseRejects','decisions')})
    summary={'processes':len(results),'rows':rows,'precisionPerProcess':precision,
      'source':str(source),'sourceSha256':json.loads((source/'sha256.json').read_text()),
      'scope':'correctness events are repeated in each process, not independent new scenarios; two distinct resources only'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    lines=['# A: 実Component境界の性能','', '5 process中央値。手書き方式に対する時間比。単位µs。','',
      '|case|mode|median|IQR|ratio/manual|','|---|---|---:|---:|---:|']
    lines += ['|{case}|{mode}|{median_us:.3f}|{iqr_us:.3f}|{medianRatioToManual:.3f}|'.format(**r) for r in rows]
    lines += ['','|mode|unsafe|false rejects|scenarios|','|---|---:|---:|---:|']
    lines += ['|{mode}|{unsafe}|{falseRejects}|{decisions}|'.format(**r) for r in precision]
    lines += ['','同じ2 resourceを繰り返すlistであり、64独立資源ではない。RSSはruntime込みのprocess指標。新規性の証拠ではない。']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'processes':len(results),'precision':precision}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
