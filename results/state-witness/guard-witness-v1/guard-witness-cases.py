"""Validate exact witnesses on existing controls plus prospective long chains."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('witness',HERE/'guard-witness.py');w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)

def prepare_module(module,model,dest):
    for r,info in model['resources'].items():module.append(k.p.expr(f'(export "__guard_resource_{r}" ({info["kind"]} {info.get("index",0)}))'))
    for i in range(model['functions']):module.append(k.p.expr(f'(export "__guard_func_{i}" (func {i}))'))
    for i,s in enumerate(model['segments']):module.append(k.p.expr(f'(func (export "__guard_drop_{i}") ({s["kind"]}.drop {s["index"]}))'))
    k.p.compile_wat(k.p.w.emit(module),dest)

def record(name,source,left,right,samples,out,expected=None):
    raw=out/(name+'.wasm')
    if source!=raw:shutil.copy2(source,raw)
    module=k.p.read(raw);model=w.g.parse(module);start=time.perf_counter();prepared=w.prepare(model,left,right);build=time.perf_counter()-start
    if expected is not None:assert prepared['proof']['guard']==expected['guard']
    compiled=out/(name+'-prepared.wasm');prepare_module(module,model,compiled)
    result=[]
    for sample in samples:
        values={i:0 if i<w.g.BASE else 256 for i in model['cells']};values.update(dict(sample['patches']));w.validate_values(model,values)
        start=time.perf_counter();witness=w.extract(prepared,values);extract=time.perf_counter()-start
        start=time.perf_counter();baseline=w.concrete_bfs(model,left,right,values);bfs=time.perf_counter()-start
        assert baseline['status']!='budget'
        assert (witness is None)==sample['satisfies']==(baseline['status']=='equivalent'),(name,sample,witness,baseline)
        if witness:
            assert len(witness['word'])==len(baseline['word'])
            if sample.get('oldWitness'):assert len(witness['word'])==len(sample['oldWitness'])
            if sample.get('expectedLength'):assert len(witness['word'])==sample['expectedLength']
        result.append({**sample,'witness':witness,'bfs':baseline,'extractSeconds':extract,'bfsSeconds':bfs})
    return {'name':name,'source':raw.name,'prepared':compiled.name,'proof':prepared['proof'],'left':left,'right':right,
      'samples':result,'prepareSeconds':build,'sourceBytes':raw.stat().st_size,'preparedBytes':compiled.stat().st_size}

def main(memory,random,table,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for prefix,directory in [('memory',memory),('random',random),('table',table)]:
        manifest=json.loads((directory/'manifest.json').read_text())
        for row in manifest['rows']:
            samples=[]
            for s in row['samples']:
                samples.append({'patches':s.get('patches',list(enumerate(s.get('bytes',[])))),'satisfies':s['satisfies'],'oldWitness':s.get('witness')})
            left=row.get('left',[False,False]);right=row.get('right',[True,False])
            rows.append(record(prefix+'-'+row['name'],directory/row['source'],left,right,samples,out,row['proof']))
    for kind in ('memory','table'):
        for n in (2,4,8,16,32,64,128):
            name=f'chain-{kind}-{n:03}';src=out/(name+'.wasm')
            if kind=='memory':
                header='(memory 1 1) (data "A") (data "B")';init=lambda i:f'(memory.init {i} (i32.const 0) (i32.const 0) (i32.const 1))'
                body='(func (export "test") '+init(0)+'(data.drop 0)'+init(1)+f') (func (export "copy") (memory.copy (i32.const 0) (i32.const 1) (i32.const {n-1})))'
                good,bad,start=65,66,0
            else:
                header=f'(table {n} {n} funcref) (func $a (result i32) (i32.const 101)) (func $b (result i32) (i32.const 202)) (elem func $a) (elem func $b)'
                init=lambda i:f'(table.init 0 {i} (i32.const 0) (i32.const 0) (i32.const 1))'
                body='(func (export "test") '+init(0)+'(elem.drop 0)'+init(1)+f') (func (export "copy") (table.copy 0 0 (i32.const 0) (i32.const 1) (i32.const {n-1})))'
                good,bad,start=257,258,w.g.BASE
            k.p.compile_wat('(module '+header+body+')',src)
            positive=[[start+i,good] for i in range(n)];negative=[[start+i,bad if i==n-1 else good] for i in range(n)]
            samples=[{'patches':positive,'satisfies':True},{'patches':negative,'satisfies':False,'expectedLength':n}]
            rows.append(record(name,src,[False,False],[True,False],samples,out))
    manifest={'rows':rows,'scope':'Known fixed-point/BFS methods. Negative witnesses replayed; positive guards previously checked separately. Times are one-shot diagnostics.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for n in ('guard-witness-cases.py','guard-witness-replay.mjs','guard-witness.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    proc=subprocess.run(['node',str(out/'guard-witness-replay.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('memory','random','table','out'):p.add_argument(n,type=Path)
    v=p.parse_args();main(v.memory,v.random,v.table,v.out)
