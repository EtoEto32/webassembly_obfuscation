"""Synthesize symbolic conditions for previously measured segment-only pairs."""
import argparse,hashlib,importlib.util,json,shutil
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('guard_analysis',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
def main(inputs,contexts,measured,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];ctx=json.loads((contexts/'manifest.json').read_text());results=json.loads((measured/'results.json').read_text())
    for item in ctx['cases']:
        c=item['case'];actual=next(r for r in results['rows'] if r['id']==c['id'] and r['backend']=='migrate' and r['kind']=='observed')
        for s in item['scenarios']:
            restored=next(x for x in actual['scenarios'] if x['status']=='restored' and x['stopAt']==s['stopAt'])
            source=inputs/c['original']
            try:
                model=g.parse(k.p.read(source))
                left=[not x.get('trap',False) for x in actual['expectedState']['segments']]
                right=[not x.get('trap',False) for x in restored['state']['segments']]
                proof=g.solve(model,left,right)
            except ValueError as e:proof={'status':'unsupported','reason':str(e)}
            rows.append({'id':c['id'],'source':c['source'],'stopAt':s['stopAt'],'proof':proof})
    counts={s:sum(r['proof']['status']==s for r in rows) for s in sorted({r['proof']['status'] for r in rows})}
    (out/'results.json').write_text(json.dumps({'counts':counts,'rows':rows},indent=2))
    for name in ('guard-context.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(counts))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inputs',type=Path);p.add_argument('contexts',type=Path);p.add_argument('measured',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.inputs,v.contexts,v.measured,v.out)
