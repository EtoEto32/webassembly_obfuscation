"""Exhaustive allowed lifetime pairs: one-call shortcut versus fixed point."""
import argparse,hashlib,importlib.util,itertools,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=load('fast','guard-terminal-fast.py');p=load('protocol','guard-protocol.py')

def main(witness,contracts,out):
    out.mkdir(parents=True,exist_ok=False);paths=[witness/r['source'] for r in json.loads((witness/'manifest.json').read_text())['rows']]
    paths+=sorted({contracts/r['source'] for r in json.loads((contracts/'manifest.json').read_text())['rows']});rows=[];counts={'equal':0,'different':0};fast_total=general_total=0
    for source in paths:
        model=f.c.parse(k.p.read(source));flags=list(itertools.product(*[(False,True) if s['initialLive'] else (False,) for s in model['segments']]));pairs=[]
        for left,right in itertools.product(flags,repeat=2):
            start=time.perf_counter();fast=f.analyse(model,left,right);fast_total+=time.perf_counter()-start
            start=time.perf_counter();prepared=p.prepare(model,left,right,'returns','terminal');general_total+=time.perf_counter()-start
            assert fast['guard']==prepared['proof']['guard'],(str(source),left,right,fast,prepared['proof'])
            if fast['witness']:
                values={i:0 if i<f.c.g.BASE else 256 for i in model['cells']};found=p.extract(prepared,values);assert found and found['shortestLength']==1
            counts['equal' if fast['witness'] is None else 'different']+=1
            pairs.append({'left':left,'right':right,'status':fast['status'],'witness':fast['witness'],'fixedPointStates':len(prepared['proof']['states'])})
        rows.append({'source':str(source),'pairs':pairs})
    result={'rows':rows,'modules':len(rows),'pairs':sum(len(r['pairs']) for r in rows),'counts':counts,
      'singlePassDiagnosticSeconds':{'shortcut':fast_total,'fixedPoint':general_total},'scope':'Exhaustive permitted lifetime pairs; same parser but different outcome classifier. Single-pass timing is diagnostic, not a performance experiment.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-terminal-evaluate.py','guard-terminal-fast.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for n in ('witness','contracts','out'):a.add_argument(n,type=Path)
    v=a.parse_args();main(v.witness,v.contracts,v.out)
