"""Heuristic quotient from continuation fingerprints, without full state scan.

Candidates need validation. Source models are used ONLY after recovery by the
experiment manager, and never by fingerprint().
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import time
import tracemalloc
import prototype as p

def fingerprint(rows,start,seed=20261019):
    rng=random.Random(seed);suffixes=[]
    for n in range(5):
        for value in range(1<<n):suffixes.append(tuple((value>>i)&1 for i in range(n)))
    for _ in range(64):suffixes.append(tuple(rng.randrange(2) for _ in range(rng.randrange(1,33))))
    signatures={};probes=0
    def sig(q):
        nonlocal probes
        if q in signatures:return signatures[q]
        answer=[]
        for word in suffixes:
            at=q
            for c in word:at=rows[at][c];probes+=1
            answer.append(rows[at][2]);probes+=1
        signatures[q]=tuple(answer);return signatures[q]
    ids={sig(start):0};reps=[start];out=[]
    for q in reps:
        dest=[]
        for c in range(2):
            at=rows[q][c];key=sig(at)
            if key not in ids:
                if len(ids)>=128:raise ValueError('Representative budget')
                ids[key]=len(ids);reps.append(at)
            dest.append(ids[key])
        out.append(dest+[rows[q][2]])
    return out,dict(representatives=len(reps),physical_states_probed=len(signatures),table_probes=probes,suffixes=len(suffixes),exact=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((a.input/'manifest.json').read_text());records=[]
    for entry in manifest['files']:
        if entry['mode']=='plain' or 'kind' in entry:continue
        full,start,ex=p.extract(a.input/entry['path'],a.output);samples=[]
        for _ in range(11):
            begin=time.perf_counter();small,stats=fingerprint(full,start);samples.append((time.perf_counter()-begin)*1000)
        tracemalloc.start();fingerprint(full,start);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        d=manifest['models'][entry['model']];source=[row+[(d['final']>>q)&1] for q,row in enumerate(d['trans'])];eq=p.equivalent(source,small)
        # The emitted full-partition clone already has this exact model.
        certified,_=p.quotient(full,start)
        same=small==certified
        if not eq['equivalent'] or not same:raise AssertionError((entry,eq,same))
        records.append(dict(path=entry['path'],**ex,**stats,median_ms=statistics.median(samples),samples_ms=samples,heap_peak_bytes=peak,posthoc_equivalence=eq,same_as_existing_static_clone=same))
    rare,start,_=p.extract(a.input/'rare-exception.wasm',a.output);small,stats=fingerprint(rare,start);negative=dict(**stats,rows=small,posthoc_equivalence=p.equivalent(rare,small,start,0))
    if negative['posthoc_equivalence']['equivalent']:raise AssertionError('Negative control unexpectedly succeeds')
    report=dict(records=records,conditions=len(records),equivalent=len(records),rare_control=negative,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(a.output/'adaptive.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in report.items() if k!='records'}))

if __name__=='__main__':main()
