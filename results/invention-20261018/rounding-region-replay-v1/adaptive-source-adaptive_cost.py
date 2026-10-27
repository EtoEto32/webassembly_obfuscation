"""Separate optional certification cost from trusted-family extraction cost."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import time
import prototype as p
import recover as r

ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);a=ap.parse_args()
build=json.loads((a.directory/'build.json').read_text())
rows=list(build['conditions']);random.Random(0x41444150).shuffle(rows)
results=[]
for row in rows:
    mod=p.w.parse(p.w.tool('wasm2wat',[a.directory/row['file'],'--fold-exprs']))
    reference=r.recover_model(mod,True)
    for verify in (False,True):
        samples=[]
        for iteration in range(6):
            start=time.perf_counter();result=r.recover_model(mod,verify);elapsed=time.perf_counter()-start
            assert result==reference
            if iteration:samples.append(elapsed)
        results.append({**row,'verify_correction':verify,'samples_seconds':samples,
                        'median_seconds':statistics.median(samples),'status':'recovered',
                        'recovered_tree_sha256':hashlib.sha256(json.dumps(result).encode()).hexdigest()})
# A trusted-family extractor deliberately does not reject a forged correction.
# This is its assumption/limit, not an error hidden as a secure verifier.
bad=p.w.parse(p.w.tool('wasm2wat',[a.directory/'wrong-residue.wasm','--fold-exprs']))
unchecked=r.recover_model(bad,False)
try:r.recover_model(bad,True)
except ValueError as exc:rejection=str(exc)
else:raise AssertionError('Verification should reject')
report={'scope':'Parsed model to reconstructed integer tree. Excludes WABT/disassembly, output emission and hash. One warmup, five samples. Same process; no significance claim.',
        'results':results,'control':{'trusted_family_extracts_forged_program':True,'verifier_rejection':rejection,
        'warning':'Unchecked extraction is valid only for this generator family, not arbitrary code matching a superficial pattern.'}}
with (a.directory/'adaptive-cost.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
for name in ('adaptive_cost.py','recover.py','finish.py'):
    (a.directory/('adaptive-source-'+name)).write_bytes(Path(__file__).with_name(name).read_bytes())
print(json.dumps({'analyses':len(results),'recovered_tree_disagreements':0,'forged_control_rejected_by_verifier':True}))
