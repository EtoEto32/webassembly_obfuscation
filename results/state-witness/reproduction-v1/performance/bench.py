import argparse,hashlib,json,shutil,statistics,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for name in ('bench.py','bench.cjs','observer.cjs'):shutil.copy2(HERE/name,out/name)
    raw=[]
    for i in range(5):
        cmd=['node',str(HERE/'bench.cjs'),str(source.resolve()),str(20261024+i)]
        r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=90)
        raw.append({'command':cmd,'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
    runs=[json.loads(x['stdout']) for x in raw];rows=[]
    for r in runs[0]['rows']:
        key=lambda x:(x['fixture'],x['state'],x['mode']);target=key(r)
        medians=[next(x['medianNs'] for x in d['rows'] if key(x)==target) for d in runs]
        rows.append({'fixture':r['fixture'],'state':r['state'],'mode':r['mode'],'medianNs':statistics.median(medians),
                     'processMedians':medians,'quartiles':statistics.quantiles(medians,n=4,method='inclusive')})
    (out/'results.json').write_text(json.dumps({'rows':rows,'processes':5,'warmup':3,'rounds':15,'repeats':100,
       'inputHash':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
       'rssBytesRange':[min(x['rss'] for x in runs),max(x['rss'] for x in runs)]},indent=2))
    (out/'sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir()},indent=2))
    print(json.dumps({'rows':len(rows),'processes':len(runs)}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
