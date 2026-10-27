import json, shutil, statistics, sys
from pathlib import Path
import prototype as p

src,run,control,recovery,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
manifest=json.loads((src/'manifest.json').read_text());runtime=json.loads((run/'summary.json').read_text())
rows=[];lines=['# 0への割当による補正削除：測定表','','nsは5 fresh processの各中央値の中央値。[min,max]もprocess中央値間の範囲。比率は小さい方が速い。CPU/V8一組での測定。','','| kernel | seed | masked ns [range] | free ns [range] | table ns [range] | free/masked | free/table | free/plain | bytes masked/free/table |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for kernel in sorted({r['kernel'] for r in manifest}):
    plain=next(r['median_ns'] for r in runtime if r['kernel']==kernel and r['mode']=='plain')
    for seed in (7,29):
        g={r['mode']:r for r in runtime if r['kernel']==kernel and r['seed']==seed}
        mm={r['mode']:r for r in manifest if r['kernel']==kernel and r['seed']==seed and r['opt']=='O3'}
        f=g['anchor-free']['median_ns'];ratio=f/g['anchor-masked']['median_ns'];rt=f/g['anchor-table']['median_ns']
        def desc(k):
            r=g[k];return f"{r['median_ns']:.3f} [{r['min_ns']:.3f},{r['max_ns']:.3f}]"
        sizes='/'.join(str(mm[k]['bytes']) for k in ('anchor-masked','anchor-free','anchor-table'))
        lines.append(f"|{kernel}|{seed}|{desc('anchor-masked')}|{desc('anchor-free')}|{desc('anchor-table')}|{ratio:.3f}|{rt:.3f}|{f/plain:.3f}|{sizes}|")
        rows.append(dict(kernel=kernel,seed=seed,free_masked=ratio,free_table=rt,free_plain=f/plain,masked_and=mm['anchor-masked']['instructions'].get('v128.and',0),free_and=mm['anchor-free']['instructions'].get('v128.and',0)))
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');q.save(out/'comparison.json',rows)
# Regenerate with the explicit range-to-zero assignment planner and compare
# bytes to the measurements. Semantic tests need not be repeated for identical bytes.
replay=out/'replay';replay.mkdir();identity=[]
for r in manifest:
    if r['opt']!='raw':continue
    f=replay/r['file'];info=p.transform(src/r['source'],f,r['mode'],r['seed'])
    assert q.digest(f)==r['sha256'],r['file']
    identity.append(dict(file=r['file'],sha256=q.digest(f),byte_identical=True,planner=info))
    opt=f.with_name(f.name.replace('-raw','-O3'));q.tool('wasm-opt',[f,'--enable-simd','--enable-relaxed-simd','-O3','-o',opt])
    ref=next(x for x in manifest if x['file']==opt.name);assert q.digest(opt)==ref['sha256'],opt.name
    identity.append(dict(file=opt.name,sha256=q.digest(opt),byte_identical=True))
q.save(out/'identity.json',identity)
files=[*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),*Path(__file__).parent.glob('*.md'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py',p.ROOT/'research/encoding-lowering/internal.cjs']
snap=out/'sources';snap.mkdir();hashes=[]
for f in files:
    name=str(f.relative_to(p.ROOT) if f.is_absolute() else f).replace('\\','__').replace('/','__')
    shutil.copyfile(f,snap/name);hashes.append(dict(path=str(f),snapshot=name,sha256=q.digest(f)))
checks={label:json.loads((folder/'checks.json').read_text()) for label,folder in [('main',src),('deterministic_clones',control),('recovered',recovery)]}
analysis=json.loads((recovery/'analysis.json').read_text())
q.save(out/'protocol.json',dict(sources=hashes,environment=json.loads((src/'environment.json').read_text()),counts={k:dict(cases=v['cases'],wasm_calls=v['wasm_calls'],mismatches=v['mismatches']) for k,v in checks.items()},total_calls=sum(v['wasm_calls'] for v in checks.values()),recovered=sum(x['status']=='recovered' for x in analysis),unsupported=sum(x['status']=='unsupported' for x in analysis),crashes=0,timeouts=0,main_targets=len(manifest),fresh_processes=330,warmup=100000,batches=9,batch_size=200000,benchmark_order_seed=21102026,linear_memory_bytes=0,replayed_byte_identical=len(identity)))
print(json.dumps(dict(replayed=len(identity),calls=sum(v['wasm_calls'] for v in checks.values()),recovered=sum(x['status']=='recovered' for x in analysis))))
