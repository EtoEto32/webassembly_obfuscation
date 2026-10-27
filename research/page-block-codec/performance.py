import argparse, json, random, statistics, subprocess
from pathlib import Path
from run import q,HERE

def main(main,extra,dst):
    main=Path(main);extra=Path(extra);dst=Path(dst);dst.mkdir(parents=True,exist_ok=False)
    jobs=[]
    for mode in ('plain','lifted','byte','block','block-high'):
        f=(extra if mode=='block-high' else main)/f'p1.{mode}.O3.wasm'
        for off in (0,13):
            for rep in range(3):jobs.append((mode,str(f.resolve()),off,rep))
    random.Random(211063).shuffle(jobs);rows=[]
    for mode,f,off,rep in jobs:
        r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(HERE/'bench.cjs'),f,str(off)],capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr)
        row=dict(mode=mode,file=f,offset=off,rep=rep,sha256=q.digest(f),bytes=Path(f).stat().st_size,result=json.loads(r.stdout));rows.append(row)
        q.save(dst/f'{mode}-offset{off}-rep{rep}.json',row)
    assert len({x['result']['expected'] for x in rows})==1
    summary=[]
    for mode in ('plain','lifted','byte','block','block-high'):
        for off in (0,13):
            rr=[x for x in rows if x['mode']==mode and x['offset']==off];tt=[x['result']['median_ns'] for x in rr]
            summary.append(dict(mode=mode,offset=off,median_ns=statistics.median(tt),min_ns=min(tt),max_ns=max(tt),bytes=rr[0]['bytes'],linear_memory_bytes=65536,maxRSS_KiB=statistics.median(x['result']['maxRSS_KiB'] for x in rr)))
    q.save(dst/'summary.json',dict(seed=211063,fresh_processes=len(rows),rows=summary));print(json.dumps(summary))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('extra');ap.add_argument('output');a=ap.parse_args();main(a.main,a.extra,a.output)
