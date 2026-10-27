"""Reproduce import contracts from the self-contained source artifact."""
import hashlib,json,subprocess,sys
from pathlib import Path


def main():
    root=Path(__file__).resolve().parent;here=root/'research/state-witness';sys.path.insert(0,str(here));expected=json.loads((root/'expected.json').read_text())
    for name,value in json.loads((root/'source-sha256.json').read_text()).items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value,name
    import prototype as k
    assert k.ROOT==root and k.p.ROOT==root and k.p.w.ROOT==root,'source dependency escaped artifact'
    out=root/'results/state-witness';out.mkdir(parents=True,exist_ok=False);logs=[]
    def run(script,*args):
        result=subprocess.run([sys.executable,str(here/script),*map(str,args)],cwd=root,text=True,encoding='utf8',capture_output=True,timeout=120)
        logs.append({'script':script,'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if result.returncode:(out/'failure.json').write_text(json.dumps(logs,indent=2));raise RuntimeError(result.stderr)
    run('guard-import-controls.py',out/'controls')
    for stem in ('check','ablation','finite','generic'):run('guard-import-'+stem+'.py',out/'controls',out/stem)
    run('guard-import-boundary.py',out/'boundary');run('guard-import-chain.py',out/'chain')
    run('guard-import-cached.py',out/'controls',out/'cached')
    run('guard-import-controls.py',out/'may','--writes','may-public')
    for script,name in [('guard-import-check.py','may-check'),('guard-import-finite.py','may-finite'),('guard-import-cached.py','may-generic')]:run(script,out/'may',out/name)
    run('guard-import-may-pair.py',out/'may-pair');run('guard-import-may-witness.py',out/'may-pair',out/'may-witness')
    for name,value in expected['binaries'].items():assert hashlib.sha256((out/name).read_bytes()).hexdigest()==value,name
    summaries={}
    for name,fields in expected['results'].items():
        actual=json.loads((out/name/expected.get('resultFiles',{}).get(name,'results.json')).read_text())
        for key,value in fields.items():assert actual[key]==value,(name,key,actual[key])
        summaries[name]=fields
    result={'status':'passed','byteIdenticalBinaries':len(expected['binaries']),'checks':summaries,'sourceTree':str(root),'wabtRoot':str(k.p.w.WABT),'logs':logs,
        'scope':'Small import profile controls, finite and generic solvers; no external restorer or natural application reproduction.'}
    (out/'reproduction.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':'passed','byteIdenticalBinaries':result['byteIdenticalBinaries']}))


if __name__=='__main__':main()
