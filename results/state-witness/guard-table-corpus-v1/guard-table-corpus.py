"""Apply the same equality method to the full previous disjoint corpus."""
import argparse,hashlib,importlib.util,json,shutil
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('table_guard',HERE/'guard-table.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
def main(spec,disjoint,previous,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];old=json.loads((previous/'results.json').read_text())['rows']
    for c in json.loads((disjoint/'manifest.json').read_text())['cases']:
        for target in c['segments']:
            seg=target['segment'];source=spec/c['source']
            try:
                model=g.parse(k.p.read(source));left=[s['initialLive'] for s in model['segments']];right=left.copy()
                i=next(i for i,s in enumerate(model['segments']) if s['kind']==seg['kind'] and s['index']==seg['index']);right[i]=False
                proof=g.solve(model,left,right)
            except ValueError as e:proof={'status':'unsupported','reason':str(e)}
            before=next(r['result'] for r in old if r['source']==c['source'] and r['segment']['kind']==seg['kind'] and r['segment']['index']==seg['index'])
            if before['status']!='unsupported':assert proof['status']==before['status'] and proof['guard']==before['guard']
            rows.append({'source':c['source'],'sourceSha256':c['sourceSha256'],'segment':seg,'proof':proof,'previousStatus':before['status']})
    counts={s:sum(r['proof']['status']==s for r in rows) for s in sorted({r['proof']['status'] for r in rows})}
    result={'rows':rows,'counts':counts,'sourceHashes':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('guard-table.py','guard-analysis.py')}}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-table-corpus.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(counts))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path);p.add_argument('disjoint',type=Path);p.add_argument('previous',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.spec,v.disjoint,v.previous,v.out)
