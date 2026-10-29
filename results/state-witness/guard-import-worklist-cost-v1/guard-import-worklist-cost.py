"""Condition-only scheduling comparison; both backends omit rank history."""
import argparse,hashlib,importlib.util,json,random,shutil,statistics,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=load('worklist_cost','guard-import-worklist.py');i=w.i;cost=load('worklist_memory','guard-import-cost.py')

def worker(source,out,method,index):
    rows=json.loads((source/'manifest.json').read_text())['rows'];random.Random(27651+index).shuffle(rows);results=[]
    for row in rows:
        proof=row['proof'];initial=proof['states'][0];summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in proof['hostSummaries']}
        started=time.perf_counter();model=i.parse(i.k.p.read(source/row['source']),summaries);parse=time.perf_counter()-started;times=[];before=cost.memory()
        for repeat in range(7):
            result=None;started=time.perf_counter();result=w.solve(model,initial['left'],initial['right'],proof['contract'],proof['protocol'],schedule=method);elapsed=time.perf_counter()-started
            assert all(result['proof'][k]==proof[k] for k in ('status','guard','states'))
            if repeat>=2:times.append(elapsed)
        results.append({'name':row['name'],'length':row['length'],'parseSeconds':parse,'timesSeconds':times,'medianSeconds':statistics.median(times),
            'algorithm':result['summary'],'memoryBefore':before,'memoryAfter':cost.memory()})
    result={'method':method,'process':index,'seed':27651+index,'python':sys.version,'warmups':2,'repeats':5,'rows':results}
    out.write_text(json.dumps(result,indent=2));print(json.dumps({'method':method,'process':index,'conditions':len(results)}),flush=True)

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);processes=[];failures=[]
    for index in range(3):
        for method in ('atomic','sweep'):
            target=out/(method+'-'+str(index)+'.json')
            try:
                run=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(source),str(target),'--method',method,'--worker',str(index)],timeout=180)
                if run.returncode:failures.append({'method':method,'process':index,'status':'error','code':run.returncode})
                else:processes.append(json.loads(target.read_text()))
            except subprocess.TimeoutExpired:failures.append({'method':method,'process':index,'status':'timeout'})
    rows=[]
    for row in json.loads((source/'manifest.json').read_text())['rows']:
        methods={}
        for method in ('atomic','sweep'):
            values=[next(r['medianSeconds'] for r in p['rows'] if r['name']==row['name']) for p in processes if p['method']==method]
            methods[method]={'processMediansSeconds':values,'medianSeconds':statistics.median(values) if values else None,'rangeSeconds':[min(values),max(values)] if values else None}
        rows.append({'name':row['name'],'length':row['length'],'methods':methods,'sweepOverAtomic':methods['sweep']['medianSeconds']/methods['atomic']['medianSeconds'] if all(v['medianSeconds'] for v in methods.values()) else None})
    result={'rows':rows,'processes':len(processes),'failures':failures,'warmups':2,'repeats':5,
        'scope':'Condition-only, artificial chains, shared parser and WP; graph construction included, parse separate; both omit rank history; both load Z3 through memory helper.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-worklist-cost.py','guard-import-worklist-plan.md','guard-import-worklist.py','guard-import-cost.py','guard-import-generic.py','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({'processes':len(processes),'failures':failures}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);a.add_argument('--method',choices=['atomic','sweep']);a.add_argument('--worker',type=int);v=a.parse_args()
    if v.worker is None:main(v.source,v.out)
    else:worker(v.source,v.out,v.method,v.worker)
