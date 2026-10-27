"""Cost of one-plan authorization vs correct separate projections."""
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
def main(source,generated,out):
    inputs={}
    for name,directory in [('component',source),('plan',generated)]:
        hashes=json.loads((directory/'sha256.json').read_text())
        for relative,digest in hashes.items():assert sha(directory/relative)==digest
        inputs[name]={'path':str(directory),'hashes':hashes}
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('effect-performance.py','effect-performance.cjs','effect-performance-plan.md','effect-engine.cjs','fence-runtime.cjs'):
        shutil.copy2(HERE/name,out/'sources'/name)
    modes=['separate-manual','separate-generated','plan-generated'];jobs=[(rep,mode) for rep in range(5) for mode in modes];random.Random(2026102402).shuffle(jobs)
    (out/'jobs.json').write_text(json.dumps(jobs),encoding='utf8');results=[]
    for rep,mode in jobs:
        target=out/(str(rep)+'-'+mode+'.json')
        r=subprocess.run(['node',str(HERE/'effect-performance.cjs'),str(source),str(generated),mode,str(target)],capture_output=True,text=True,timeout=60)
        (out/(target.stem+'.log')).write_text(r.stdout+r.stderr,encoding='utf8');assert r.returncode==0,r.stderr
        results.append({'rep':rep,**json.loads(target.read_text())})
    rows=[]
    for name in [r['name'] for r in results[0]['rows']]:
        med=lambda x:statistics.median(next(r['samples_us'] for r in x['rows'] if r['name']==name))
        baseline={x['rep']:med(x) for x in results if x['mode']=='separate-manual'}
        for mode in modes:
            chosen=[x for x in results if x['mode']==mode];samples=[med(x) for x in chosen];q=statistics.quantiles(samples,n=4,method='inclusive')
            ratios=[med(x)/baseline[x['rep']] for x in chosen]
            rows.append({'case':name,'mode':mode,'median_us':statistics.median(samples),'iqr_us':q[2]-q[0],
                'processMedians_us':samples,'pairedRatios':ratios,'medianRatioToManual':statistics.median(ratios)})
    summary={'processes':len(results),'rows':rows,'inputs':inputs,'correctnessPerProcess':{'decisions':36,'unsafe':0,'falseRejects':0},
        'scope':'6 cases; two objects; same local-file executor; page cache warm; no fsync; repeated 36 correctness conditions are not 540 distinct conditions'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    lines=['# 同一処理計画と分離した依存抽出の比較','','5 process中央値、単位µs。1 KiBの入力ファイル、OS cacheあり、fsyncなし。',
      '','|case|mode|median|IQR|ratio/manual|','|---|---|---:|---:|---:|']
    lines+=['|{case}|{mode}|{median_us:.3f}|{iqr_us:.3f}|{medianRatioToManual:.3f}|'.format(**r) for r in rows]
    lines+=['','全方式で36失効条件の誤判定0。新しい安全原理、第三者アプリケーションでの効果、汎用WIT対応を示す試験ではない。']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'processes':len(results),'planRatios':[r['medianRatioToManual'] for r in rows if r['mode']=='plan-generated']}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('component',type=Path);ap.add_argument('plan',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.component.resolve(),a.plan.resolve(),a.output.resolve())
