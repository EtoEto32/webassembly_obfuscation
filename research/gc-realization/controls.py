"""CLI rejection and deeper construction tests; separate from the 797-case screen."""
import argparse,json,subprocess,shutil
from pathlib import Path
from realize import ROOT,HERE,generate,Unsupported,Budget,Impossible
from experiment import model,wt,dump,digest
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];errors=[];files=[]
    tests=[('nonnull-null',model('array',True,False),[dict(type=0,values=[None])],Unsupported),('bad-target',model('array',True,True),[dict(type=0,values=[dict(node=5)])],Unsupported),('too-many-nodes',model('array',True,False),[dict(type=0,values=[])]*129,Budget),('immutable-cycle',model('array',False,False),[dict(type=0,values=[dict(node=0)])],Impossible)]
    for name,m,n,exc in tests:
        try:generate(m,n);errors.append(dict(name=name,kind='unexpected-accept'))
        except exc as e:rows.append(dict(name=name,status=type(e).__name__,reason=str(e)))
    # An array seed breaks a long chain of mandatory struct references.
    length=70;ts=[dict(kind='array',fields=[dict(mutable=True,value=dict(ref=dict(index=1),nullable=False))])]
    ts += [dict(kind='struct',fields=[dict(mutable=False,value=dict(ref=dict(index=i+1),nullable=False))]) for i in range(1,length-1)]
    ts += [dict(kind='array',fields=[dict(mutable=False,value=dict(ref=dict(index=0),nullable=False))])]
    m=dict(types=ts,groups=[dict(start=0,length=length)]);nodes=[dict(type=i,values=[dict(node=i+1)] if i<length-1 else []) for i in range(length)]
    for mode in ['staged','dfs-staged','all-deps']:
        g=generate(m,nodes,mode);p=out/('deep-'+mode+'.wasm');p.write_bytes(wt.wat2wasm(g.pop('wat')));files.append(p.name);rows.append(dict(name='deep',**g))
    dump(out/'request.json',dict(directory=str(out.resolve()),files=files));executions=[]
    for name,cmd in [('node',['node',str(ROOT/'research/gc-witness/run.cjs'),str(out/'request.json')]),('spidermonkey',[str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),str(ROOT/'research/gc-witness/run-sm.js'),str(out/'request.json')])]:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=30);cp.check_returncode();executions += [dict(engine=name,**r) for r in json.loads(cp.stdout)['rows']]
    engine=wt.Engine()
    for file in files:
        s=wt.Store(engine);i=wt.Instance(s,wt.Module(engine,(out/file).read_bytes()),[]);executions.append(dict(engine='wasmtime',file=file,status='ok',result=i.exports(s)['run'](s)))
    for r in executions:
        if r['status']!='ok' or r.get('result')!=1:errors.append(r)
    dump(out/'rows.json',rows);dump(out/'executions.json',executions);dump(out/'summary.json',dict(rejections=len(tests),deep_binaries=len(files),deep_calls=len(executions),errors=errors))
    for p in [Path(__file__),HERE/'realize.py']:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print((out/'summary.json').read_text());assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
