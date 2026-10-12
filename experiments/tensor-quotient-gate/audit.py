"""Recheck stored certificates, negative mutations and file provenance."""
import copy, hashlib, json
from pathlib import Path
from experiment import BASE, ROOT, OUT, certificate

report=OUT/'audit.json'
if report.exists():raise SystemExit('Refuse overwrite audit')
rows=0;cases=0
for f in sorted(OUT.glob('*.recovered.json')):
    stem=f.name.removesuffix('.recovered.json')
    p=json.loads((OUT/(stem+'.public.json')).read_text())
    r=json.loads(f.read_text())
    rows+=certificate(p,r);cases+=1
    assert r['source_public_sha256']==hashlib.sha256((OUT/(stem+'.public.json')).read_bytes()).hexdigest()
    assert r['public_sha256']==hashlib.sha256((OUT/(stem+'.quotient.json')).read_bytes()).hexdigest()
results=json.loads((OUT/'results.json').read_text())
for relative,digest in results['source_hashes'].items():
    assert hashlib.sha256((BASE/relative).read_bytes()).hexdigest()==digest
p=json.loads((OUT/'plain.public.json').read_text())
r=json.loads((OUT/'plain.recovered.json').read_text())
mutations=[]
for kind in ['output-bit','input-order']:
    changed=copy.deepcopy(r)
    if kind=='output-bit':changed['outputs'][0]['table'][0]^=1
    else:changed['inputs'][0],changed['inputs'][1]=changed['inputs'][1],changed['inputs'][0]
    try:certificate(p,changed)
    except AssertionError:mutations.append({'kind':kind,'rejected':True})
    else:raise AssertionError('Mutation accepted')
# Reduction modulo 2 does not commute with arbitrary Wasm word operations.
shift_counterexample={'inputs':[0,2],'input_parities':[0,0],'unsigned_shift_right_by_one':[0,1],'output_parities':[0,1]}
assert [(x>>1)&1 for x in shift_counterexample['inputs']]==[0,1]
record={'certificates':cases,'local_rows':rows,'source_hashes_verified':len(results['source_hashes']),'mutations':mutations,'noncongruence_counterexample':shift_counterexample}
report.write_text(json.dumps(record,indent=2))
print(json.dumps(record))
