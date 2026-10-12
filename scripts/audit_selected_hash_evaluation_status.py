"""Join selected published artifacts to saved correctness/timing evidence."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/runtime-mining/cross-dataset'
sources=[]
def read(name):
    data=(OUT/name).read_bytes()
    sources.append(dict(file=name,sha256=hashlib.sha256(data).hexdigest()))
    return json.loads(data)

manifest=read('proof-of-theft/glue-control-input.json')
vectors=read('proof-of-theft/original-glue-public-vector-check-corrected-20261008.json')
wmp=read('proof-of-theft/hash-throughput-preliminary-20261007-retry.json')
xmr=read('proof-of-theft/xmr-repeated-throughput-20261008.json')
links=read('rq1-rq2-runtime-evidence.json')
by_sha={r['sha256']:r for r in vectors['results']}
linked={r['sha256']:r for r in links['modules']}
assert len(by_sha)==len(manifest['modules'])==19
assert set(by_sha)=={r['sha256'] for r in manifest['modules']}
records=[]
for module in manifest['modules']:
    sha=module['sha256']
    assert hashlib.sha256((ROOT/module['object']).read_bytes()).hexdigest()==sha
    check=by_sha[sha];outputs=check['outputs']
    error=check.get('error','')
    mismatched=sum(not r['matches'] for r in outputs)
    if outputs:
        status='applicable public vectors matched' if not mismatched else 'observed output mismatch'
        assert len(outputs)==(3 if module['family']=='xmr-wasm' else 5)
    elif 'no cryptonight_hash export' in error:
        status='per-input interface unavailable; correctness unverified'
    elif 'null function or function signature mismatch' in error:
        status='runtime interface error before output; correctness unverified'
    else:raise AssertionError((module['method'],error))
    samples=[];algorithm=None;expected_kind=None;seconds=None;warmup=None
    if module['family']=='webminerpoolhashcn':
        samples=[s for s in wmp['benchmark']['samples'] if s['sha256']==sha]
        if samples:
            algorithm='cn/pico';expected_kind='13 stored pool-accepted output/input records (not new submissions)'
            seconds=wmp['benchmark']['seconds_per_block'];warmup=wmp['benchmark']['warmup_seconds']
            correctness=next(r for r in wmp['results'] if r['sha256']==sha)
            assert len(correctness['outputs'])==13 and all(r['matches'] for r in correctness['outputs'])
    elif module['family']=='xmr-wasm':
        samples=[s for s in xmr['samples'] if s['sha256']==sha]
        if samples:
            algorithm='cn/0';expected_kind='three applicable XMRig public vectors'
            seconds=xmr['seconds_per_block'];warmup=xmr['warmup_seconds']
    if samples:
        assert len(samples)==3 and sorted(s['repetition'] for s in samples)==[1,2,3]
        for sample in samples:
            assert sample['final_output_matches']
            assert sample['elapsed_ms']>=seconds*1000
            assert abs(sample['count']*1000/sample['elapsed_ms']-sample['hashes_per_second'])<1e-9
        assert sha in linked and not linked[sha]['wasabi_hooks']
    records.append(dict(family=module['family'],method=module['method'],sha256=sha,
        source_path=module['path'],correctness_status=status,public_vector_algorithm='cn/0',
        applicable_public_vectors_with_outputs=len(outputs),observed_public_output_mismatches=mismatched,
        benchmark_algorithm=algorithm,benchmark_expected_output_basis=expected_kind,
        completed_timing_blocks=len(samples),seconds_per_block=seconds,warmup_seconds=warmup,
        timing_status='three validated blocks present' if samples else 'no completed valid timing blocks; not zero throughput',
        confirmed_mechanism=linked.get(sha,{}).get('confirmed_mechanism','not established by this status audit'),
        diagnostic_first_line=error.splitlines()[0] if error else '',
        evidence_scope='This status audit joins existing logs, not new executions or full-input correctness proof.'))

assert sum(r['completed_timing_blocks'] for r in records)==30
assert sum(bool(r['applicable_public_vectors_with_outputs']) for r in records)==10
assert sum(r['observed_public_output_mismatches'] for r in records)==0
with (OUT/'selected-hash-evaluation-status.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
report=dict(sources=sources,modules=records,
    coverage=dict(selected_published_modules=len(records),status_counts=dict(Counter(r['correctness_status'] for r in records)),
                  validated_timing_blocks=30),
    limitations=['This report covers the 19 modules selected for original-glue checks, not the complete public corpus.',
        'The SWAMPED controlled trio and historical Cryptic Bytes external-pool runs are outside this report; consult their separate logs.',
        'No recorded output mismatch among returned public-vector outputs does not mean untested/erroring modules are correct.',
        'webminerpoolhashcn public vectors use cn/0, while its measured 5-second blocks use cn/pico; they must not be merged into one algorithm evaluation.',
        'Three validated timing blocks do not prove the named obfuscation mechanism, causal overhead, all-input semantic preservation, or reproducible historical toolchains.'],
    executed_hashes=0)
(OUT/'selected-hash-evaluation-status.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['coverage']))
