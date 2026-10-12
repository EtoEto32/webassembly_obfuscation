"""Audit saved evidence; this does not rerun or expand the earlier experiment."""
from pathlib import Path
import hashlib,json
base=Path(r'C:\Users\ettotto\Documents\wasm-structured-encoding\candidates')
program_path=base/'trap-prefix-fusion/artifacts-v2/programs.json'
result_path=base/'trap-prefix-recovery/artifacts-v3/results.json'
programs=json.loads(program_path.read_text());results=json.loads(result_path.read_text())['results']
rows=[]
for p in programs:
    stores=[i for i,op in enumerate(p['ops']) if op['op']=='store']
    loads=[i for i,op in enumerate(p['ops']) if op['op']=='load']
    rows.append({'program':p['name'],'stores':len(stores),'last_store':max(stores,default=-1),
                 'last_load':max(loads,default=-1),'load_after_all_stores':bool(loads) and max(loads)>max(stores,default=-1)})
binary_checks=[]
for r in results:
    p=base/'trap-prefix-fusion/artifacts-v2'/r['file']
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual==r['inputSha256'],p
    binary_checks.append({'file':r['file'],'sha256':actual,'cases':r['inputCases'],
                           'recovered':r['exactOrderedLogs'],'mismatches':r['mismatches']})
out={'scope':'Saved-evidence audit, not a new recovery experiment.',
     'sources':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (program_path,result_path)],
     'programs':rows,'binaries':binary_checks,
     'all_programs_have_load_after_all_stores':all(r['load_after_all_stores'] for r in rows),
     'total_cases':sum(r['cases'] for r in binary_checks),'total_recovered':sum(r['recovered'] for r in binary_checks)}
Path(__file__).with_name('evidence-audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ('sources','programs','binaries')},indent=2))
