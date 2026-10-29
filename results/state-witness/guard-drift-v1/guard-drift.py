"""Small source-level explanation of a prospective mixed-resource finding."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('protocol',HERE/'guard-protocol.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();rows=[];calls=prefixes=0
    for name,byte,trap in [('clear-traps',0,True),('clear-returns',0,False),('clear-preserves',65,True)]:
        raw=out/(name+'.wasm');end='(memory.init 1 (i32.const 0) (i32.const 0) (i32.const 1))' if trap else ''
        wat=f'''(module (memory (export "memory") 1 1) (data "A") (data "B") (data (i32.const 0) "A")
          (func (export "retire") (data.drop 0) (data.drop 1)) (func (export "release_b") (data.drop 1))
          (func (export "mask") (memory.init 0 (i32.const 0) (i32.const 0) (i32.const 1)) (data.drop 0)
            (memory.init 1 (i32.const 0) (i32.const 0) (i32.const 1)))
          (func (export "clear") (memory.fill (i32.const 0) (i32.const {byte}) (i32.const 1)) {end}))'''
        k.p.compile_wat(wat,raw);model=p.c.parse(k.p.read(raw));compiled=wt.Module(engine,raw.read_bytes())
        assert {x.name for x in compiled.exports}=={'memory','retire','release_b','mask','clear'}
        for contract in ('full','public','returns'):
            for protocol in ('reenter','terminal'):
                prepared=p.prepare(model,[False,False,False],[True,False,False],contract,protocol);proof=prepared['proof'];witness=p.extract(prepared,{0:65})
                expected=[] if contract=='returns' else None if name=='clear-returns' or name=='clear-traps' and protocol=='reenter' else [[['c',65],['m',0]]]
                assert proof['guard']==expected
                sequences=[[x['name'] for x in witness['calls']]] if witness else [['mask'],['clear'],['clear','mask']];traces=[]
                if witness:assert witness['shortestLength']==2
                for sequence in sequences:
                    with wt.Store(engine) as store:
                        pair=[wt.Instance(store,compiled,[]).exports(store) for _ in range(2)];pair[0]['retire'](store);pair[1]['release_b'](store);prefixes+=2;trace=[];difference=None
                        for i,api in enumerate(sequence):
                            outcomes=[]
                            for e in pair:
                                try:outcomes.append(['return',e[api](store)])
                                except wt.Trap:outcomes.append(['trap'])
                                calls+=1
                            memories=[bytes(e['memory'].read(store)) for e in pair];equal=memories[0]==memories[1]
                            trace.append({'api':api,'outcomes':outcomes,'firstBytes':[m[0] for m in memories],'memoryEqual':equal})
                            if outcomes[0]!=outcomes[1] or contract!='returns' and not equal:difference=i+1;break
                            if protocol=='terminal' and outcomes[0][0]=='trap':break
                        assert difference==(2 if witness else None);traces.append({'sequence':sequence,'difference':difference,'trace':trace})
                rows.append({'name':name+'-'+contract+'-'+protocol,'source':raw.name,'proof':proof,'witness':witness,'traces':traces})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'wasmtimeApiCalls':calls,'preparationApiCalls':prefixes,
      'scope':'Hand-reduced mechanism from mixed-15; not claimed to be a formally minimized program. Original exports only; both initial states reached by original prefixes.'},indent=2))
    for n in ('guard-drift.py','guard-drift.mjs','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    run=subprocess.run(['node',str(HERE/'guard-drift.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));(out/'sha256.json').write_text(json.dumps({q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in out.iterdir()},indent=2));assert run.returncode==0,run.stderr;print(run.stdout)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
