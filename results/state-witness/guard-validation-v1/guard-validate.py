"""Validate symbolic guards on measured and perturbed original-program states."""
import argparse,base64,hashlib,importlib.util,itertools,json,random,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('guard_analysis',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def satisfies(guard,data):
    if guard is None:return False
    value=lambda t:t[1] if t[0]=='c' else data[t[1]]
    return all(value(x)==value(y) for x,y in guard)
def main(inputs,measured,proofs,out):
    out.mkdir(parents=True,exist_ok=False);rng=random.Random(7401);engine=wt.Engine();rows=[];calls=0
    old=json.loads((measured/'results.json').read_text())['rows']
    for row in json.loads((proofs/'results.json').read_text())['rows']:
        proof=row['proof']
        if proof['status']=='unsupported':continue
        stem=f'case-{row["id"]}-stop-{row["stopAt"]}';original=inputs/f'case-{row["id"]:02}/original.wasm'
        m=k.p.read(original);model=g.parse(m);states=proof['states'][0];left,right=states['left'],states['right']
        prev=next(x for x in old if x['id']==row['id'] and x['stopAt']==row['stopAt'])
        observed=json.loads((measured/prev['stateFile']).read_text());baseline=base64.b64decode(observed['baseline']['memory'])
        assert baseline==base64.b64decode(observed['restored']['memory']);assert len(baseline)==proof['memoryBytes']
        assert satisfies(proof['guard'],baseline)==(prev['finiteClosure']['status']=='closed-original-api-model')
        for i in range(len(left)):m.append(k.p.expr(f'(func (export "__guard_drop_{i}") (data.drop {i}))'))
        prepared=out/(stem+'.wasm');k.p.compile_wat(k.p.w.emit(m),prepared);compiled=wt.Module(engine,prepared.read_bytes())
        memoryfile=out/(stem+'.bin');memoryfile.write_bytes(baseline)
        actions=[a['name'] for a in model['actions'] if not a['readonly']]
        sequences=[list(x) for n in range(1,5) for x in itertools.product(actions,repeat=n)];samples=[]
        for i in range(13):
            data=bytearray(baseline)
            if i:
                for cell in model['cells']:data[cell]=rng.randrange(256)
                if i<=6 and proof['guard'] is not None:
                    for x,y in proof['guard']:data[y[1]]=x[1] if x[0]=='c' else data[x[1]]
            positive=satisfies(proof['guard'],data);witness=None
            for seq in sequences:
                traces=[]
                for alive in (left,right):
                    with wt.Store(engine) as store:
                        e=wt.Instance(store,compiled,[]).exports(store);e['memory'].write(store,data)
                        for index,live in enumerate(alive):
                            if not live:e[f'__guard_drop_{index}'](store)
                        trace=[]
                        for name in seq:
                            try:e[name](store);outcome='return'
                            except wt.Trap:outcome='trap'
                            trace.append((outcome,bytes(e['memory'].read(store))));calls+=1
                        traces.append(trace)
                if traces[0]!=traces[1]:witness=seq;break
            assert (witness is None)==positive,(stem,i,positive,witness)
            samples.append({'patches':[[j,b] for j,b in enumerate(data) if b!=baseline[j]],'satisfies':positive,'witness':witness})
        rows.append({'name':stem,'prepared':prepared.name,'memory':memoryfile.name,'memorySha256':hashlib.sha256(baseline).hexdigest(),
          'proof':proof,'left':left,'right':right,'actions':actions,'samples':samples})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'depth':4,'wasmtimeApiCalls':calls,'seed':7401},indent=2))
    for n in ('guard-validate.py','guard-validate.mjs','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    proc=subprocess.run(['node',str(out/'guard-validate.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=90)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inputs',type=Path);p.add_argument('measured',type=Path);p.add_argument('proofs',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.inputs,v.measured,v.proofs,v.out)
