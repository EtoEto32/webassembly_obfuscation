"""Audit the recorded feasibility experiment, not protection efficacy."""
import argparse,json,shutil
from pathlib import Path
import prototype as q
from run import save
p=q.p

def read(d,name):return json.loads((Path(d)/name).read_text(encoding='utf-8'))
def copy_func(f):
    m=p.w.parse(p.w.tool('wasm2wat',[f,'--fold-exprs','--no-debug-names']))
    idx=int(next(x[2][1] for x in m[1:] if x[0]=='export' and x[1]=='"copy"'))
    fs=[x for x in m[1:] if x[0]=='func']
    # Ignore only redundant type-section index, retaining parameters and all code.
    return [x for x in fs[idx] if not isinstance(x,list) or x[0]!='type']

def main(main,replay,model,verification,out):
    main,replay,verification,out=map(Path,(main,replay,verification,out));out.mkdir(parents=True,exist_ok=False)
    a,b=read(main,'manifest.json'),read(replay,'manifest.json');assert len(a)==len(b)==32
    hashes=[];copy_checks=[]
    for x,y in zip(a,b):
        assert all(x[k]==y[k] for k in ('file','source','mode','opt','alignment','legal','seed'))
        for key,hk in [('file','sha256'),('probe','probe_sha256')]:
            digest=p.digest(main/x[key]);assert digest==x[hk]==y[hk]==p.digest(replay/y[key])
            hashes.append(dict(file=x[key],sha256=digest))
        assert p.digest(main/x['source'])==p.digest(replay/y['source'])
        ok=copy_func(main/x['file'])==copy_func(main/x['source']);assert ok
        copy_checks.append(dict(file=x['file'],copy_function_unchanged=ok))
    native=read(main,'native.json');assert native==read(replay,'native.json')
    assert len(native['cases'])==242 and native['positive_mismatches']==0
    assert native['negative_with_counterexample']==12 and native['total_calls']==255552
    assert all(x['bad_traps']==0 for x in native['results'])
    assert len(read(main,'refusals.json'))==6
    finite=json.loads(Path(model).read_text());assert all(x['class_equal'] for x in finite['rows'])
    assert finite['directed']['class_equal'] and finite['counterexample']['aligned_pair_checks']==3584
    cross=read(verification,'cross-engine.json');assert len(cross)==32 and all(x['match'] for x in cross)
    sources=[]
    for s in read(replay,'sources.json'):
        f=q.ROOT/s['path'];snapshot=replay/'sources'/s['snapshot']
        assert p.digest(f)==s['sha256']==p.digest(snapshot);sources.append(s)
    # audit.py was added after the replay; preserve its exact executed version too.
    shutil.copyfile(Path(__file__),out/'audit.py');sources.append(dict(path=str(Path(__file__).relative_to(q.ROOT)),sha256=p.digest(Path(__file__))))
    save(out/'binary-hashes.json',hashes);save(out/'copy-functions.json',copy_checks);save(out/'sources.json',sources)
    save(out/'summary.json',dict(passed=True,byte_identical_targets=32,byte_identical_probes=32,unchanged_copy_functions=32,identical_native_results=True,model_matches_classification=True,cross_engine_checks=128,unsupported_profile_refusals=6,goal_complete=False,claim='feasibility gate only; no protection advantage or patent novelty established'))
    print(json.dumps(read(out,'summary.json')))

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for n in ('main','replay','model','verification','output'):a.add_argument(n)
    v=a.parse_args();main(v.main,v.replay,v.model,v.verification,v.output)
