"""Terminal-protocol regression and retained engine-replay inputs."""
import argparse,copy,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('protocol',HERE/'guard-protocol.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);c=p.c

def main(witness,contracts,out):
    out.mkdir(parents=True,exist_ok=False);regressions=[];counts={kind:{'equal':0,'different':0} for kind in ('full','public','returns')}
    for row in json.loads((witness/'manifest.json').read_text())['rows']:
        model=c.parse(k.p.read(witness/row['source']));profiles={kind:p.prepare(model,row['left'],row['right'],kind) for kind in counts};samples=[]
        for sample in row['samples']:
            values={i:0 if i<c.g.BASE else 256 for i in model['cells']};values.update(dict(sample['patches']));got={kind:p.extract(prepared,values) for kind,prepared in profiles.items()}
            for kind,result in got.items():counts[kind]['equal' if result is None else 'different']+=1
            samples.append(got)
        regressions.append({'name':row['name'],'proofs':{kind:prepared['proof'] for kind,prepared in profiles.items()},'samples':samples})
    (out/'regressions.json').write_text(json.dumps({'counts':counts,'rows':regressions},indent=2));rows=[]
    for old in json.loads((contracts/'manifest.json').read_text())['rows']:
        row=copy.deepcopy(old);model=c.parse(k.p.read(contracts/row['source']));prepared=p.prepare(model,row['left'],row['right'],row['proof']['contract']);row['proof']=prepared['proof'];row['reenterProof']=old['proof']
        for sample,previous in zip(row['samples'],old['samples']):
            values={i:0 if i<c.g.BASE else 256 for i in model['cells']};values.update(dict(sample['patches']));sample['witness']=p.extract(prepared,values)
            if sample['witness'] is None:
                sample['positiveSequences']=([previous['witness']['calls']] if previous['witness'] else previous['positiveSequences'])
        for n in (row['source'],row['prepared']):
            if not (out/n).exists():shutil.copy2(contracts/n,out/n)
        rows.append(row)
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'regressionCounts':counts,'protocol':'terminal'},indent=2))
    for n in ('guard-protocol-cases.py','guard-protocol-replay.mjs','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    result=subprocess.run(['node',str(out/'guard-protocol-replay.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));assert result.returncode==0,result.stderr;print(result.stdout)
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for n in ('witness','contracts','out'):a.add_argument(n,type=Path)
    v=a.parse_args();main(v.witness,v.contracts,v.out)
