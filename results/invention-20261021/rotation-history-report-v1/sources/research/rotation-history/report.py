"""Audit saved evidence and snapshot all reproduction sources."""
import json
import shutil
import sys
from pathlib import Path
import prototype as p

out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
base=p.ROOT/'results/invention-20261021'
names=['rotation-history-v1','rotation-history-model-v1','rotation-history-audit-v1','rotation-history-runtime-v1']
dirs=[base/n for n in names]
def read(d,n):return json.loads((d/n).read_text(encoding='utf-8'))
old=read(dirs[0],'hashes.json')
assert all(p.q.digest(dirs[0]/f)==h for f,h in old.items())
correct=read(dirs[0],'correctness.json');attacks=read(dirs[0],'attacks.json');replay=read(dirs[2],'replay.json')
assert correct['calls']==26496 and all(x['mismatches']==0 for x in correct['records'])
assert len(attacks)==16 and all(x['queries']==64 for x in attacks)
assert len(replay)==24 and all((dirs[0]/f).read_bytes()==(dirs[2]/f).read_bytes() for f in replay)
dynamic=read(dirs[0],'dynamic-counterexamples.json');bits=read(dirs[2],'dynamic-bit-probes.json')
assert len(dynamic)==12 and all(x['next_outputs']==[0,1] for x in dynamic)
assert sum(len(x['pairs']) for x in bits)==104 and all(x['next_outputs']==[0,1] for r in bits for x in r['pairs'])
summary=dict(classification='negative protection result and finite-suffix obstruction; not a new adopted invention',
    source_directories=names,wasm_calls=correct['calls'],wasm_binaries=len(correct['records']),
    expected_traps=sum(x['traps'] for x in correct['records']),recovered_source=8,recovered_history=8,
    queries_per_binary=64,byte_replays=len(replay),interpreter_calls=read(dirs[2],'interpreter.json')['calls'],
    model=read(dirs[1],'summary.json'),runtime=read(dirs[3],'summary.json'),dynamic_suffix_pairs=12,
    dynamic_bit_pairs=104,initial_hashes_verified=len(old),environment=read(dirs[2],'environment.json'))
p.q.save(out/'summary.json',summary)
sources=list(Path(__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.cjs'))+list(Path(__file__).parent.glob('*.md'))
sources += [p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
for f in sources:
    dst=out/'sources'/f.relative_to(p.ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
p.q.save(out/'input-hashes.json',{str(f.relative_to(base)).replace('\\','/'):p.q.digest(f) for d in dirs for f in sorted(d.rglob('*')) if f.is_file()})
p.q.save(out/'hashes.json',{str(f.relative_to(out)).replace('\\','/'):p.q.digest(f) for f in sorted(out.rglob('*')) if f.is_file()})
print(json.dumps({k:summary[k] for k in ('wasm_calls','wasm_binaries','expected_traps','byte_replays','dynamic_bit_pairs')}))
