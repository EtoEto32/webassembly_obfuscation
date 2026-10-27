"""Audit the evidence files without repeating performance measurements."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import prototype as p

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'results/invention-20261019'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(folder,name):return json.loads((BASE/folder/name).read_text(encoding='utf-8'))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();checks={}
    main='nilpotent-stencil-v1';probe='nilpotent-stencil-probe-v2';batch='nilpotent-stencil-batch-v1';verify='nilpotent-stencil-verify-v1';proof='nilpotent-stencil-proof-v1';edge='nilpotent-stencil-edge-v1'
    summary=read(main,'summary.json');manifest=read(main,'manifest.json');assert len(summary)==len(manifest['files'])==70
    assert len({r['path'] for r in summary})==70
    for row in summary:
        path=BASE/main/row['path'];assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256'];assert path.read_bytes()==(BASE/probe/row['path']).read_bytes()
    replay=read(main,'replay.json');assert len(replay)==70 and all(replay.values());checks['byte_replay_and_hashes']=70
    hashes=read(main,'environment.json')['source_sha256']
    for relative,expected in hashes.items():
        src=ROOT/relative;copy=BASE/main/'sources'/(src.parent.name+'_'+src.name);assert sha(src)==sha(copy)==expected,relative
    checks['contemporaneous_main_sources']=len(hashes)
    total=0;binaries=0
    for folder,count,calls in [(main,70,300160),(verify+'/random',60,257280),(edge,6,25728)]:
        c=read(folder,'correctness.json');assert (c['binaries'],c['calls'],c['mismatches'],c['traps'])==(count,calls,0,0);assert len(c['records'])==count and sum(r['calls'] for r in c['records'])==calls;total+=calls;binaries+=count
    checks['native_binaries_including_positive_controls']=binaries;checks['native_calls_including_positive_controls']=total
    interp=read(verify,'interpreter.json');assert interp['calls']==420 and interp['mismatches']==0 and len(interp['records'])==70;checks['interpreter_calls']=420
    attacks=read(main,'attacks.json');assert len(attacks)==30 and all(r['status']=='recovered' for r in attacks)
    for row in attacks:assert len(row['samples_ms'])==9 and row['median_ms']==statistics.median(row['samples_ms'])
    checks['scalar_recoveries']=30
    smt=read(proof,'proof.json');assert (smt['unsat'],smt['sat'],smt['unknown'])==(30,0,0);assert len(list((BASE/proof).glob('*.smt2')))==30;checks['scalar_SMT_unsat']=30
    controls=read(verify,'controls.json');assert len(controls)==6 and all(r['status']=='refused' for r in controls);checks['refused_controls']=6
    witnesses=read(verify,'counterexamples.json');assert len(witnesses)==3 and all(r['actual']!=r['expected'] for r in witnesses);checks['actual_Wasm_wrong_transform_witnesses']=3
    collisions=read(verify,'lane-collisions.json');assert len(collisions)==4 and {r['k'] for r in collisions}=={1,2,3,4}
    for r in collisions:assert r['a']!=r['b'] and r['values'][0]==r['values'][1]
    checks['noninjective_lane_witnesses']=4
    algebra=read(verify,'algebra.json');assert sum(r['checks'] for r in algebra)==16000 and all(r['mismatches']==0 for r in algebra);checks['finite_difference_checks']=16000
    bmanifest=read(batch,'manifest.json');bs=read(batch,'summary.json');brows=read(batch,'benchmark.json');assert len(bmanifest['files'])==len(bs)==35 and len(brows)==105
    for name,expected in bmanifest['source_sha256'].items():assert sha(HERE/name)==sha(BASE/batch/'sources'/name)==expected
    for row in bs:
        path=BASE/batch/row['path'];assert path.stat().st_size==row['harness_bytes'] and sha(path)==row['harness_sha256'];group=[b for b in brows if b['path']==row['path']];assert len(group)==3 and {b['repeat'] for b in group}=={0,1,2}
        assert row['median_ns']==statistics.median(b['median_ns'] for b in group)
        for b in group:
            assert (b['warmup_calls'],b['calls_per_sample'],b['repetitions'])==(1000000,200000,11);assert len(b['samples_ns'])==11 and b['median_ns']==statistics.median(b['samples_ns'])
    bc=read(batch,'correctness.json');assert (bc['harnesses'],bc['tests'],bc['referenceCalls'],bc['mismatches'])==(35,700,7140,0);checks['batch_fresh_processes']=105;checks['batch_harness_tests']=700
    counts={}
    for name in manifest['models']:
        path=BASE/main/(name+'.dynamic.O3.wasm');wat=p.w.tool('wasm2wat',[path]);counts[name]=dict(extract=wat.count('i32x4.extract_lane'),multiply=wat.count('i32x4.mul'));assert counts[name]['extract']==4 and counts[name]['multiply']>0
    checks['O3_retained_vector_operations']=counts
    links=0
    for path in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(path.parent/link.split('#',1)[0]).resolve();assert target.exists() or target==a.output.resolve(),(path,target);links+=1
    checks['local_document_links']=links
    folders=['nilpotent-stencil-probe-v1',probe,main,batch,verify,proof,edge]
    artifacts={str(path.relative_to(ROOT)):sha(path) for folder in folders for path in (BASE/folder).rglob('*') if path.is_file()}
    sources={str(path.relative_to(ROOT)):sha(path) for path in HERE.iterdir() if path.is_file()}
    result=dict(status='passed',checks=checks,goal_complete=False,artifact_sha256=artifacts,audit_time_source_sha256=sources,
                conclusion='Restricted four-point execution is correct in the tested scope. A coefficient projection recovers all 30 scalar computations. Independent novelty and useful protection gain are unestablished.',
                source_note='Main and batch sources were saved at execution; verification/proof/report sources written later are hashed at audit time. No benchmark is rerun by this audit.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(status='passed',checks=checks,artifact_files=len(artifacts),goal_complete=False)))


if __name__=='__main__':main()
