import json,random,statistics,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
rows=[r for r in json.loads((root/'manifest.json').read_text()) if r['profile']=='counter' and r['opt']=='O3' and not r['negative']]
order=[(r,i) for r in rows for i in range(3)];random.Random(211021).shuffle(order);results=[]
for r,i in order:
    cmd=['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(root/r['file']),str(r['b'])]
    p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=60);j=json.loads(p.stdout);j.update(mode=r['mode'],process=i,bytes=r['bytes'])
    results.append(j);(out/f'{r["mode"]}-{i}.json').write_text(json.dumps(j,indent=2),encoding='utf-8')
summary=[]
for r in rows:
    xs=[x for x in results if x['mode']==r['mode']];v=[x['median'] for x in xs]
    summary.append(dict(mode=r['mode'],median_ns=statistics.median(v),min_ns=min(v),max_ns=max(v),bytes=r['bytes'],rss_kib=[x['rssKiB'] for x in xs]))
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
