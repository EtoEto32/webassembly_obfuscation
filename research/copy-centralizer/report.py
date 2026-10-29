"""Verify saved evidence and pin sources; does not rerun or inflate experiments."""
import json,os,platform,re,statistics,sys
from pathlib import Path
import prototype as p
q=p.q
main,rec,direct,seq,dispatch,audit,out=[Path(x).resolve() for x in sys.argv[1:]];out.mkdir(parents=True,exist_ok=False)
def read(folder,name):return json.loads((folder/name).read_text(encoding='utf-8'))
a=read(audit,'audit.json')
for pin in a['pins']:assert q.digest(p.ROOT/pin['file'])==pin['sha256'],pin['file']
mainrows=read(main,'manifest.json');learned=read(rec,'recovery.json');quick=read(direct,'direct.json')
for r in learned:
    target=next(x for x in mainrows if x['file']==r['file']);n=target['n'];expected=target['matrix']+[1<<i for i in range(n,32)]
    assert r['matrix']==expected and not any(r['offset'])
    assert r['learningCalls']==96 and r['holdoutCalls']==128
for r in quick:
    assert r['logicalReadCalls']==32 and r['logicalWriteCalls']==0
    assert q.digest(direct/r['recovered_file'])==q.digest(rec/r['recovered_file'])
mc=read(main,'checks.json');rc=read(rec,'checks.json');assert mc['mismatches']==rc['mismatches']==0
tables=[];comparison=['# Copy-compatible encoding: measured workload cost','', 'ns is median of 3 process medians, each from 9 batches. Includes write/read, loop and dispatch.','', '|profile|workload|plain ns|conjugate ns|native ns|native/conjugate|native/plain|','|---|---|---:|---:|---:|---:|---:|']
for name,folder in [('sequence',seq),('dispatch',dispatch)]:
    summary=read(folder,'summary.json');runtime=read(folder,'runtime.json');assert len(runtime)==48 and len(summary)==16
    for k in p.m.FIXTURES:
        rows={r['mode']:r for r in summary if r['kernel']==k};assert set(rows)=={'plain','uniform','conjugate','native'}
        for mode,r in rows.items():
            samples=[statistics.median(v['ns']) for v in runtime if v['kernel']==k and v['mode']==mode]
            assert len(samples)==3 and statistics.median(samples)==r['median_ns']
        n,c,b=rows['native']['median_ns'],rows['conjugate']['median_ns'],rows['plain']['median_ns']
        tables.append(dict(profile=k,workload=name,native_vs_conjugate=n/c,native_vs_plain=n/b))
        comparison.append(f'|{k}|{name}|{b:.3f}|{c:.3f}|{n:.3f}|{n/c:.3f}|{n/b:.3f}|')
(out/'comparison.md').write_text('\n'.join(comparison)+'\n',encoding='utf-8')
doclinks=[]
for f in Path(__file__).parent.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'):continue
        target=(f.parent/link.split('#')[0]).resolve();assert target.exists(),str(target);doclinks.append(str(target))
files=[f for folder in (Path(__file__).parent,main,rec,direct,seq,dispatch,audit) for f in folder.iterdir() if f.is_file() and f.suffix in ('.md','.py','.cjs','.json','.wasm')]
files.extend([p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py'])
files.extend(p.q.w.WABT/(name+'.exe') for name in ('wat2wasm','wasm2wat','wasm-validate','wasm-interp'))
files.append(p.q.BIN/'wasm-opt.exe')
pins=[dict(file=str(f.resolve().relative_to(p.ROOT)),sha256=q.digest(f)) for f in files]
result=dict(status='completed candidate evaluation; overall invention goal remains active',main_calls=mc['calls'],recovered_calls=rc['calls'],traps=mc['traps']+rc['traps'],full_memory_comparisons=mc['fullMemoryComparisons']+rc['fullMemoryComparisons'],direct_targets=len(quick),direct_calls=sum(r['logicalReadCalls'] for r in quick),matrix_models=len(a['model_checks']),model_matrices=sum(r['enumerated'] for r in a['model_checks']),byte_reproductions=len(a['regenerated']),engine_probe_conditions=len(a['engine_checks']),negative_controls=len(a['negative_controls']),rejections=len(a['rejections']),performance_processes=96,comparisons=tables,local_document_links=len(doclinks),environment=dict(platform=platform.platform(),python=platform.python_version(),processor_identifier=os.environ.get('PROCESSOR_IDENTIFIER'),node=mc['node'],v8=mc['v8'],tools=a['tools'],cpu_name_status='friendly-name CIM query denied; no new friendly-name measurement'),pins=pins)
q.save(out/'report.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('pins','comparisons','environment')}|dict(pinned_files=len(pins))))
