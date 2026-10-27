"""Apply the predeclared host-write contract to the frozen mixed corpus."""
import argparse,collections,hashlib,importlib.util,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('environment',HERE/'guard-environment.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)

def guard(x):return None if x is None else e.eq.canonical([(tuple(a),tuple(b)) for a,b in x])

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);old=json.loads((source/'manifest.json').read_text());rows=[];cache={};changes=collections.Counter();sample_changes=collections.Counter()
    try:
        for row in old['rows']:
            if row['source'] not in cache:
                cache[row['source']]=e.c.parse(e.k.p.read(source/row['source']))
                for key in ('source','prepared'):shutil.copy2(source/row[key],out/row[key])
            model=cache[row['source']];prepared=e.prepare(model,row['left'],row['right'],row['proof']['contract'],row['proof']['protocol']);proof=prepared['proof']
            closed=e.prepare(model,row['left'],row['right'],proof['contract'],proof['protocol'],False)['proof'];assert closed['guard']==row['proof']['guard']
            assert e.eq.combine(guard(proof['guard']),guard(closed['guard']))==guard(proof['guard']),'condition weakened'
            changes[(proof['contract'],proof['protocol'],closed['status'],proof['status'])]+=1;samples=[]
            for sample in row['samples']:
                values=dict(sample['patches']);witness=e.extract(prepared,values);positive=[]
                sample_changes[(sample['witness'] is not None,witness is not None)]+=1
                if not witness:
                    assert not sample['witness']
                    positive=[[{'kind':'call',**a} for a in seq] for seq in sample['positiveSequences']]
                    assignments=list(e.assignments(prepared,values,values))
                    for i,seq in enumerate(positive[:3]):
                        writes=assignments[i%len(assignments)]
                        positive.append([step for call in seq for step in ({'kind':'write','cells':list(map(list,sorted(writes.items())))},call)])
                samples.append({'origin':sample['origin'],'patches':sample['patches'],'witness':witness,'positiveSequences':positive,'legacyNegative':sample['witness'] is not None})
            rows.append({key:row[key] for key in ('name','source','prepared','family','maskedTemplate','left','right')})
            rows[-1].update(proof=proof,samples=samples,legacyStatus=closed['status'],legacyGuard=closed['guard'])
        e.k.p.compile_wat('(module (func (export "foreign") (result i32) (i32.const 999)))',out/'foreign.wasm')
        summary={'contractChanges':[{'contract':a,'protocol':b,'before':c,'after':d,'count':n} for (a,b,c,d),n in sorted(changes.items())],
            'sampleChanges':[{'beforeNegative':a,'afterNegative':b,'count':n} for (a,b),n in sorted(sample_changes.items())]}
        (out/'manifest.json').write_text(json.dumps({'rows':rows,'summary':summary,'source':source.as_posix(),'scope':'Same frozen synthetic inputs; arbitrary common writes to originally public resources; initial fitted samples inherited from the closed-host experiment.'},indent=2))
        print(json.dumps({'contracts':len(rows),**summary}))
    except Exception as err:(out/'failure.json').write_text(json.dumps({'reason':repr(err),'completed':len(rows)},indent=2));raise
    finally:
        for name in ('guard-environment-corpus.py','guard-environment.py','guard-environment-plan.md','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
        (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
