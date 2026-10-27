"""Replay the actual solver-free witnesses beyond the short control corpus."""
import argparse,copy,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('direct_chain',HERE/'guard-import-direct.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d);i=d.i
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine()
    for old in json.loads((source/'manifest.json').read_text())['rows']:
        raw=source/old['source'];target=out/raw.name
        if not target.exists():shutil.copy2(raw,target)
        module=i.k.p.read(raw);compiled=wt.Module(engine,raw.read_bytes())
        for writes in ('public','may-public'):
            reads=old['proof']['hostSummaries'][0]['reads'];summaries={('env','touch'):{'reads':reads,'writes':writes}}
            model=i.parse(module,summaries);p=i.prepare(model,old['left'],old['right'],'public','reenter')
            if writes=='public':assert json.loads(json.dumps(p['proof']))==old['proof']
            values={c:259 for c in model['cells']};witness=d.witness(p,values)
            expected=reads=='public' or writes=='may-public';assert (witness is not None)==expected
            word=copy.deepcopy(witness['calls']) if witness else [{'name':'seed','writes':[]}]+[{'name':'step','writes':[{'block':0,'cells':[[i.g.BASE,256]]}]} for _ in range(old['length'])]
            assert [c['name'] for c in word]==['seed']+['step']*old['length']
            for call in word:
                for block in call['writes']:
                    allowed=[[[i.g.BASE,256]]]+([[]] if writes=='may-public' else [])
                    assert block['block']==0 and [list(c) for c in block['cells']] in allowed,block
            traces=[];counts={k:0 for k in ('apiCalls','hostCalls','cellWrites','pureTagCalls','preparationCalls')}
            for side in range(2):
                with wt.Store(engine) as store:
                    ex={};trace=[];current={}
                    def snapshot():
                        ref=ex['public'].get(store,0)
                        if isinstance(ref,wt.Func):counts['pureTagCalls']+=1;return ref(store)
                        return None
                    def touch():
                        counts['hostCalls']+=1;trace.append({'name':'touch','read':snapshot() if reads=='public' else None})
                        for cell,value in current.get(0,{}).items():
                            assert cell==i.g.BASE and value==256;ex['public'].set(store,0,None);counts['cellWrites']+=1
                    ex=wt.Instance(store,compiled,[wt.Func(store,wt.FuncType([],[]),touch)]).exports(store)
                    ex['retire' if side==0 else 'release_b'](store);counts['preparationCalls']+=1;output=[]
                    for call in word:
                        current={b['block']:dict(b['cells']) for b in call['writes']};trace=[]
                        try:ex[call['name']](store);outcome='return'
                        except wt.Trap:outcome='trap'
                        counts['apiCalls']+=1;output.append({'api':call['name'],'outcome':outcome,'hostTrace':trace,'public':snapshot()})
                    traces.append(output)
            difference=next((j+1 for j,(a,b) in enumerate(zip(*traces)) if a!=b),None);assert difference==(old['length']+1 if expected else None)
            rows.append({'name':old['name']+'-'+writes,'source':raw.name,'length':old['length'],'reads':reads,'writes':writes,'proof':p['proof'],
                'witness':witness,'word':word,'traces':traces,'difference':difference,**counts})
    result={'rows':rows,'contracts':len(rows),'negativeWitnesses':sum(r['witness'] is not None for r in rows),'maxApiLength':max(len(r['word']) for r in rows),
        **{key:sum(r[key] for r in rows) for key in counts}}
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    run=subprocess.run(['node',str(HERE/'guard-import-direct-chain.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    names=['guard-import-direct-chain.py','guard-import-direct-chain.mjs','guard-import-direct-chain-plan.md','guard-import-direct.py','guard-import.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py']
    for name in names:shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
