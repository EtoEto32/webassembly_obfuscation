"""Check all prospective contracts with independent array recurrence."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('protocol','guard-protocol.py');r=load('reenter_check','guard-contract-check.py');t=load('terminal_check','guard-protocol-check.py');f=load('fast','guard-terminal-fast.py')

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];cache={};fast_checks=0
    try:
        for row in json.loads((source/'manifest.json').read_text())['rows']:
            if row['source'] not in cache:cache[row['source']]=p.c.parse(k.p.read(source/row['source']))
            model=cache[row['source']];kind=row['proof']['contract'];protocol=row['proof']['protocol'];prepared=p.prepare(model,row['left'],row['right'],kind,protocol)
            assert json.loads(json.dumps(prepared['proof']))==row['proof'];start=time.perf_counter();checks=(t if protocol=='terminal' else r).check(model,prepared)
            if kind=='returns' and protocol=='terminal':assert f.analyse(model,row['left'],row['right'])['guard']==row['proof']['guard'];fast_checks+=1
            rows.append({'name':row['name'],'checks':checks,'seconds':time.perf_counter()-start})
            if len(rows)%96==0:print(json.dumps({'checkedContracts':len(rows)}),flush=True)
        result={'rows':rows,'contracts':len(rows),'unsat':sum(x['answer']=='unsat' for r0 in rows for x in r0['checks']),
          'unknown':sum(x['answer']=='unknown' for r0 in rows for x in r0['checks']),'fastTerminalReturnsChecks':fast_checks,'z3':r.z.get_version_string(),
          'scope':'Prospective mixed-resource recurrence checks; shared parser and independent array effects; not full Wasm semantics proof.'}
        (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    except Exception as e:(out/'failure.json').write_text(json.dumps({'reason':repr(e),'rows':rows},indent=2));raise
    finally:
        for n in ('guard-holdout-check.py','guard-terminal-fast.py','guard-protocol-check.py','guard-protocol.py','guard-contract-check.py','guard-contract.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
        (out/'sha256.json').write_text(json.dumps({q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in out.iterdir()},indent=2))
if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('source',type=Path);q.add_argument('out',type=Path);v=q.parse_args();main(v.source,v.out)
