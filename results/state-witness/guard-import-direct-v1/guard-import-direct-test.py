"""Replay solver-free counterexamples on the existing import control families."""
import argparse,copy,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=load('direct_solver','guard-import-direct.py');c=load('runtime_imports','guard-import-controls.py');i=d.i

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];signs=[];engine=c.wt.Engine();totals={k:0 for k in ('apiCalls','preparationCalls','hostCalls','cellWrites','pureTagCalls')};checks=0
    for folder in ('guard-import-controls-v1','guard-import-may-controls-v1'):
        source=ROOT/'results/state-witness'/folder
        for original in json.loads((source/'manifest.json').read_text())['rows']:
            raw=source/original['source'];target=out/raw.name
            if target.exists():assert target.read_bytes()==raw.read_bytes()
            else:shutil.copy2(raw,target)
            summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in original['proof']['hostSummaries']}
            model=i.parse(i.k.p.read(raw),summaries);prepared=i.prepare(model,original['left'],original['right'],original['proof']['contract'],original['proof']['protocol'])
            assert json.loads(json.dumps(prepared['proof']))==original['proof'];compiled=c.wt.Module(engine,raw.read_bytes());row=copy.deepcopy(original);row['samples']=[]
            for sample in original['samples']:
                values=dict(sample['values']);witness=d.witness(prepared,values);assert (witness is None)==(sample['witness'] is None)
                signs.append({'name':row['name'],'values':sample['values'],'equal':witness is None})
                if witness is None:continue
                word=copy.deepcopy(witness['calls']);fresh=257+model['functions']
                # Existing controls provide one pure foreign tag 260. The new
                # representative is not a program constant; relabel it injectively.
                constants={x for s in model['segments'] for x in s['values']}
                if row['kind']=='table':
                    assert fresh not in constants and 260 not in constants and fresh not in values.values()
                    for call in word:
                        for block in call['writes']:
                            block['cells']=[[cell,260 if value==fresh else value] for cell,value in block['cells']]
                run,count=c.replay(engine,compiled,row,values,word);assert not run['equal'],row['name'];checks+=1
                for key,value in count.items():totals[key]+=value
                row['samples'].append({'values':sample['values'],'witness':witness,'referenceRelabeling':{str(fresh):260} if row['kind']=='table' else {},'runs':[{'word':word,**run}]})
            rows.append(row)
    isolated=subprocess.run([sys.executable,'-c',"import sys,importlib.util;from pathlib import Path;p=Path(sys.argv[1]);sys.path.insert(0,str(p.parent));s=importlib.util.spec_from_file_location('direct',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);assert not any(n=='z3' or n.startswith('z3.') for n in sys.modules);print('no-z3-import')",str(HERE/'guard-import-direct.py')],capture_output=True,text=True,encoding='utf8',timeout=20);assert isolated.returncode==0,isolated.stderr
    result={'rows':rows,'contracts':len(rows),'runtimeComparisons':checks,**totals,'signs':signs,'isolatedImport':isolated.stdout.strip()}
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    node=subprocess.run(['node',str(HERE/'guard-import-controls.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=90)
    (out/'node-log.json').write_text(json.dumps({'code':node.returncode,'stdout':node.stdout,'stderr':node.stderr},indent=2));assert node.returncode==0,node.stderr
    for name in ('guard-import-direct-test.py','guard-import-direct.py','guard-import-direct-plan.md','guard-import-controls.py','guard-import-controls.mjs','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(node.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
