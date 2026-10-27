import json,subprocess,statistics,hashlib
from pathlib import Path
from datetime import datetime,timezone
import prototype as q
import recover as r
from run import save
p=q.p;ROOT=q.ROOT;HERE=Path(__file__).resolve().parent;R=ROOT/'results/invention-20261019'
def read(d,n):return json.loads((R/d/n).read_text(encoding='utf-8'))
def main():
    out=R/'concurrent-frontier-final-audit-v1';out.mkdir(exist_ok=False);rows=read('concurrent-frontier-v2','manifest.json');old=read('concurrent-frontier-v1','manifest.json');checks=[]
    for row,prev in zip(rows,old):
        assert p.digest(R/'concurrent-frontier-v2'/row['source'])==p.digest(R/'concurrent-frontier-v1'/prev['source'])
        for key,hashkey in [('file','sha256'),('recovered','recovered_sha256')]:
            if key not in row:continue
            f=R/'concurrent-frontier-v2'/row[key];assert p.digest(f)==row[hashkey]==prev[hashkey]
        if row['mode']=='atomic' and row['opt']=='O3':
            wat=p.w.tool('wasm2wat',[R/'concurrent-frontier-v2'/row['file'],'--enable-threads'])
            assert 'i32.atomic.rmw.cmpxchg' in wat
        checks.append(row['file'])
    c=read('concurrent-frontier-v2','correctness.json');assert c['total_calls']==101376 and c['mismatches']==0
    a=read('concurrent-frontier-v2','attacks.json');assert len(a)==24 and all(x['graph_equal'] for x in a)
    verify=read('concurrent-frontier-verify-v2','summary.json');assert verify['wabt_checks']==240 and verify['all_wabt_match']
    v=read('concurrent-frontier-verify-v2','native.json');assert v['mismatches']==0 and v['negative']['differences']>0
    reject=read('concurrent-frontier-verify-v2','rejections.json');assert any('cyclic dependency' in x['reason'] for x in reject)
    ms=read('concurrent-frontier-performance-v2','measurements.json');assert len(ms)==108
    for x in ms:assert statistics.median(x['samples_ns'])==x['median_ns']
    # Independent JS loop checks the measured Wasm-loop checksum against source.
    script='''const fs=require('fs');const rows=JSON.parse(fs.readFileSync(process.argv[1]));const dir=process.argv[2];const out={};for(const r of rows){const key=r.kernel+r.k;if(key in out)continue;const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(dir+'/'+r.source))).exports.run;let h=137;for(let i=0;i<512;i++)h=(f(h,i,h^1431655765)^i)|0;out[key]=h;}console.log(JSON.stringify(out));'''
    source=R/'concurrent-frontier-v2';expected=json.loads(subprocess.check_output(['node','-e',script,str(source/'manifest.json'),str(source)],text=True))
    for x in ms:
        if x['kind']=='local':assert x['checksum']==expected[x['kernel']+str(x['k'])]
    critical={'prototype.py','recover.py','run.py','harness.cjs','worker.cjs','check.cjs'}
    for item in read('concurrent-frontier-v2','sources.json'):
        if Path(item['path']).name in critical:assert p.digest(ROOT/item['path'])==item['sha256']
    for name in ('measure.py','measure.cjs','prototype.py','harness.cjs','worker.cjs'):
        assert p.digest(HERE/name)==p.digest(R/'concurrent-frontier-performance-v2'/'sources'/name)
    # Freeze current scripts, including supplemental verification/report code.
    sources=[dict(path=str(f.relative_to(ROOT)),sha256=p.digest(f)) for f in HERE.iterdir() if f.is_file()]
    profile_start=__import__('time').perf_counter();allowed=r.profiles();profile_ms=(__import__('time').perf_counter()-profile_start)*1000
    assert allowed==read('concurrent-frontier-v2','profiles.json')
    save(out/'audit.json',dict(status='passed',utc=datetime.now(timezone.utc).isoformat(),targets=len(checks),recovered=24,reproduction='v1/v2 independently generated identical target and recovered bytes',main_calls=c['total_calls'],extra_calls=v['total_calls'],wabt_checks=verify['wabt_checks'],processes=108,independent_local_checksum_checks=54,profile_generation_ms=profile_ms,source_hashes=sources,goal_complete=False))
    print(json.dumps(dict(status='passed',targets=len(checks),main_calls=c['total_calls'],extra_calls=v['total_calls'])))
if __name__=='__main__':main()
