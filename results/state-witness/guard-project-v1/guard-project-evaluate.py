"""Regression and actual-engine controls for segment dependency projection."""
import argparse,hashlib,importlib.util,json,random,shutil,statistics,subprocess,sys,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('projection','guard-project.py');wc=load('witness_cases','guard-witness-cases.py');g=p.w.g
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def main(witness,corpus,spec,out):
    out.mkdir(parents=True,exist_ok=False);regressions=[];changed_words=0;total_samples=0
    for row in json.loads((witness/'manifest.json').read_text())['rows']:
        model=g.parse(k.p.read(witness/row['source']));r=p.analyse(model,row['left'],row['right']);proof=r['prepared']['proof']
        assert proof['guard']==row['proof']['guard'] and proof['status']==row['proof']['status']
        for s in row['samples']:
            values={i:0 if i<g.BASE else 256 for i in model['cells']};values.update(dict(s['patches']));got=p.w.extract(r['prepared'],values);before=s['witness'];total_samples+=1
            assert (got is None)==(before is None)
            if got:
                assert len(got['word'])==len(before['word']);changed_words+=got['word']!=before['word']
        regressions.append({'name':row['name'],'segmentsBefore':len(model['segments']),'segmentsAfter':len(r['model']['segments']),
          'statesBefore':len(row['proof']['states']),'statesAfter':len(proof['states']),'status':proof['status']})
    official=[]
    for row in json.loads((corpus/'results.json').read_text())['rows']:
        try:
            model=g.parse(k.p.read(spec/row['source']));left=[s['initialLive'] for s in model['segments']];right=left.copy();target=row['segment']
            si=next(i for i,s in enumerate(model['segments']) if s['kind']==target['kind'] and s['index']==target['index']);right[si]=False
            r=p.analyse(model,left,right);proof=r['prepared']['proof']
        except ValueError as e:proof={'status':'unsupported','reason':str(e)}
        assert proof['status']==row['proof']['status']
        if proof['status']!='unsupported':assert proof['guard']==row['proof']['guard']
        official.append({'source':row['source'],'segment':row['segment'],'status':proof['status']})
    rng=random.Random(524810);engine=wt.Engine();rows=[];cost=[];calls=0
    for n in (0,2,4,6,8,10,11):
        name=f'projection-{n:02}';raw=out/(name+'.wasm')
        wat='(module (memory 1 1) (data "A") (data "B") '+' '.join('(data "X")' for _ in range(n))
        wat+='(func (export "test") (memory.init 0 (i32.const 0) (i32.const 0) (i32.const 1)) (data.drop 0) (memory.init 1 (i32.const 0) (i32.const 0) (i32.const 1)))'
        wat+=' '.join(f'(func (export "noise{i}") (data.drop {i+2}))' for i in range(n))+')';k.p.compile_wat(wat,raw)
        module=k.p.read(raw);model=g.parse(module);left=[False,False]+[True]*n;right=[True,False]+[True]*n
        times={'original':[],'projected':[]}
        for repeat in range(9):
            start=time.perf_counter()
            try:old=g.solve(model,left,right);before={'status':old['status'],'states':len(old['states'])}
            except ValueError as e:before={'status':'unsupported','reason':str(e)}
            elapsed=time.perf_counter()-start
            if repeat>=2:times['original'].append(elapsed)
            start=time.perf_counter();r=p.analyse(model,left,right);elapsed=time.perf_counter()-start
            if repeat>=2:times['projected'].append(elapsed)
        assert r['prepared']['proof']['guard']==[[['c',65],['m',0]]]
        if before['status']!='unsupported':assert old['guard']==r['prepared']['proof']['guard']
        cost.append({'independentDrops':n,'original':before,'projectedStates':len(r['prepared']['proof']['states']),
          'timesSeconds':times,'medianSeconds':{key:statistics.median(v) for key,v in times.items()}})
        binary=out/(name+'-prepared.wasm');wc.prepare_module(module,model,binary);compiled=wt.Module(engine,binary.read_bytes())
        for pattern in range(4):
            left=[False,False]+[rng.choice([False,True]) for _ in range(n)];right=[True,False]+[rng.choice([False,True]) for _ in range(n)]
            r=p.analyse(model,left,right);proof=r['prepared']['proof'];assert proof['guard']==[[['c',65],['m',0]]]
            prefix=['noise'+str(rng.randrange(n)) for _ in range(32)] if n else []
            suffix=['noise'+str(rng.randrange(n)) for _ in range(16)] if n else []
            sequence=prefix+['test']+suffix+['test'];samples=[]
            for byte in (65,66):
                difference=None
                with wt.Store(engine) as store:
                    pair=[]
                    for flags in (left,right):
                        e=wt.Instance(store,compiled,[]).exports(store);e['__guard_resource_0'].write(store,bytes([byte]))
                        for i,v in enumerate(flags):
                            if not v:e['__guard_drop_'+str(i)](store)
                        pair.append(e)
                    for i,api in enumerate(sequence):
                        outcomes=[]
                        for e in pair:
                            try:e[api](store);outcomes.append('return')
                            except wt.Trap:outcomes.append('trap')
                            calls+=1
                        if outcomes[0]!=outcomes[1] or pair[0]['__guard_resource_0'].read(store)!=pair[1]['__guard_resource_0'].read(store):difference=i+1;break
                expected=None if byte==65 else len(prefix)+1;assert difference==expected
                samples.append({'byte':byte,'firstDifference':difference})
            rows.append({'name':name+'-'+str(pattern),'prepared':binary.name,'left':left,'right':right,'proof':proof,
              'keptOriginalSegmentIndices':r['keptOriginalSegmentIndices'],'sequence':sequence,'samples':samples})
    manifest={'rows':rows,'regressions':regressions,'official':official,'cost':cost,'priorSamples':total_samples,'changedWitnessWords':changed_words,'wasmtimeApiCalls':calls,'seed':524810}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for n in ('guard-project-evaluate.py','guard-project-replay.mjs','guard-project.py','guard-witness.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    proc=subprocess.run(['node',str(out/'guard-project-replay.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for name in ('witness','corpus','spec','out'):a.add_argument(name,type=Path)
    v=a.parse_args();main(v.witness,v.corpus,v.spec,v.out)
