import argparse,hashlib,json,shutil,statistics,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
def stats(v):
    q=statistics.quantiles(v,n=4,method='inclusive')
    return {'median':statistics.median(v),'q1':q[0],'q3':q[2],'processMedians':v}
def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for f in ('bench.py','bench.cjs','plan.md'):shutil.copy2(HERE/f,out/f)
    raw=[]
    try:
        for i in range(5):
            cmd=['node','--no-liftoff',str(HERE/'bench.cjs'),str(source/'manifest.json'),str(i)]
            r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=120)
            raw.append({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
            (out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if r.returncode:raise RuntimeError(r.stderr)
        data=[json.loads(r['stdout']) for r in raw];rows=[]
        for row in data[0]['rows']:
            keys=['fixture','kind','n','mode'];key=tuple(row[k] for k in keys)
            vals=[next(x['medianNs'] for x in d['rows'] if tuple(x[k] for k in keys)==key) for d in data]
            bases=[next(x['medianNs'] for x in d['rows'] if (x['fixture'],x['kind'],x['n'],x['mode'])==(*key[:3],'fresh')) for d in data]
            rows.append({**dict(zip(keys,key)),'ns':stats(vals),'pairedToFresh':stats([a/b for a,b in zip(vals,bases)])})
        result={'rows':rows,'processes':5,'rounds':15,'warmupRounds':2,'sourceSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
                'note':'Cached compiled Module. Fresh includes allocation/GC; reset includes work. Plain is correct only for work-only fixtures; it is not a general reset. Process RSS is mixed-mode, not per-mode.'}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({'rows':len(rows),'processes':5}))
    finally:(out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2),encoding='utf8')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
