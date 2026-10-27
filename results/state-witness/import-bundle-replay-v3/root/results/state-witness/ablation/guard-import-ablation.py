"""Deliberately weakened import models, scored against saved concrete tests."""
import argparse,copy,hashlib,importlib.util,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('import_guard',HERE/'guard-import.py');i=importlib.util.module_from_spec(s);s.loader.exec_module(i)


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];summary={m:{'falseEqual':0,'falseDifferent':0} for m in ('erase-import','ignore-read','ignore-write','boundary-only')}
    for row in json.loads((source/'manifest.json').read_text())['rows']:
        contracts={(r['module'],r['field']):{k:r[k] for k in ('reads','writes')} for r in row['proof']['hostSummaries']}
        model=i.parse(i.k.p.read(source/row['source']),contracts);proof=row['proof'];guards={}
        for mode in ('ignore-read','ignore-write'):
            mutant=copy.deepcopy(model)
            for contract in mutant['summaries'].values():contract['reads' if mode=='ignore-read' else 'writes']='none'
            guards[mode]=i.prepare(mutant,row['left'],row['right'],proof['contract'],proof['protocol'])['layers'][-1][0]
        flat=copy.deepcopy(model)
        flat['actions']=[{'name':a['name'],'ops':[op for b in a['blocks'] for op in b['ops']],'readonly':False,'observation':'void'} for a in model['actions']]
        guards['erase-import']=i.e.p.prepare(flat,row['left'],row['right'],proof['contract'],proof['protocol'])['layers'][-1][0]
        guards['boundary-only']=i.e.prepare(flat,row['left'],row['right'],proof['contract'],proof['protocol'],any(s['writes']=='public' for s in contracts.values()))['layers'][-1][0]
        wrong={m:[] for m in guards}
        for n,sample in enumerate(row['samples']):
            expected=sample['witness'] is None;values=dict(sample['values'])
            for mode,guard in guards.items():
                observed=i.c.holds(guard,values,values)
                if observed!=expected:
                    kind='falseEqual' if observed else 'falseDifferent';summary[mode][kind]+=1;wrong[mode].append({'sample':n,'kind':kind})
        rows.append({'name':row['name'],'errors':wrong})
    result={'rows':rows,'summary':summary,'contracts':len(rows),'samples':sum(len(r['samples']) for r in json.loads((source/'manifest.json').read_text())['rows']),
        'scope':'Deliberately wrong models, not existing tools. Boundary-only moves possible host effects to API boundaries and erases host trace observations.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-ablation.py','guard-import.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
