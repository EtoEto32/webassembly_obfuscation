import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p
def wrap(src,dst,probe=False):
    m=p.q.read(src);fs=[e for e in m[1:] if e[0]=='func'];ix=next(int(e[2][1]) for e in m[1:] if e[0]=='export' and e[1]=='"compress"')
    # n=0, state=1, loop index=2, chaining state=3..10.
    f=['func',['param','i32'],['result','i32'],['local',*(['i32']*10)]]
    f.extend(['local.set',str(3+i),p.c(0x6a09e667+i)] for i in range(8));f.append(['local.set','1',p.c(211053)])
    body=[['br_if','1',['i32.ge_u',p.get(2),p.get(0)]],['local.set','1',p.add(p.op('mul',p.get(1),p.c(1664525)),p.c(1013904223))],['call',str(ix),*[p.get(3+i) for i in range(8)],*[p.xor(p.get(1),p.c(i*0x1234567)) for i in range(16)]]]
    body.extend(['local.set',str(3+i)] for i in reversed(range(8)))
    body.extend([['local.set','2',p.add(p.get(2),p.c(1))],['br','0']]);f.append(['block',['loop',*body]]);f.append(p.xor(p.get(1),*[p.get(3+i) for i in range(8)]))
    index=len(fs);m.extend([f,['export','"bench"',['func',str(index)]]]);p.q.compile(p.q.w.emit(m),dst)
def main(main,rec,out):
    main=Path(main);rec=Path(rec);out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[r for r in json.loads((main/'targets.json').read_text()) if r['opt']=='O3'];rt=json.loads((rec/'targets.json').read_text());r=next(x for x in rt if x['label']=='fiber1-O3-recovered-O3');rows.append({'label':'recovered','path':r['path'],'bytes':Path(r['path']).stat().st_size})
    for row in rows:
        f=out/(row['label']+'-bench.wasm');wrap(row['path'],f);row['bench']=str(f)
    jobs=[(r,repeat) for repeat in range(3) for r in rows];random.Random(211054).shuffle(jobs);samples=[]
    for row,repeat in jobs:
        f=out/(row['label']+'-'+str(repeat)+'.json');cp=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),row['bench'],str(f)],capture_output=True,text=True,timeout=60)
        if cp.returncode:raise RuntimeError(cp.stderr)
        v=json.loads(f.read_text());v.update(label=row['label'],repeat=repeat,core_bytes=row['bytes']);samples.append(v);print(row['label'],repeat,round(v['median_ns'],2),flush=True)
    if len(set(x['correctness_checksum'] for x in samples))!=1:raise AssertionError('benchmark checksum mismatch')
    summary=[]
    for row in rows:
        ss=[x for x in samples if x['label']==row['label']];times=[x['median_ns'] for x in ss]
        summary.append({'label':row['label'],'median_ns':statistics.median(times),'min_ns':min(times),'max_ns':max(times),'core_bytes':row['bytes'],'linear_memory_bytes':0 if row['label']=='recovered' else 65536,'median_max_rss_kib':statistics.median(x['max_rss_kib'] for x in ss)})
    (out/'summary.json').write_text(json.dumps({'processes':len(samples),'seed':211054,'conditions':summary,'samples':samples},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main(*sys.argv[1:])
