"""Regression plus delayed-public-observation controls for relational guards."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load('contract','guard-contract.py');wc=load('witness_cases','guard-witness-cases.py')
def main(witness,audit,out):
    out.mkdir(parents=True,exist_ok=False);regressions=[];counts={kind:{'equal':0,'different':0} for kind in ('full','public','returns')}
    audited={r['name']:r for r in json.loads((audit/'results.json').read_text())['rows']}
    for row in json.loads((witness/'manifest.json').read_text())['rows']:
        model=c.parse(k.p.read(witness/row['source']));profiles={kind:c.prepare(model,row['left'],row['right'],kind) for kind in counts}
        assert profiles['full']['proof']['guard']==row['proof']['guard']
        rc=audited[row['name']]['returnTrapContract']['status']
        if rc!='unsupported-read-api':assert profiles['returns']['proof']['status']==('unconditional' if rc=='equivalent-under-return-trap-contract' else 'impossible')
        samples=[]
        for s in row['samples']:
            values={i:0 if i<c.g.BASE else 256 for i in model['cells']};values.update(dict(s['patches']));got={kind:c.extract(p,values) for kind,p in profiles.items()}
            assert (got['full'] is None)==(s['witness'] is None)
            if got['full']:assert got['full']['shortestLength']==s['witness']['shortestLength']
            for kind,r in got.items():counts[kind]['equal' if r is None else 'different']+=1
            samples.append(got)
        regressions.append({'name':row['name'],'proofs':{kind:r['proof'] for kind,r in profiles.items()},'samples':samples})
    assert counts['public']=={'equal':634,'different':330},counts
    (out/'regressions.json').write_text(json.dumps({'rows':regressions,'counts':counts},indent=2))
    rows=[]
    for n in (1,2,4,8,16,32):
        for reset in (False,True):
            name=f'delayed-{n:02}-'+('repair' if reset else 'expose');raw=out/(name+'.wasm')
            before=f'(table.fill 1 (i32.const 0) (ref.func $a) (i32.const {n}))' if reset else ''
            wat=f'''(module (table (export "public") 1 1 funcref) (table {n} {n} funcref)
              (func $a (export "a") (result i32) (i32.const 101)) (func $b (export "b") (result i32) (i32.const 202))
              (elem func $a) (elem func $b)
              (func (export "mask") (table.init 1 0 (i32.const {n-1}) (i32.const 0) (i32.const 1)) (elem.drop 0) (table.init 1 1 (i32.const 0) (i32.const 0) (i32.const 1)))
              (func (export "copy") (table.copy 1 1 (i32.const 0) (i32.const 1) (i32.const {n-1})))
              (func (export "publish") {before} (table.copy 0 1 (i32.const 0) (i32.const 0) (i32.const 1))))'''
            k.p.compile_wat(wat,raw);module=k.p.read(raw);model=c.parse(module);left,right=[False,False],[True,False]
            binary=out/(name+'-prepared.wasm');wc.prepare_module(module,model,binary)
            for kind in counts:
                prepared=c.prepare(model,left,right,kind);proof=prepared['proof'];expected=[] if kind=='returns' or kind=='public' and reset else [[['c',257],['m',2*c.g.BASE+n-1]]]
                assert proof['guard']==expected,(name,kind,proof['guard'],expected)
                samples=[]
                for last in (257,258):
                    values={i:257 for i in model['cells']};values[2*c.g.BASE+n-1]=last;found=c.extract(prepared,values)
                    if found:assert len(found['calls'])==(1 if kind=='full' else n+1),(name,kind,found)
                    suffix=[{'name':'copy','args':[]} for _ in range(n-1)]+[{'name':'publish','args':[]}]
                    mask={'name':'mask','args':[]};publish={'name':'publish','args':[]}
                    tests=[[mask], [mask]+suffix,[publish,mask]+suffix,[mask]+suffix+[mask,publish]]
                    samples.append({'patches':[[i,v] for i,v in sorted(values.items())],'witness':found,'positiveSequences':tests if found is None else []})
                rows.append({'name':name+'-'+kind,'source':raw.name,'prepared':binary.name,'proof':proof,'left':left,'right':right,'samples':samples})
    name='private-byte-reader';raw=out/(name+'.wasm')
    k.p.compile_wat('''(module (memory 1 1) (data "A") (data "B")
      (func (export "mask") (memory.init 0 (i32.const 0) (i32.const 0) (i32.const 1)) (data.drop 0) (memory.init 1 (i32.const 0) (i32.const 0) (i32.const 1)))
      (func (export "read") (param i32) (result i32) (i32.load8_u (local.get 0))))''',raw)
    module=k.p.read(raw);model=c.parse(module);binary=out/(name+'-prepared.wasm');wc.prepare_module(module,model,binary)
    for kind in counts:
        prepared=c.prepare(model,[False,False],[True,False],kind);proof=prepared['proof'];assert proof['guard']==[[['c',65],['m',0]]]
        samples=[]
        for byte in (65,66):
            found=c.extract(prepared,{0:byte})
            if found:assert len(found['calls'])==(1 if kind=='full' else 2)
            sequences=[[{'name':'mask','args':[]},{'name':'read','args':[i]}] for i in (0,1,65536,-1)]
            samples.append({'patches':[[0,byte]],'witness':found,'positiveSequences':sequences if found is None else []})
        rows.append({'name':name+'-'+kind,'source':raw.name,'prepared':binary.name,'proof':proof,'left':[False,False],'right':[True,False],'samples':samples})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'regressionCounts':counts},indent=2))
    for n in ('guard-contract-cases.py','guard-contract-replay.mjs','guard-contract.py','guard-witness-cases.py','guard-witness.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    proc=subprocess.run(['node',str(out/'guard-contract-replay.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('witness','audit','out'):p.add_argument(n,type=Path)
    v=p.parse_args();main(v.witness,v.audit,v.out)
