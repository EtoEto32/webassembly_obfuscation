import json,shutil,statistics,sys
from pathlib import Path
import prototype as p

src,run,pilot,controls,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
load=lambda f:json.loads(f.read_text())
manifest=load(src/'manifest.json');runtime=load(run/'summary.json');pilotrows=load(pilot/'summary.json');raw=load(run/'runtime.json')
lines=['# 飽和カウンタの符号化：比較結果','','主要測定はwarmup20,000、9×50,000回、5 fresh process。nsは全counter更新1回の時間、process中央値5個の中央値。[min,max]は同5個の範囲。比率は小さい方が速い。下の値は1 CPU / 1 engineの観察。','','|N|処理|seed|min ns [range]|zero ns [range]|zero/min|zero/native|zero/random-min|zero/plain|zero/complement|zero/table|bytes min/zero|初回zero/min|','|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|'];rows=[]
for n in (256,4096):
    for w in ('merge','merge_decay'):
        for seed in (7,29):
            g={r['mode']:r for r in runtime if r['counters']==n and r['workload']==w and r['seed'] in (0,seed)}
            old={r['mode']:r for r in pilotrows if r['counters']==n and r['workload']==w and r['seed'] in (0,seed)}
            mm={r['mode']:r for r in manifest if r['counters_per_bank']==n and r['seed']==seed and r['opt']=='O3'}
            f=g['anchor-zero']['median_ns'];ratios={k:f/g[k]['median_ns'] for k in ('anchor-min','anchor-native','random-min','plain','complement','random-table')}
            desc=lambda k:f"{g[k]['median_ns']:.3f} [{g[k]['min_ns']:.3f},{g[k]['max_ns']:.3f}]"
            ratiofields='|'.join(f'{r:.3f}' for r in ratios.values());sz=f"{mm['anchor-min']['bytes']}/{mm['anchor-zero']['bytes']}"
            pr=old['anchor-zero']['median_ns']/old['anchor-min']['median_ns']
            lines.append(f"|{n}|{w}|{seed}|{desc('anchor-min')}|{desc('anchor-zero')}|{ratiofields}|{sz}|{pr:.3f}|")
            rows.append(dict(counters=n,workload=w,seed=seed,ratios=ratios,pilot_zero_min=pr,nonoverlap=g['anchor-zero']['max_ns']<g['anchor-min']['min_ns']))
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');q.save(out/'comparison.json',rows)
replay=out/'replay';replay.mkdir();identities=[];instructions=[]
for r in manifest:
    counts={}
    for node in q.walk(q.read(src/r['file'])):counts[node[0]]=counts.get(node[0],0)+1
    instructions.append(dict(file=r['file'],bytes=r['bytes'],instructions=counts))
    if r['opt']!='raw':continue
    f=replay/r['file'];p.transform(src/r['source'],f,r['mode'],r['seed']);assert q.digest(f)==r['sha256']
    identities.append(dict(file=f.name,sha256=q.digest(f)))
    opt=f.with_name(f.name.replace('-raw','-O3'));q.tool('wasm-opt',[f,'--enable-simd','--enable-relaxed-simd','--enable-bulk-memory','-O3','-o',opt])
    ref=next(x for x in manifest if x['file']==opt.name);assert q.digest(opt)==ref['sha256'];identities.append(dict(file=opt.name,sha256=q.digest(opt)))
q.save(out/'identity.json',identities);q.save(out/'instructions.json',instructions)
snapshot=out/'sources';snapshot.mkdir();hashes=[]
files=[*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),*Path(__file__).parent.glob('*.md'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
for file in files:
    f=file.resolve();name=str(f.relative_to(p.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,snapshot/name);hashes.append(dict(path=str(f),snapshot=name,sha256=q.digest(f)))
q.save(out/'protocol.json',dict(sources=hashes,environment=load(src/'environment.json'),correctness={k:v for k,v in load(src/'checks.json').items() if k!='records'},adaptive_recovered=len(load(src/'recovery.json')),adaptive_queries_per_binary=16,adaptive_task='known layout: learn one shared nibble encoding and decode observed banks',analysis_status=dict(recovered=48,unsupported=0,crashes=0,timeouts=0),replayed_byte_identical=len(identities),controls=dict(algebra=load(controls/'algebra.json'),clones=load(controls/'clones.json'),rejections=load(controls/'rejections.json')),measurement=dict(fresh_processes=len(raw),warmup=20000,batch=50000,batches=9,order_seed=211002,pilot_processes=240,pilot_warmup=100,pilot_batch=500),linear_memory_bytes=65536,packed_data_bytes=[256,4096],transform_ms_range=[min(r['ms'] for r in manifest),max(r['ms'] for r in manifest)],rss_kib_range=[min(r['rss_kib'] for r in raw),max(r['rss_kib'] for r in raw)]))
print(json.dumps(dict(replayed=len(identities),comparisons=len(rows),processes=len(raw),nonoverlap=sum(r['nonoverlap'] for r in rows))))
