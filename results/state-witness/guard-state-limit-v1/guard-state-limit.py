"""Expose unnecessary segment-state enumeration; compare existing def-use proof."""
import argparse,hashlib,importlib.util,json,random,shutil,statistics,subprocess,sys,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('table_guard','guard-table.py');c=load('context_analysis','context-analysis.py')
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine();rng=random.Random(45033);calls=0
    for n in (2,4,6,8,10,11):
        source=out/f'drops-{n:02}.wasm';wat='(module (memory (export "memory") 1 1) '+' '.join('(data "X")' for _ in range(n+1))
        wat+=' '.join(f'(func (export "drop{i}") (data.drop {i}))' for i in range(1,n+1))+')'
        k.p.compile_wat(wat,source);module=k.p.read(source);model=g.parse(module);left=[False]+[True]*n;right=[True]*(n+1)
        times={'symbolic':[],'def-use':[]}
        for repeat in range(9):
            start=time.perf_counter()
            try:
                proof=g.solve(model,left,right);result={'status':proof['status'],'states':len(proof['states']),'iterations':proof['iterations']}
            except ValueError as e:result={'status':'unsupported','reason':str(e)}
            elapsed=time.perf_counter()-start
            if repeat>=2:times['symbolic'].append(elapsed)
            start=time.perf_counter();cert=c.certify(module,[('data',0)]);elapsed=time.perf_counter()-start
            if repeat>=2:times['def-use'].append(elapsed)
        assert cert['status']=='certified-no-segment-effect'
        if n<=10:assert result['status']=='unconditional' and result['states']==2**n
        else:assert result=={'status':'unsupported','reason':'segment-state-pair bound'}
        prepared=out/f'drops-{n:02}-prepared.wasm';module.append(k.p.expr('(func (export "__drop0") (data.drop 0))'));k.p.compile_wat(k.p.w.emit(module),prepared)
        compiled=wt.Module(engine,prepared.read_bytes());sequence=[rng.randrange(1,n+1) for _ in range(64)]
        with wt.Store(engine) as store:
            a=wt.Instance(store,compiled,[]).exports(store);b=wt.Instance(store,compiled,[]).exports(store);a['__drop0'](store)
            for i in sequence:
                a['drop'+str(i)](store);b['drop'+str(i)](store);calls+=2
                assert a['memory'].read(store)==b['memory'].read(store)
        rows.append({'independentDrops':n,'source':source.name,'prepared':prepared.name,'analysis':result,'defUse':cert,'timesSeconds':times,
          'medianSeconds':{name:statistics.median(values) for name,values in times.items()},'apiSequence':sequence})
    result={'rows':rows,'wasmtimeApiCalls':calls,'warmups':2,'repeats':7,'seed':45033,
      'scope':'Artificial state-growth control. Def-use already proves all cases; no new dependency-slicing algorithm claimed.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-state-limit.py','guard-table.py','guard-analysis.py','context-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps({'cases':len(rows),'wasmtimeCalls':calls,'classifications':[r['analysis'] for r in rows]}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
