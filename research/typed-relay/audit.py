"""Check stored evidence, exact raw-body reconstruction and timing summaries."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import prototype as p


def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args()
    d=a.directory
    def read(name):return json.loads((d/name).read_text(encoding='utf-8'))
    manifest=read('manifest.json');files=read('files.json');analysis=read('analysis.json');perf=read('performance.json')
    hashes={x['path']:hashlib.sha256((d/x['path']).read_bytes()).hexdigest() for x in files}
    assert hashes==manifest['binaries']
    raw_equal=[]
    for f in files:
        if f['recovered'] or f['opt']!='raw':continue
        orig,_=p.load(d/(f['model']+'.plain.raw.wasm'));m,_=p.load(d/f['path'])
        r=p.recover(m);of=p.check_module(orig)[0][0];rf=p.check_module(r['module'])[0][0]
        assert rf==of
        raw_equal.append(f['path'])
    check=read('correctness.json');assert check['mismatches']==0 and check['binaries']==len(files)
    assert all(x['status']=='success' for x in analysis)
    optimized=[x for x in analysis if '.O' in x['path']]
    assert all(x['functions']==1 and sum(x['instruction_counts'].values())==0 for x in optimized)
    assert all(x['status']=='rejected' for x in read('negative.json'))
    secondary=read('binaryen-interpreter.json');assert all(x['status']=='success' for x in secondary)
    stats=[]
    for f in files:
        if f['recovered']:continue
        sessions=[x for x in perf if x['path']==f['path']]
        medians=[statistics.median(x['samples_ns']) for x in sessions];pooled=[y for x in sessions for y in x['samples_ns']]
        assert len(sessions)==3
        ar=next(x for x in analysis if x['path']==f['path']);q=statistics.quantiles(pooled,n=4,method='inclusive')
        stats.append(dict(path=f['path'],bytes=(d/f['path']).stat().st_size,runtime_median_ns=statistics.median(medians),
                          session_medians_ns=medians,pooled_q1_ns=q[0],pooled_q3_ns=q[2],
                          analysis_median_ms=statistics.median(ar['samples_ms']),analysis_min_ms=min(ar['samples_ms']),
                          analysis_max_ms=max(ar['samples_ms']),peak_rss_kib=[x['max_rss_kib'] for x in sessions]))
    compare=None
    if a.compare:
        other=json.loads((a.compare/'manifest.json').read_text(encoding='utf-8'))
        assert hashes==other['binaries'];compare=dict(path=str(a.compare),binaries_identical=True)
    report=dict(passed=True,binaries=len(files),raw_bodies_exact=raw_equal,optimized_no_calls=len(optimized),
                node_calls=check['calls'],node_traps=check['traps'],binaryen_calls=sum(x['calls'] for x in secondary),
                wabt_statuses=dict(Counter(x['status'] for x in read('wabt.json'))),performance=stats,compare=compare)
    with (d/'verification.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('performance','raw_bodies_exact')}))


if __name__=='__main__':main()
