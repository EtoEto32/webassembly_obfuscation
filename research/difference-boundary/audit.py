"""Saved-result audit and O3-input acceptance check; creates a fresh output folder."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import prototype as p
from run import save,command,HERE

BASE=p.ROOT/'results/invention-20261019'
def read(folder,name):return json.loads((BASE/folder/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);o=ap.parse_args();out=o.output;out.mkdir(parents=True,exist_ok=False)
    hashes={};calls=traps=0;attacks=[];checked=0
    for folder in ['difference-boundary-v2','difference-boundary-edge-v1']:
        m=read(folder,'manifest.json');c=read(folder,'correctness.json');a=read(folder,'attacks.json')
        assert len(m['files'])==c['binaries']==60 and c['mismatches']==0
        assert c['copies']==sum(q['steps'] for q in c['rows'])*2
        assert c['digests']==c['copies']+120 and c['calls']==c['copies']+c['digests']
        assert c['trapCopies']==sum(q['trappingSteps'] for q in c['rows'])*2
        calls+=c['calls'];traps+=c['trapCopies'];attacks+=a
        for q in m['files']:
            path=BASE/folder/q['path'];assert sha(path)==q['sha256'];assert path.stat().st_size==q['bytes']
            hashes[str(path.relative_to(p.ROOT))]=sha(path)
            probe=BASE/folder/q['probe'];hashes[str(probe.relative_to(p.ROOT))]=sha(probe)
            if q['recovered']:assert path.read_bytes()==(BASE/folder/(q['dataset']+'.plain.raw.wasm')).read_bytes()
            checked+=1
        for name in m['datasets']:
            arrays=[p.read_data(BASE/folder/(name+'.'+mode+'.O3.wasm')) for mode in ['roundtrip','two','shared']]
            assert arrays[0]==arrays[1]==arrays[2]
    assert (checked,calls,traps)==(120,256080,20080)
    assert Counter(q['status'] for q in attacks)=={'recovered':60}
    assert sum(q['mode']!='plain' for q in attacks)==48
    replay=read('difference-boundary-v2','replay.json');assert len(replay['same'])==60 and not replay['different']
    for q in read('difference-boundary-v2','manifest.json')['files']:
        assert sha(BASE/'difference-boundary-v1'/q['path'])==q['sha256']
    sources=[HERE/'prototype.py',HERE/'run.py',HERE/'check.cjs',p.ROOT/'research/zero-extent/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
    env=read('difference-boundary-v2','environment.json')
    for path in sources:
        name=path.parent.name+'_'+path.name
        assert sha(path)==env['sources'][name]==sha(BASE/'difference-boundary-v2/sources'/name)
        assert sha(path)==sha(BASE/'difference-boundary-edge-v1/sources'/name)
    for folder,names in [('difference-boundary-batch-v1',['measure.py','batch.cjs']),('difference-boundary-verify-v1',['verify.py']),('difference-boundary-indexed-v3',['indexed-attack.py'])]:
        for name in names:assert sha(HERE/name)==sha(BASE/folder/'sources'/name)
    verify=read('difference-boundary-verify-v1','verification.json')
    assert verify['finite_model_checks']==112130 and verify['interpreter_exports_checked']==360 and verify['interpreter_traps']==120
    assert len(verify['negative_witnesses'])==4 and len(verify['refusals'])==3
    lines=[]
    for path in (BASE/'difference-boundary-verify-v1').glob('interp.*.log'):
        lines.extend(l for l in path.read_text().splitlines() if re.match(r'check\d+\(\)',l))
    assert len(lines)==360 and sum('error:' in l for l in lines)==120
    assert all('=> i32:' in l or '=> error: unreachable executed' in l for l in lines)
    indexed=read('difference-boundary-indexed-v3','results.json');assert len(indexed['results'])==60
    for q in indexed['results']:
        path=BASE/'difference-boundary-indexed-v3'/q['output'];assert sha(path)==q['recovered_sha256'];assert q['matches_previously_tested']
        source=p.ROOT/q['input'];expected=source.with_name(source.stem+'.recovered.wasm');assert path.read_bytes()==expected.read_bytes()
        assert statistics.median(q['lookup_decode_samples_ms'])==q['median_ms']
    bench=read('difference-boundary-batch-v1','benchmark.json');summary=read('difference-boundary-batch-v1','summary.json');hc=read('difference-boundary-batch-v1','correctness.json')
    assert len(bench)==45 and len(summary)==75 and len(hc['checks'])==75 and hc['mismatches']==0
    for q in summary:
        records=[b for b in bench if b['path']==q['path']];assert len(records)==3
        values=[next(x for x in b['rows'] if x['scenario']==q['scenario']) for b in records]
        assert statistics.median(x['median_ns'] for x in values)==q['median_ns']
        assert all(x['warmup']==2000 and len(x['samples_ns'])==11 for x in values)
        assert sha(BASE/'difference-boundary-batch-v1'/q['path'])==q['harness_sha256']
    o3=[]
    for n in [64,1024,8192]:
        source=BASE/'difference-boundary-v2'/f'n{n}.plain.O3.wasm'
        for mode in ['xor','roundtrip','two','shared']:
            target=out/f'n{n}.{mode}.from-O3.wasm';stats=p.transform(source,target,mode)
            assert target.read_bytes()==(BASE/'difference-boundary-v2'/f'n{n}.{mode}.raw.wasm').read_bytes()
            o3.append(dict(n=n,mode=mode,sha256=sha(target),source_opt=stats['source_opt']))
    persistence=[]
    for n in [64,1024,8192]:
        path=BASE/'difference-boundary-v2'/f'n{n}.shared.O3.wasm';text=p.w.tool('wasm2wat',[path])
        assert text.count('memory.copy')==1 and text.count('i32.store8')==2
        persistence.append(dict(n=n,memory_copy=1,boundary_stores=2))
    for path in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):assert (path.parent/link.split('#')[0]).exists(),(path.name,link)
    # Hashes taken now are audit-time evidence, distinct from the 9 snapshots above.
    for path in HERE.iterdir():
        if path.is_file():hashes[str(path.relative_to(p.ROOT))]=sha(path)
    for folder in ['difference-boundary-v2','difference-boundary-edge-v1','difference-boundary-verify-v1','difference-boundary-batch-v1','difference-boundary-indexed-v3']:
        for path in (BASE/folder).glob('*.json'):hashes[str(path.relative_to(p.ROOT))]=sha(path)
    result=dict(status='passed',audited_at_utc=datetime.now(timezone.utc).isoformat(),targets=120,native_calls=calls,trapping_copies=traps,recovered=60,transformed_recovered=48,byte_replay=60,contemporaneous_source_files=9,finite_model_checks=112130,interpreter_checks=360,interpreter_traps=120,negative_witnesses=4,refusals=3,harnesses=15,fresh_processes=45,O3_source_checks=o3,O3_persistence=persistence,goal_complete=False,cpu=command(['node','-e','console.log(JSON.stringify({model:require("os").cpus()[0].model,logical:require("os").cpus().length}))']),audit_time_sha256=hashes)
    save(out/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('audit_time_sha256','O3_source_checks')}))

if __name__=='__main__':main()
