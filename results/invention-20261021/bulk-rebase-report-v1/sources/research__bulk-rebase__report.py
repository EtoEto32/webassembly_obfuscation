"""Report preserved measurements, regenerate binaries, and snapshot all sources."""
import json,re,shutil,statistics,subprocess,sys
from pathlib import Path
import prototype as p
src,runtime,recovery,controls,verify,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
load=lambda f:json.loads(f.read_text(encoding='utf-8'))
manifest=load(src/'manifest.json');summary=load(runtime/'summary.json');raw=load(runtime/'runtime.json')
assert len(raw)==270 and len(summary)==54
lines=['# 位置依存表現のcopy比較','','単一CPU/V8、各値は5 fresh processの各9標本中央値の中央値、ns/copy。括弧はprocess中央値の最小–最大。全条件に同じ強制最適化compiler指定を使用。素朴な復号版、scalar直接補正版、SIMD直接補正版を分ける。','','|長さ|配置|plain|復号scalar|直接scalar|後補正scalar|直接SIMD [範囲]|後補正SIMD [範囲]|後/直接SIMD|','|---:|---|---:|---:|---:|---:|---|---|---:|'];comparisons=[]
for n in (16,256,4096):
    for layout in ('forward','backward','separate'):
        g={r['mode']:r for r in summary if r['n']==n and r['layout']==layout}
        desc=lambda k:f"{g[k]['median_ns']:.2f} [{g[k]['min_ns']:.2f}, {g[k]['max_ns']:.2f}]"
        ratio=g['bulk-simd']['median_ns']/g['direct-simd']['median_ns']
        vals='|'.join(f"{g[k]['median_ns']:.2f}" for k in ('plain','decode-scalar','direct-scalar','bulk-scalar'))
        lines.append(f"|{n}|{layout}|{vals}|{desc('direct-simd')}|{desc('bulk-simd')}|{ratio:.3f}|")
        comparisons.append(dict(n=n,layout=layout,bulk_direct_simd_ratio=ratio,bulk_plain_ratio=g['bulk-simd']['median_ns']/g['plain']['median_ns'],bulk_slower_ranges_separated=g['bulk-simd']['min_ns']>g['direct-simd']['max_ns']))
lines+=['','## サイズ・初期化・最大RSS','','binaryはbench loop追加前。線形memoryは全方式64KiB。RSSはprocess全体のhigh-water。初期化時間はinstantiate/startのみの各45processの中央値で、copy時間に含めない。変換msはreader/compiler/validator込み単回測定。','','|方式|bytes|変換ms|instantiate/start ms|RSS KiB|','|---|---:|---:|---:|---:|'];size_records=[]
for mode in p.MODES:
    r=next(x for x in manifest if x['pages']==1 and x['mode']==mode and x['opt']=='O3' and x['seed']==(0 if mode=='plain' else 7));g=[x for x in raw if x['mode']==mode]
    record=dict(mode=mode,bytes=r['bytes'],transform_ms=r['ms'],instantiate_ms_median=statistics.median(x['instantiate_ms'] for x in g),rss_kib_median=statistics.median(x['rss_kib'] for x in g));size_records.append(record)
    lines.append(f"|{mode}|{r['bytes']}|{r['ms']:.2f}|{record['instantiate_ms_median']:.3f}|{record['rss_kib_median']:.0f}|")
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');q.save(out/'comparison.json',comparisons);q.save(out/'sizes.json',size_records)

replay=out/'replay';replay.mkdir();identities=[]
for r in manifest:
    if r['opt']!='raw':continue
    f=replay/r['file'];p.transform(src/r['source'],f,r['mode'],r['seed']);assert q.digest(f)==r['sha256'];identities.append(dict(file=f.name,sha256=q.digest(f)))
    opt=f.with_name(f.name.replace('-raw','-O3'));q.tool('wasm-opt',[f,'--enable-simd','--enable-bulk-memory','-O3','-o',opt])
    ref=next(x for x in manifest if x['file']==opt.name);assert q.digest(opt)==ref['sha256'];identities.append(dict(file=opt.name,sha256=q.digest(opt)))
q.save(out/'identity.json',identities)

# Match the benchmark's explicit compiler flags in a separate diagnostic run.
machine=out/'machine';machine.mkdir();diagnostic=[]
for r in manifest:
    if r['pages']!=1 or r['opt']!='O3' or r['seed']!=(0 if r['mode']=='plain' else 7):continue
    file=runtime/r['file'];code='new WebAssembly.Instance(new WebAssembly.Module(require("fs").readFileSync(process.argv[1])));'
    result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation','--print-wasm-code','-e',code,str(file)],capture_output=True,text=True,check=True,timeout=30)
    (machine/(r['mode']+'.txt')).write_text(result.stdout+'\nSTDERR\n'+result.stderr,encoding='utf-8')
    compilers=re.findall(r'^compiler: (.+)$',result.stdout,re.M);assert compilers and set(compilers)=={'TurboFan'},compilers
    diagnostic.append(dict(file=r['file'],sha256=q.digest(file),functions=len(compilers),compilers=sorted(set(compilers))))
q.save(out/'machine.json',diagnostic)
snapshot=out/'sources';snapshot.mkdir();hashes=[]
for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),*Path(__file__).parent.glob('*.md'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
    f=f.resolve();name=str(f.relative_to(p.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,snapshot/name);hashes.append(dict(file=str(f.relative_to(p.ROOT)),snapshot=name,sha256=q.digest(f)))
rc=load(recovery/'recovery.json');checks=load(src/'checks.json');vf=load(verify/'verification.json')
q.save(out/'audit.json',dict(correctness={k:v for k,v in checks.items() if k!='records'},adaptive={k:v for k,v in rc.items() if k!='records'},adaptive_queries_per_target=31,selected_input_verification_per_target=4096,second_engine={k:v for k,v in vf.items() if k!='records'},model=load(controls/'model.json'),negative_controls=load(controls/'negative-controls.json'),rejections=load(controls/'rejections.json'),identical_binaries=len(identities),performance_processes=len(raw),comparisons=len(comparisons),slower_nonoverlap=sum(x['bulk_slower_ranges_separated'] for x in comparisons),sources=hashes,environment=load(src/'environment.json'),performance_protocol=load(runtime/'protocol.json')))
print(json.dumps(dict(replayed=len(identities),performance_processes=len(raw),slower_nonoverlap=sum(x['bulk_slower_ranges_separated'] for x in comparisons),compiler_diagnostics=len(diagnostic))))
