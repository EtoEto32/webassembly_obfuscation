import gzip
import hashlib
import importlib.util
import json
import platform
import random
import sys
import time
from pathlib import Path
from recover import recover

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'sha-joint-history-gate'
spec=importlib.util.spec_from_file_location('joint',SOURCE/'check.py')
joint=importlib.util.module_from_spec(spec);spec.loader.exec_module(joint)


def save_gzip(path,obj):
    path.write_bytes(gzip.compress(json.dumps(obj,separators=(',',':')).encode(),mtime=0))


def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    plan=json.loads((HERE/'protocol.json').read_text())
    raw=gzip.decompress((SOURCE/'artifacts/observations.jsonl.gz').read_bytes())
    source_report=json.loads((SOURCE/'artifacts/results.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==source_report['uncompressed_trace_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==9102
    assert all(r['case']=='empty' and r['block']==0 and r['boundary']==24+i for i,r in enumerate(rows[:5]))
    reports=[]
    for seed in plan['seeds']:
        rng=random.Random(seed)
        permutation=list(range(48));rng.shuffle(permutation)
        anonymous=[]
        for count,row in enumerate(rows):
            values=row['history']+[rng.getrandbits(32) for _ in range(22)]+[0,count]
            anonymous.append([values[i] for i in permutation])
        training=anonymous[:5]
        start=time.perf_counter()
        found=recover(training)
        elapsed=time.perf_counter()-start
        # The private permutation is available only to the evaluator.
        expected_order=[permutation.index(i) for i in range(24)]
        assert found['order']==expected_order
        outputs=[]
        for row,values in zip(rows[5:],anonymous[5:]):
            history=[values[i] for i in found['order']]
            assert history==row['history']
            state,words=joint.observer(history,row['boundary'])
            assert state==row['recovered_state'] and words==row['recovered_W']
            outputs.append({'state':state,'words':words})
        controls=[]
        for name,bad in [('all-zero',[[0]*48 for _ in range(5)]),
                         ('duplicated-chain',[r['history']+r['history'] for r in rows[:5]])]:
            try:
                recover(bad)
            except ValueError as error:
                controls.append({'name':name,'rejected':True,'message':str(error)})
            else:
                raise AssertionError(f'control accepted: {name}')
        # Positive identification of one chain must not silently resolve ambiguity.
        save_gzip(out/f'{seed}-anonymous.json.gz',{'training':training,
            'evaluation':[{'boundary':r['boundary'],'values':v} for r,v in zip(rows[5:],anonymous[5:])]})
        save_gzip(out/f'{seed}-recovered.json.gz',outputs)
        report={'seed':seed,'private_permutation':permutation,'found':found,'recovery_seconds':elapsed,
                'evaluation_states':len(outputs),'controls':controls,'mismatches':0}
        reports.append(report)
    paths=[HERE/'check.py',HERE/'recover.py',HERE/'protocol.json',SOURCE/'check.py',SOURCE/'artifacts/results.json']
    result={'python':platform.python_version(),'source_trace_sha256':hashlib.sha256(raw).hexdigest(),
            'variants':reports,'total_evaluation_states':sum(r['evaluation_states'] for r in reports),
            'source_hashes':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'artifact_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'variants':len(reports),'total_evaluation_states':result['total_evaluation_states'],
                      'controls_rejected':sum(len(r['controls']) for r in reports),
                      'recovery_seconds':[r['recovery_seconds'] for r in reports]},indent=2))


if __name__=='__main__': main()
