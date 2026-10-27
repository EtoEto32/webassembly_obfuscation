"""Apply the unchanged guard generator to the previous disjoint memory corpus."""
import argparse,hashlib,importlib.util,json,shutil
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('guard_analysis',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
def main(spec,disjoint,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for c in json.loads((disjoint/'manifest.json').read_text())['cases']:
        for target in c['segments']:
            seg=target['segment'];source=spec/c['source']
            try:
                model=g.parse(k.p.read(source));left=[s['initialLive'] for s in model['segments']];right=left.copy()
                if seg['kind']!='data':raise g.Unsupported('not a data segment')
                right[seg['index']]=False;result=g.solve(model,left,right)
            except ValueError as e:result={'status':'unsupported','reason':str(e)}
            rows.append({'source':c['source'],'sourceSha256':c['sourceSha256'],'segment':seg,'result':result})
    counts={s:sum(r['result']['status']==s for r in rows) for s in sorted({r['result']['status'] for r in rows})}
    (out/'results.json').write_text(json.dumps({'counts':counts,'rows':rows,'classifierSha256':hashlib.sha256((HERE/'guard-analysis.py').read_bytes()).hexdigest()},indent=2))
    for n in ('guard-corpus.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(counts))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path);p.add_argument('disjoint',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.spec,v.disjoint,v.out)
