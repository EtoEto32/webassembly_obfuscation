"""Check pinned evidence and references without rerunning or relabeling experiments."""
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
src,runtime,audit,extra,report=map(Path,sys.argv[1:])
target=report/'final-evidence.json'
if target.exists():raise FileExistsError(target)
read=lambda d,n:json.loads((d/n).read_text(encoding='utf-8'))
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pinned=[]
def verify_manifest(folder):
    rows=read(folder,'manifest.json')
    assert len({r['file'] for r in rows})==len(rows)
    for r in rows:
        f=folder/r['file'];assert digest(f)==r['sha256'],f
        pinned.append(dict(file=str(f.resolve().relative_to(ROOT)),sha256=digest(f)))
    return rows
rows=verify_manifest(src);checks=read(src,'checks.json');summary=read(report,'summary.json')
assert len(rows)==checks['targets']==summary['targets']==88
assert checks['inputs']==6656 and checks['calls']==585728
assert checks['positive_mismatches']==0
assert len(checks['records'])==88
positive=[r for r in checks['records'] if r['mode'] not in ('candidate','uncorrected')]
assert len(positive)==56 and all(r['mismatches']==0 for r in positive)
candidate=[r for r in checks['records'] if r['mode']=='candidate']
assert len(candidate)==16 and all(r['nonzeroMismatches']==0 for r in candidate)
assert sum(r['mismatches']>0 for r in candidate)==summary['candidate_failures']==4
assert sum(r['mismatches'] for r in candidate)==summary['candidate_zero_mismatches']==5485
assert len(read(src,'attacks.json'))==16 and all(x['status']=='candidate-extracted' for x in read(src,'attacks.json'))
replay=read(audit,'replay.json');assert len(replay)==88
for r in replay:assert digest(audit/r['file'])==r['sha256']==digest(src/r['file'])
assert read(audit,'interpreter.json')['calls']==336 and len(read(audit,'rejections.json'))==4
# Old snapshots cover the scripts present then; newer docs/scripts are recorded below.
for d in (audit,extra):
    for r in read(d,'sources.json'):assert digest(ROOT/r['file'])==r['sha256'],r['file']
timings=read(runtime,'runtime.json');protocol=read(runtime,'protocol.json');times=read(runtime,'summary.json')
assert len(timings)==len(protocol['jobs'])==120 and len(times)==24
assert all(len(r['ns'])==9 for r in timings)
perf=read(runtime,'checks.json');assert perf['targets']==12 and perf['calls']==79872 and perf['positive_mismatches']==0
for r in times:
    f=runtime/next(x['file'] for x in read(runtime,'manifest.json') if x['kernel']==r['kernel'] and x['mode']==r['mode'])
    assert f.stat().st_size==r['binary_bytes']
for f in sorted(runtime.glob('*.wasm')):
    pinned.append(dict(file=str(f.resolve().relative_to(ROOT)),sha256=digest(f)))
extras=read(extra,'generalization.json');assert len(extras)==6
for r in extras:
    folder=extra/f'arity-{r["arity"]}';rr=verify_manifest(folder);c=read(folder,'checks.json')
    assert len(rr)==r['targets']==c['targets']==18
    assert r['calls']==c['calls'] and c['positive_mismatches']==0
    assert all(x['mismatches']==0 for x in c['records'] if x['mode']!='candidate')
    assert all(x['nonzeroMismatches']==0 for x in c['records'] if x['mode']=='candidate')
    assert len(r['attacks'])==4 and all(x['status']=='candidate-extracted' for x in r['attacks'])
controls=read(extra,'rounding-controls.json');assert len(controls)==4
for r in controls:
    assert r['node']==r['interpreter'] and r['node']['original']==r['expected']!=r['node']['changed']
    assert digest(extra/(r['name']+'-'+r['opt']+'.wasm'))==r['sha256']
files=sorted(Path(__file__).parent.glob('*.md'))+sorted(Path(__file__).parent.glob('*.py'))+sorted(Path(__file__).parent.glob('*.cjs'))
files += [ROOT/'research/isotope-swizzle/prototype.py',ROOT/'research/connectivity-elimination/prototype.py',ROOT/'research/patent/zero-sign-transport.md']
tool_files=[ROOT/'.tools/wabt-1.0.42/bin'/n for n in ('wat2wasm.exe','wasm2wat.exe','wasm-validate.exe','wasm-interp.exe')]+[ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe']
links=[]
for f in files:
    if f.suffix!='.md':continue
    for href in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
        if '://' in href or href.startswith('#'):continue
        linked=(f.parent/href.split('#')[0]).resolve();assert linked.exists(),(f,href)
        links.append(dict(file=str(f.relative_to(ROOT)),target=href))
evidence=[]
for folder,names in ((src,('manifest.json','checks.json','attacks.json','inputs.json','fixtures.json')),(runtime,('protocol.json','runtime.json','summary.json','checks.json')),(audit,('replay.json','interpreter.json','rejections.json','environment.json','sources.json')),(extra,('generalization.json','rounding-controls.json','sources.json')),(report,('summary.json','comparison.md'))):
    for name in names:
        f=folder/name;evidence.append(dict(file=str(f.resolve().relative_to(ROOT)),sha256=digest(f)))
record=dict(scope='Saved evidence and source integrity; no new Wasm runs, timing runs, novelty proof, or legal conclusion',main_positive_calls=56*6656,additional_positive_calls=sum(r['positive_calls'] for r in extras),performance_recheck_calls=perf['calls'],additional_candidate_failures=sum(r['candidate_failures'] for r in extras),additional_candidate_zero_mismatches=sum(r['candidate_mismatches'] for r in extras),runtime_processes=len(timings),sources=[dict(file=str(f.relative_to(ROOT)),sha256=digest(f)) for f in files],tools=[dict(file=str(f.relative_to(ROOT)),sha256=digest(f)) for f in tool_files],evidence=evidence,binaries=pinned,local_links=links)
target.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(source_files=len(files),evidence_files=len(evidence),binaries=len(pinned),local_links=len(links),additional_positive_calls=record['additional_positive_calls'])))
