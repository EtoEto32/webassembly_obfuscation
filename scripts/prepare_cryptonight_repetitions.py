"""Prepare a sequential plan or verify existing logs; never launch a runner."""
import argparse
import hashlib
import json
import math
import statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--logs',type=Path)
    args=parser.parse_args()
    manifest=BASE/'cryptonight-export-only-manifest.json'
    modules=json.loads(manifest.read_text())['modules']
    assert len(modules)==5 and modules[0]['method']=='cryptonight-hash'
    runner=ROOT/'experiments/runtime-reference/proof-cryptonight-export-check.cjs'
    vectors=BASE/'glue-control-input.json'
    expected=json.loads(vectors.read_text())['vectors']
    steps=[]
    for repetition in range(3):
        rotated=modules[repetition:]+modules[:repetition]
        for order,item in enumerate(rotated):
            steps.append({'repetition':repetition+1,'order':order+1,'method':item['method'],
                'original_sha256':item['original_sha256'],'derivative_sha256':item['derivative_sha256'],
                'glue_sha256':item['original_glue_sha256'],
                'output_name':f"round-{repetition+1}-{item['original_sha256'][:12]}.json"})
    plan={'status':'prepared, not executed','steps':steps,'manifest_sha256':sha(manifest),
        'runner_sha256':sha(runner),'vector_manifest_sha256':sha(vectors),
        'helpers_sha256':sha(ROOT/'experiments/runtime-reference/proof-glue-controls.cjs'),
        'requirements':['Confirmed university permission; bounded non-root network-disabled container.',
            'One fresh process at a time, external timeout, fixed image/CPU/memory settings.',
            'Run five-vector check alone before attempting timing; keep failures as failures.',
            'Three cyclically rotated rounds; 3 s warmup and >=30 s timing per block.'],
        'scope':'Prepared five export-only derivatives; no claim of unchanged published-artifact timing.'}
    (BASE/'cryptonight-repetition-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    if args.logs is None:
        print('Prepared 15 sequential steps; no process launched.');return
    accepted=[];rejected=[];previous_end=None;environment=None
    for step in steps:
        p=args.logs/step['output_name']
        try:
            r=json.loads(p.read_text())
            assert r['status']=='public vectors and one timed block final check matched'
            for key in ('method','original_sha256','derivative_sha256','glue_sha256'):
                assert r[key]==step[key],key
            for key,expected_value in [('manifest_sha256',plan['manifest_sha256']),
                    ('script_sha256',plan['runner_sha256']),('vector_manifest_sha256',plan['vector_manifest_sha256']),
                    ('file_helpers_sha256',plan['helpers_sha256'])]:assert r[key]==expected_value,key
            assert len(r['results'])==len(expected)==5
            for actual,v in zip(r['results'],expected):
                assert actual['vector_id']==v['id'] and actual['expected']==actual['actual']==v['expected']
                assert all(actual[k] is True for k in ('matches','input_unchanged','output_guard_unchanged'))
            b=r['throughput_block'];count=b['count'];elapsed=b['elapsed_ms']
            assert isinstance(count,int) and not isinstance(count,bool) and count>0
            assert math.isfinite(elapsed) and elapsed>=30000
            assert math.isfinite(b['warmup_elapsed_ms']) and b['warmup_elapsed_ms']>=3000
            assert b['target_elapsed_ms']==30000 and b['target_warmup_ms']==3000
            assert math.isclose(b['hashes_per_second'],count*1000/elapsed,rel_tol=1e-12)
            last=expected[(count-1)%len(expected)]
            assert b['last_vector_id']==last['id'] and b['expected']==b['actual']==last['expected']
            assert all(b[k] is True for k in ('matches','input_unchanged','output_guard_unchanged'))
            start=datetime.fromisoformat(r['started_utc'].replace('Z','+00:00'))
            end=datetime.fromisoformat(r['finished_utc'].replace('Z','+00:00'))
            block_start=datetime.fromisoformat(b['started_utc'].replace('Z','+00:00'))
            block_end=datetime.fromisoformat(b['finished_utc'].replace('Z','+00:00'))
            assert all(t.tzinfo is not None and t.utcoffset().total_seconds()==0
                       for t in (start,end,block_start,block_end))
            assert start<=block_start<block_end<=end
            assert previous_end is None or previous_end<=start,'Overlapping/out-of-order processes'
            current=(r['node'],r['v8'],r.get('image_id'))
            assert current[2] and (environment is None or current==environment),'Missing or changed image/runtime'
            previous_end=end;environment=current
            accepted.append({**step,'path':str(p),'sha256':sha(p),'hashes_per_second':count*1000/elapsed})
        except (OSError,ValueError,KeyError,AssertionError,TypeError) as error:
            rejected.append({**step,'reason':str(error) or 'Log validation assertion failed'})
    complete=len(accepted)==15 and not rejected
    summaries=[]
    if complete:
        reference=[x['hashes_per_second'] for x in accepted if x['method']=='cryptonight-hash']
        for item in modules:
            rows=sorted([x for x in accepted if x['method']==item['method']],key=lambda x:x['repetition'])
            rates=[x['hashes_per_second'] for x in rows]
            summaries.append({'method':item['method'],'median_hps':statistics.median(rates),
                'min_hps':min(rates),'max_hps':max(rates),
                'median_ratio':statistics.median(rates)/statistics.median(reference),
                'within_round_ratios':[v/base for v,base in zip(rates,reference)]})
    result={'status':'complete log set verified' if complete else 'incomplete; no comparison summary',
        'accepted':accepted,'rejected':rejected,'summaries':summaries,
        'scope':'Existing logs only; no execution. Sequential ratios are not confidence intervals or causal proof.'}
    out=BASE/'cryptonight-repetition-log-review.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(f'{len(accepted)} accepted logs; {len(rejected)} missing/rejected; summary available: {complete}.')

if __name__=='__main__':main()
