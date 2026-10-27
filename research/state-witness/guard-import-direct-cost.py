"""Isolated repeated witness-only batches, with shared preparation reported."""
import argparse,hashlib,importlib.util,json,random,shutil,statistics,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=load('direct_cost_solver','guard-import-direct.py');q=load('smt_cost_solver','guard-import-check.py');cost=load('memory_reading','guard-import-cost.py');i=d.i

def cases():
    result=[]
    for folder in ('guard-import-controls-v1','guard-import-may-controls-v1'):
        source=ROOT/'results/state-witness'/folder
        for row in json.loads((source/'manifest.json').read_text())['rows']:
            samples=[s for s in row['samples'] if s['witness']]
            if not samples:continue
            summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in row['proof']['hostSummaries']}
            model=i.parse(i.k.p.read(source/row['source']),summaries);p=i.prepare(model,row['left'],row['right'],row['proof']['contract'],row['proof']['protocol'])
            for sample in samples:result.append((row['name'],p,dict(sample['values'])))
    source=ROOT/'results/state-witness/guard-import-may-witness-v1';manifest=json.loads((source/'manifest.json').read_text());prepared={}
    for row in manifest['rows']:
        if row['kind'] not in prepared:
            summaries={('env','touch'):{'reads':'none','writes':'may-public'},('env','observe'):{'reads':'public','writes':'none'}}
            model=i.parse(i.k.p.read(source/row['source']),summaries);prepared[row['kind']]=i.prepare(model,[False]*3,[True,False,False],'returns','reenter')
        result.append(('two-import-'+row['kind'],prepared[row['kind']],dict(row['values'])))
    assert len(result)==280;return result

def worker(out,method,index):
    started=time.perf_counter();items=cases();prepare=time.perf_counter()-started;rng=random.Random(91431+index);rng.shuffle(items);times=[];outputs=[];before=cost.memory()
    fn=d.witness if method=='direct' else q.witness
    for repeat in range(7):
        result=[];started=time.perf_counter()
        for name,p,values in items:result.append(fn(p,values))
        elapsed=time.perf_counter()-started
        assert all(r is not None for r in result)
        stat={'witnesses':len(result),'totalApiLength':sum(r['apiLength'] for r in result),'maxApiLength':max(r['apiLength'] for r in result)}
        if repeat>=2:times.append(elapsed);outputs.append(stat)
    row={'method':method,'process':index,'seed':91431+index,'preparationSeconds':prepare,'timesSeconds':times,'medianSeconds':statistics.median(times),'outputCounts':outputs,
        'memoryBefore':before,'memoryAfter':cost.memory(),'python':sys.version,'z3':q.z.get_version_string(),'warmups':2,'repeats':5}
    out.write_text(json.dumps(row,indent=2));print(json.dumps({'method':method,'process':index,'medianSeconds':row['medianSeconds'],'outputCounts':outputs[-1]}),flush=True)

def main(out):
    out.mkdir(parents=True,exist_ok=False);processes=[];failures=[]
    for index in range(3):
        for method in ('direct','smt'):
            target=out/(method+'-'+str(index)+'.json')
            try:
                run=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(target),'--method',method,'--worker',str(index)],timeout=180)
                if run.returncode:failures.append({'method':method,'process':index,'status':'error','code':run.returncode})
                else:processes.append(json.loads(target.read_text()))
            except subprocess.TimeoutExpired:failures.append({'method':method,'process':index,'status':'timeout'})
    summary={}
    for method in ('direct','smt'):
        medians=[r['medianSeconds'] for r in processes if r['method']==method]
        summary[method]={'processMediansSeconds':medians,'medianSeconds':statistics.median(medians) if medians else None,'rangeSeconds':[min(medians),max(medians)] if medians else None}
    (out/'results.json').write_text(json.dumps({'summary':summary,'failures':failures,'processes':len(processes),'negativeCases':280,'warmups':2,'repeats':5,'scope':'Witness-only artificial corpus; parser and equality fixed point shared; not author-tool performance.'},indent=2))
    for name in ('guard-import-direct-cost.py','guard-import-direct-cost-plan.md','guard-import-direct.py','guard-import-direct-plan.md','guard-import-cost.py','guard-import-generic.py','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({'summary':summary,'failures':failures}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);a.add_argument('--method',choices=['direct','smt']);a.add_argument('--worker',type=int);v=a.parse_args()
    if v.worker is None:main(v.out)
    else:worker(v.out,v.method,v.worker)
