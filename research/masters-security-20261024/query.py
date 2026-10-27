"""Post-callback query contract benchmark; reuse statistical reporting only."""
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
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('query.py','query.cjs','query-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
    modes=('full','materialize','segments','manual');schedule=[(i,m) for i in range(5) for m in modes]
    random.Random(20261024).shuffle(schedule);runs={}
    (out/'schedule.json').write_text(json.dumps(schedule,indent=2),encoding='utf8')
    for rep,mode in schedule:
        dest=out/f'{rep}-{mode}.json';r=subprocess.run(['node',str(HERE/'query.cjs'),str(source),mode,str(dest)],capture_output=True,text=True,timeout=90)
        assert r.returncode==0,r.stderr;runs[rep,mode]=json.loads(dest.read_text())
    stats=[]
    for j in range(8):
        baseline=[statistics.median(runs[i,'full']['entries'][j]['samples_us']) for i in range(5)]
        for mode in modes:
            es=[runs[i,mode]['entries'][j] for i in range(5)]
            for i,e in enumerate(es):assert e['checksums']==runs[i,'full']['entries'][j]['checksums']
            mids=[statistics.median(e['samples_us']) for e in es];q=statistics.quantiles(mids,n=4,method='inclusive')
            ratios=[v/b for v,b in zip(mids,baseline)]
            stats.append({'fixture':es[0]['fixture'],'mode':mode,'processMedians_us':mids,'median_us':statistics.median(mids),
             'iqr_us':[q[0],q[2]],'pairedRatios':ratios,'medianRatio':statistics.median(ratios),
             'retainedPayloadBytes':es[0]['retainedPayloadBytes'],'postCallbackPayloadBytes':es[0]['postCallbackPayloadBytes']})
    (out/'summary.json').write_text(json.dumps({'stats':stats,'sourceManifestSha256':sha(source/'manifest.json'),'processes':20,'queriesPerInvocation':16},indent=2),encoding='utf8')
    lines=['# 復帰後の位置queryの実測','','5独立process反復。比較する4方式は各16byte値を返す。位置はcallback後にcallerから取得。','','|fixture|方式|us/call|全コピー比|','|---|---|---:|---:|']
    for r in stats:lines.append('|%s|%s|%.3f|%.3f|'%(r['fixture'],r['mode'],r['median_us'],r['medianRatio']))
    lines+=['','全8KiBのhashは計算しない。単一checksumを前倒しする方式はこのAPIを満たさない。事前に位置が既知なら、その位置だけを保存する方式が有力である。',
            '自作microbenchmarkであり、実アプリケーション採用や特許新規性を確立するものではない。IQR・全反復・payload量はsummary.json。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'processes':20,'fixtures':8,'checksumsAgree':True}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
