"""Seeded prospective controls; validate the frozen synthesis against real Wasm."""
import argparse,hashlib,importlib.util,itertools,json,random,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('guard_analysis',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def satisfies(guard,data):
    if guard is None:return False
    value=lambda t:t[1] if t[0]=='c' else data[t[1]]
    return all(value(x)==value(y) for x,y in guard)
def main(out):
    out.mkdir(parents=True,exist_ok=False);rng=random.Random(48879);engine=wt.Engine();rows=[];calls=0;unresolved=[]
    def operation():
        op=rng.choice(['memory.init','memory.copy','memory.fill','data.drop']);idx=rng.randrange(3)
        if op=='data.drop':return f'(data.drop {idx})'
        dst,src,n=rng.randrange(16),rng.randrange(4 if op=='memory.init' else 16),rng.randrange(4)
        return f'({op} '+(str(idx)+' ' if op=='memory.init' else '')+f'(i32.const {dst}) (i32.const {src}) (i32.const {n}))'
    for ci in range(96):
        name=f'random-{ci:03}';actions=[];funcs=[]
        for ai in range(rng.randint(1,3)):
            aname='api'+str(ai);actions.append(aname)
            ops=[operation() for _ in range(rng.randint(1,5))]
            if ci>=48 and ai==0:ops=['(memory.init 0 (i32.const 0) (i32.const 0) (i32.const 2))','(data.drop 0)',
              '(memory.init 2 (i32.const 0) (i32.const 0) (i32.const 1))']
            funcs.append(f'(func (export "{aname}") '+ ' '.join(ops)+')')
        raw=out/(name+'.wasm');k.p.compile_wat('(module (memory (export "memory") 1 1) (data "AB") (data "CD") (data "E") '+ ' '.join(funcs)+')',raw)
        module=k.p.read(raw);model=g.parse(module);left,right=[False,True,False],[True,True,False];proof=g.solve(model,left,right)
        for i in range(3):module.append(k.p.expr(f'(func (export "__guard_drop_{i}") (data.drop {i}))'))
        prepared=out/(name+'-prepared.wasm');k.p.compile_wat(k.p.w.emit(module),prepared);compiled=wt.Module(engine,prepared.read_bytes())
        baseline=bytes(65536);memoryfile=out/(name+'.bin');memoryfile.write_bytes(baseline);samples=[]
        sequences=[list(x) for n in range(1,5) for x in itertools.product(actions,repeat=n)]
        for si in range(6):
            data=bytearray(baseline)
            for cell in model['cells']:data[cell]=rng.randrange(256)
            if si<3 and proof['guard'] is not None:
                for x,y in proof['guard']:data[y[1]]=x[1] if x[0]=='c' else data[x[1]]
            positive=satisfies(proof['guard'],data);witness=None
            for seq in sequences:
                with wt.Store(engine) as store:
                    instances=[]
                    for flags in (left,right):
                        e=wt.Instance(store,compiled,[]).exports(store);e['memory'].write(store,data)
                        for i,alive in enumerate(flags):
                            if not alive:e[f'__guard_drop_{i}'](store)
                        instances.append(e)
                    for step,api in enumerate(seq):
                        outcomes=[]
                        for e in instances:
                            try:e[api](store);outcomes.append('return')
                            except wt.Trap:outcomes.append('trap')
                            calls+=1
                        if outcomes[0]!=outcomes[1] or instances[0]['memory'].read(store)!=instances[1]['memory'].read(store):
                            witness=seq[:step+1];break
                if witness:break
            if positive:assert witness is None,(name,si,witness)
            if not positive and witness is None:unresolved.append({'name':name,'sample':si,'iterations':proof['iterations']})
            samples.append({'patches':[[i,v] for i,v in enumerate(data) if v],'satisfies':positive,'witness':witness})
        rows.append({'name':name,'source':raw.name,'prepared':prepared.name,'memory':memoryfile.name,'proof':proof,
          'left':left,'right':right,'actions':actions,'samples':samples})
        if ci%16==15:print(json.dumps({'generated':ci+1,'unresolved':len(unresolved),'calls':calls}),flush=True)
    result={'seed':48879,'rows':rows,'depth':4,'wasmtimeApiCalls':calls,'boundedUnresolved':unresolved,
      'classifierSha256':hashlib.sha256((HERE/'guard-analysis.py').read_bytes()).hexdigest()}
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-random.py','guard-random.mjs','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    proc=subprocess.run(['node',str(out/'guard-random.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=90)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
