"""Re-use the original inference function; change only trace column labels."""
import gzip
import hashlib
import json
import platform
from pathlib import Path
from recover import recover

HERE = Path(__file__).resolve().parent
OUT = HERE/'provenance-results.json'
if OUT.exists():
    raise FileExistsError(OUT)
report = json.loads((HERE/'artifacts/results.json').read_text())
source_key = str(Path('history-position-gate')/'recover.py')
assert hashlib.sha256((HERE/'recover.py').read_bytes()).hexdigest() == report['source_hashes'][source_key]
rows = []
for variant in report['variants']:
    name = f"{variant['seed']}-anonymous.json.gz"
    raw = (HERE/'artifacts'/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == report['artifact_hashes'][name]
    data = json.loads(gzip.decompress(raw))
    old = variant['found']['order']
    rotate = lambda xs: xs[1:]+xs[:1]
    found = recover([rotate(r) for r in data['training']])['order']
    expected = [(i-1) % 48 for i in old]
    assert found == expected
    good = bad = 0
    witness = None
    for i,row in enumerate(data['evaluation']):
        vals = row['values']
        changed = rotate(vals)
        target = [vals[k] for k in old]
        actual = [changed[k] for k in found]
        stale = [changed[k] for k in old]
        assert actual == target
        good += 1
        if stale != target:
            bad += 1
            if witness is None:
                witness = {'row':i,'boundary':row['boundary'],'expected':target,'stale':stale}
    assert good == variant['evaluation_states'] and bad > 0
    rows.append({'seed':variant['seed'],'old_order':old,'found_order':found,
                 'held_out_matches':good,'stale_map_mismatches':bad,'negative_witness':witness,
                 'input_sha256':hashlib.sha256(raw).hexdigest()})
sources = [HERE/'recover.py',HERE/'check_provenance.py',HERE/'provenance-protocol.json',HERE/'artifacts/results.json']
result = {'python':platform.python_version(),'variants':rows,
          'total_binding_checks':sum(r['held_out_matches'] for r in rows),
          'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'total_binding_checks':result['total_binding_checks'],
                  'stale_map_mismatches':[r['stale_map_mismatches'] for r in rows]}))
