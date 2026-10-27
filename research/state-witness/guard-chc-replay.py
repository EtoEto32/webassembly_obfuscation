"""Reparse and solve saved CHC artifacts independently of the encoder."""
import argparse,hashlib,importlib.util,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('array_checker',HERE/'guard-table-check.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);z=a.z

def main(sources,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for source in sources:
        data=json.loads((source/'results.json').read_text());selected=[]
        # Include SAT, UNSAT, and the deepest accepted negative public chain.
        for status in ('sat','unsat'):
            eligible=[r for r in data['rows'] if r['status']==status]
            if eligible:selected.append(eligible[0])
        eligible=[r for r in data['rows'] if r['status']=='sat' and r['contract']=='public']
        if eligible:selected.append(max(eligible,key=lambda r:r['cells']))
        for r in selected:
            fp=z.Fixedpoint();fp.set(engine='spacer',timeout=5000);queries=fp.parse_file(str(source/r['smt']));assert len(queries)==1
            answer=str(fp.query(queries[0]));assert answer==r['status'];rows.append({'source':str(source/r['smt']),'answer':answer,'sha256':hashlib.sha256((source/r['smt']).read_bytes()).hexdigest()})
    (out/'results.json').write_text(json.dumps({'rows':rows,'parsedQueries':len(rows),'z3':z.get_version_string()},indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({'parsedQueries':len(rows)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('sources',nargs='+',type=Path);v=p.parse_args();main(v.sources,v.out)
