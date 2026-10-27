import argparse,json,shutil,subprocess
from pathlib import Path
import prototype as q
from census import census
def read(d,f):return json.loads((Path(d)/f).read_text(encoding='utf-8'))
def main(out):
    root=q.ROOT/'results/invention-20261019';a=root/'type-identity-v3';b=root/'type-identity-replay-v1';extra=root/'type-identity-extra-v1';out=Path(out);out.mkdir(parents=True,exist_ok=False)
    rows=read(a,'manifest.json');replay=read(b,'manifest.json');assert len(rows)==len(replay)==42
    hashes=[];counts=[]
    for x,y in zip(rows,replay):
        assert x['file']==y['file']
        for k,h in [('file','sha256'),('recovered','recovered_sha256')]:
            sha=q.digest(a/x[k]);assert sha==x[h]==y[h]==q.digest(b/y[k]);hashes.append(dict(file=x[k],sha256=sha))
        c=census(a/x['file']);counts.append(dict(file=x['file'],**c))
        if x['mode'] in ('gc','groups'):
            expected=(x['states']+x['siblings'])*(x['groups'] if x['opt']=='raw' else 1)
            assert c['structs']==expected
        assert census(a/x['recovered'])['structs']==0
    assert read(a,'checks.json')==read(b,'checks.json')
    assert read(a,'checks.json')['wasm_calls']==203490 and read(a,'checks.json')['mismatches']==0
    assert read(extra,'summary.json')['wasm_calls']==58140 and len(read(extra,'refusals.json'))==6
    for x in read(extra,'manifest.json'):
        for k,h in [('file','sha256'),('recovered','recovered_sha256')]:assert q.digest(extra/x[k])==x[h]
    assert read(root/'type-identity-verify-v2','summary.json')['all_pass']
    assert read(root/'type-identity-extra-verify-v1','summary.json')['all_pass']
    perf=read(root/'type-identity-performance-v2','native.json');assert len(perf)==126
    for kernel in ('mod5','pattern','random16'):
        checks={x['checksum'] for x in perf if x['file'].startswith(kernel+'-')};assert len(checks)==1
    assert read(root/'type-identity-null-v2','result.json')['values']==[1,0]
    assert read(root/'type-identity-null-v3','result.json')['values']==[1,1]
    sources=[]
    for s in read(b,'sources.json'):
        assert q.digest(q.ROOT/s['path'])==s['sha256']==q.digest(b/'sources'/s['snapshot']);sources.append(s)
    for name in ('audit.py','report.py'):
        f=Path(__file__).parent/name;shutil.copyfile(f,out/name);sources.append(dict(path=str(f.relative_to(q.ROOT)),sha256=q.digest(f)))
    cpu=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({cpu:require("os").cpus()[0].model,logical:require("os").cpus().length,v8:process.versions.v8}))'],text=True))
    q.save(out/'environment.json',cpu);q.save(out/'type-census.json',counts);q.save(out/'binary-hashes.json',hashes);q.save(out/'sources.json',sources)
    q.save(out/'summary.json',dict(passed=True,reproduced_targets=42,reproduced_recoveries=42,main_native_calls=203490,additional_native_calls=58140,binaryen_run_checks=648,binaryen_transition_accept_checks=519,node_transition_accept_checks=519,negative_group_witnesses=len(read(a,'negative.json')),refusals=6,performance_processes=126,goal_complete=False,claim='Type-group expansion gives no established protection advantage over the ordinary GC token control.'))
    print(json.dumps(read(out,'summary.json')))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
