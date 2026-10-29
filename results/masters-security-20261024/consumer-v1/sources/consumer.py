"""Randomized, separate-process consumer microbenchmark and paired analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import time

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('consumer.py','consumer.cjs','consumer-plan.md'):
        shutil.copy2(HERE/name,out/'sources'/name)
    schedule=[(i,m) for i in range(5) for m in ('full','materialize','segments','manual')]
    random.Random(20261024).shuffle(schedule)
    (out/'schedule.json').write_text(json.dumps(schedule,indent=2),encoding='utf8')
    runs={};durations=[]
    for rep,mode in schedule:
        dest=out/f'{rep}-{mode}.json';start=time.perf_counter()
        r=subprocess.run(['node',str(HERE/'consumer.cjs'),str(source),mode,str(dest)],capture_output=True,text=True,timeout=90)
        if r.returncode: raise RuntimeError(r.stderr)
        runs[rep,mode]=json.loads(dest.read_text());durations.append({'rep':rep,'mode':mode,'seconds':time.perf_counter()-start})
    stats=[]
    for j in range(len(runs[0,'full']['entries'])):
        baseline=[statistics.median(runs[i,'full']['entries'][j]['samples_us']) for i in range(5)]
        for mode in ('full','materialize','segments','manual'):
            es=[runs[i,mode]['entries'][j] for i in range(5)]
            for i,e in enumerate(es):assert e['checksums']==runs[i,'full']['entries'][j]['checksums']
            mids=[statistics.median(e['samples_us']) for e in es]
            ratio=[v/base for v,base in zip(mids,baseline)]
            q=statistics.quantiles(mids,n=4,method='inclusive')
            stats.append({'fixture':es[0]['fixture'],'mode':mode,'processMedians_us':mids,'median_us':statistics.median(mids),
                          'iqr_us':[q[0],q[2]],'pairedRatios':ratio,'medianRatio':statistics.median(ratio),
                          'retainedPayloadBytes':es[0]['retainedPayloadBytes'],'postCallbackPayloadBytes':es[0]['postCallbackPayloadBytes']})
    result={'sourceManifestSha256':sha(source/'manifest.json'),'processes':len(runs),'durations':durations,'stats':stats,
            'scope':'8KiB self-authored Rust fixtures; process RSS includes runtime; no third-party baseline implementation'}
    (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    lines=['# 区間consumerの実測','', '5独立process反復、各100 warmup、300呼出し×9 batch。表はprocess中央値の中央値。方式間checksum一致。','',
           '|fixture|方式|us/call|全コピー比（対応反復の中央値）|保持payload合計|復帰後payload合計|','|---|---|---:|---:|---:|---:|']
    for r in stats:lines.append('|%s|%s|%.3f|%.3f|%d|%d|'%(r['fixture'],r['mode'],r['median_us'],r['medianRatio'],r['retainedPayloadBytes'],r['postCallbackPayloadBytes']))
    lines+=['','payloadは136入力分の合計。全コピーbaselineは復帰後の全量コピーを行わない。segments/manualはconsumer終了まで別writerを許可しない。',
            '本測定は同一機器・自作8KiB fixture。IQR/全反復はsummary.json。RSSは各process JSONにあるが方式単独のpeakを示さない。']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'processes':len(runs),'fixtures':8,'checksumsAgree':True,'output':str(out)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();main(args.source.resolve(),args.output.resolve())
