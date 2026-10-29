"""Reproduce the small host-contract artifact from its own source tree."""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    expected=json.loads((root/'expected.json').read_text())
    for name,value in json.loads((root/'source-sha256.json').read_text()).items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value,name
    here=root/'research/state-witness';sys.path.insert(0,str(here))
    import prototype as k
    assert k.ROOT==root and k.p.ROOT==root and k.p.w.ROOT==root,'source dependency escaped artifact'
    output=root/'results/state-witness';output.mkdir(parents=True,exist_ok=False)
    logs=[]
    def run(script,*args):
        command=[sys.executable,str(here/script),*map(str,args)]
        result=subprocess.run(command,cwd=root,capture_output=True,text=True,encoding='utf8',timeout=120)
        logs.append({'script':script,'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if result.returncode:
            (output/'failure.json').write_text(json.dumps(logs,indent=2));raise RuntimeError(result.stderr)
    run('guard-environment-controls.py',output/'controls')
    run('guard-environment-interleave.py',output/'interleave')
    run('guard-environment-check.py',output/'interleave',output/'interleave-check')
    store=output/'store.json';store.write_text(json.dumps({'cells':[[1<<32,257],[2<<32,258],[(2<<32)+1,256]]}))
    run('diagnose.py',output/'interleave/interleave.wasm',output/'diagnosis.json','--left','01000','--right','11000','--observation','public','--after-trap','reenter','--host-writes','public','--store',store)
    compared=[]
    for name,digest in expected['binaries'].items():
        actual=hashlib.sha256((output/name).read_bytes()).hexdigest();assert actual==digest,name;compared.append(name)
    controls=json.loads((output/'controls/results.json').read_text());interleave=json.loads((output/'interleave/results.json').read_text());checker=json.loads((output/'interleave-check/results.json').read_text());diagnosis=json.loads((output/'diagnosis.json').read_text())
    for key,value in expected['controls'].items():assert controls[key]==value,(key,controls[key])
    for key,value in expected['interleave'].items():assert interleave[key]==value,(key,interleave[key])
    assert checker['contracts']==4 and checker['unsat']==44 and checker['unknown']==0
    assert diagnosis['status']=='impossible' and diagnosis['witness']['shortestLength']==3 and diagnosis['witness']['hostWrites']==1
    result={'status':'passed','byteIdenticalBinaries':len(compared),'compared':compared,'controls':expected['controls'],'interleave':expected['interleave'],
        'unsatObligations':checker['unsat'],'sourceTree':str(root),'wabtRoot':str(k.p.w.WABT),'logs':logs,
        'scope':'Small original-export controls and CLI only; not the large corpus, performance or external migration reproductions.'}
    (output/'reproduction.json').write_text(json.dumps(result,indent=2));print(json.dumps({key:result[key] for key in ('status','byteIdenticalBinaries','unsatObligations')}))

if __name__=='__main__':main()
