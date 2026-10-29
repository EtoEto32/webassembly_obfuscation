"""Explicit continuation model of entry fixtures, not resume-PC verification."""
import argparse,copy,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('check_import',HERE/'guard-import-check.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q);i=q.i
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


def main(source,external,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine();checks=[];runtime=[];calls=hostcalls=0
    externalrows=json.loads((external/'results.json').read_text())['rows']
    for original in json.loads((source/'manifest.json').read_text())['rows']:
        name=original['name'];src=source/original['original'];raw=out/(name+'.wasm');shutil.copy2(src,raw);module=i.k.p.read(raw)
        body=i.flatten([n for n in i.k.p.section(module,'func')[0][1:] if n[0] not in i.k.p.DECL])
        assert body[:3]==[['data.drop','0'],['nop'],['data.drop','1']]
        assert body[3]==['call','0'];offsets={'entry':3};left=[False,False,False]
        for live_b in (False,True):
            right=[True,live_b,False];binaries=[]
            for side,flags in enumerate((left,right)):
                derived=copy.deepcopy(module);f=i.k.p.section(derived,'func')[0]
                f[:]=['func']+[n for n in f[1:] if n[0] in i.k.p.DECL]+[['data.drop',str(j)] for j,flag in enumerate(flags) if not flag]+copy.deepcopy(body[3:])
                dst=out/(name+'-'+str(int(live_b))+'-'+str(side)+'.wasm');i.k.p.compile_wat(i.k.p.w.emit(derived),dst);i.k.p.tool('wasm-validate',[dst]);binaries.append(dst)
            for writes in ('none','public'):
                summary={('env','touch'):{'reads':'none','writes':writes}}
                model=i.parse(module,summary,offsets);prepared=i.prepare(model,left,right,'public','terminal')
                entire=i.prepare(i.parse(module,summary),left,right,'public','terminal');assert entire['proof']['status']=='unconditional'
                status='unconditional' if name in ('repair','zero') else 'conditional' if writes=='none' else 'impossible'
                assert prepared['proof']['status']==status,(name,writes,prepared['proof'])
                runchecks=q.check(model,prepared);checks.extend(runchecks)
                rows.append({'name':name+'-'+str(int(live_b))+'-'+writes,'source':raw.name,'left':left,'right':right,'proof':prepared['proof'],'wholeEntryGuard':entire['proof']['guard']})
                runs=[]
                for binary in binaries:
                    with wt.Store(engine) as store:
                        ex={};trace=[]
                        def touch():
                            nonlocal hostcalls
                            trace.append({'name':'touch','write':writes=='public'});hostcalls+=1
                            if writes=='public':ex['memory'].write(store,b'\0',7)
                        f=wt.Func(store,wt.FuncType([],[]),touch);ex=wt.Instance(store,wt.Module(engine,binary.read_bytes()),[f]).exports(store)
                        try:ex['entry'](store);outcome={'trap':False}
                        except wt.Trap:outcome={'trap':True}
                        calls+=1;memory=bytes(ex['memory'].read(store));runs.append({'outcome':outcome,'hostTrace':trace,'memory':{'sha256':hashlib.sha256(memory).hexdigest(),'bytes7to10':list(memory[7:11])}})
                erow=next(r for r in externalrows if r['name']==name and r['backend']=='migrate' and r['write']==(writes=='public'))
                assert runs[0]==erow['reference'],(name,'original continuation')
                for stop in (1,2):
                    actual=next(r for r in erow['scenarios'] if r['stop']==stop)
                    assert runs[1]=={k:actual[k] for k in ('outcome','hostTrace','memory')},(name,'restored continuation',stop)
                assert (runs[0]==runs[1])==(name in ('repair','zero') or writes=='none')
                runtime.append({'name':rows[-1]['name'],'binaries':[b.name for b in binaries],'write':writes=='public','runs':runs,'matchesExternalStops':[1,2]})
    manifest={'rows':rows,'runtime':runtime,'apiCalls':calls,'hostCalls':hostcalls,'checks':checks,'unsat':sum(c['answer']=='unsat' for c in checks),'unknown':sum(c['answer']=='unknown' for c in checks),
        'scope':'Explicit normalized entry offset 3. Segment hypotheses A dead/live, B either dead/live. Not automatic extraction or validation of restorer continuation metadata.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    run=subprocess.run(['node',str(HERE/'guard-import-continuation.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    for file in ('guard-import-continuation.py','guard-import-continuation.mjs','guard-import.py','guard-import-check.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/file,out/file)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('external',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.external,v.out)
