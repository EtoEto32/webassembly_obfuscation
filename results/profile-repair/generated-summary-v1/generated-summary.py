import argparse
import hashlib
import json
from pathlib import Path
import shutil
import importlib.util
import statistics

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit',HERE/'symbolic-audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'generated-summary.py')
    rows=json.loads((source/'results.json').read_text(encoding='utf8'))['rows'];nonconstant=[];families=[]
    try:
        for row in rows:
            expression=audit.evaluate(source/(row['name']+'-source.wasm'),audit.z.BoolVal(False))
            at_zero=audit.z.simplify(audit.z.substitute(expression,(audit.X,audit.z.BitVecVal(0,32)),(audit.Y,audit.z.BitVecVal(0,32))))
            result=audit.equivalence(expression,at_zero)
            if result['status']=='unknown':raise RuntimeError(result)
            nonconstant.append({'name':row['name'],'nonconstant':result['status']=='sat','witness':result})
        for family in range(4):
            group=[r for r in rows if r['name'].startswith('generated_'+str(family)+'_')]
            families.append({'family':family,'cases':len(group),'sites':sum(r['sites'] for r in group),
                'awareSites':sum(len(r['aware']['selected']) for r in group),'independentSites':sum(len(r['independent']['selected']) for r in group),
                'awareCost':sum(r['aware']['cost'] for r in group),'independentCost':sum(r['independent']['cost'] for r in group),
                'lowerCostCases':sum(r['aware']['cost']<r['independent']['cost'] for r in group)})
        report={'nonconstant':nonconstant,'nonconstantCount':sum(r['nonconstant'] for r in nonconstant),'families':families,
            'enumeratedSets':sum(len(r['enumerated']) for r in rows),'awareSynthesisMedianMs':statistics.median(r['aware']['synthesisMs'] for r in rows),
            'sourceManifestSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='nonconstant'}))
    finally:
        (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
