"""Audit actual results and byte reproducibility, not research novelty."""
import argparse
import hashlib
import json
from pathlib import Path

ap=argparse.ArgumentParser();ap.add_argument('first',type=Path);ap.add_argument('replay',type=Path);ap.add_argument('output',type=Path)
a=ap.parse_args();reports=[]
for directory in (a.first,a.replay):
    build=json.loads((directory/'build.json').read_text())
    check=json.loads((directory/'correctness.json').read_text())
    interp=json.loads((directory/'interpreter.json').read_text())
    times=json.loads((directory/'timing.json').read_text())
    adaptive=json.loads((directory/'adaptive-cost.json').read_text())
    controls=json.loads((directory/'controls.json').read_text())
    assert build['status']=='built' and len(build['conditions'])==45
    assert len(build['recovery'])==45 and all(x['status']=='recovered' for x in build['recovery'])
    assert len(check['rows'])==90 and all(x['status']=='passed' for x in check['rows'])
    assert check['calls']==404388 and check['mismatches']==0 and check['bad_width_mismatches']==4599
    assert interp['calls']==180 and interp['mismatches']==0
    assert times['fresh_processes']==135 and len(times['rows'])==135
    assert len(adaptive['results'])==90 and all(x['status']=='recovered' for x in adaptive['results'])
    assert controls['wrong_residue_rejected'] and len(controls['unsupported'])==4
    for row in build['conditions']:
        assert hashlib.sha256((directory/row['file']).read_bytes()).hexdigest()==row['sha256']
    inventory=[{'path':str(f.relative_to(directory)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
               for f in sorted(directory.rglob('*')) if f.is_file()]
    reports.append({'directory':str(directory),'correctness_calls':check['calls'],'interpreter_calls':interp['calls'],
                    'inventory':inventory})
build=json.loads((a.first/'build.json').read_text());matched=0
for row in build['conditions']:
    for relative in (Path(row['file']),Path('recovered')/row['file']):
        assert (a.first/relative).read_bytes()==(a.replay/relative).read_bytes(),str(relative)
        matched+=1
assert (a.first/'inputs.json').read_bytes()==(a.replay/'inputs.json').read_bytes()
result={'byte_identical_input_and_recovered_binaries':matched,'inputs_identical':True,
        'note':'Replay is not new independent input coverage. This audit does not prove novelty, human effort or arbitrary-Wasm equivalence.',
        'runs':reports}
with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps({'matched_binaries':matched,'inputs_identical':True,'inventory_counts':[len(x['inventory']) for x in reports]}))
