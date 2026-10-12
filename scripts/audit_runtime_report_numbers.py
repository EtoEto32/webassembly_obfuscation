"""Recompute rates and summary values from saved counts and measured durations."""
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
cases=[('proof-of-theft/hash-throughput-preliminary-20261007-retry.json','proof-of-theft/preliminary-summary.csv',15),
       ('proof-of-theft/xmr-repeated-throughput-20261008.json','proof-of-theft/xmr-repeated-summary.json',15),
       ('swamped/controlled-pair-repeated-throughput.json','swamped/controlled-pair-summary.json',9)]
checks=[]
for raw_name,summary_name,expected in cases:
    raw_path=BASE/raw_name
    d=json.loads(raw_path.read_text())
    assert d.get('finished_utc')
    samples=d.get('samples',d.get('benchmark',{}).get('samples'))
    assert len(samples)==expected
    if summary_name.endswith('.csv'):
        with (BASE/summary_name).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    else:rows=json.loads((BASE/summary_name).read_text())
    for r in rows:
        selected=[x for x in samples if x['sha256']==r['sha256']]
        assert sorted(x['repetition'] for x in selected)==[1,2,3]
        assert all(x['final_output_matches'] for x in selected)
        rates=[]
        for x in selected:
            assert x['count']>0 and x['elapsed_ms']>0
            rate=x['count']*1000/x['elapsed_ms']
            assert math.isclose(rate,x['hashes_per_second'],rel_tol=1e-12)
            assert all(v['matches'] for v in x.get('post_block_checks',[]))
            rates.append(rate)
        for key,value in [('median_hps',statistics.median(rates)),('min_hps',min(rates)),('max_hps',max(rates))]:
            assert math.isclose(float(r[key]),value,rel_tol=1e-12),(r['sha256'],key)
    checks.append(dict(raw_report=raw_name,raw_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                       summary=summary_name,blocks=len(samples),unique_modules=len(rows),
                       min_elapsed_ms=min(s['elapsed_ms'] for s in samples),
                       count_duration_rates_and_summary_match=True))
report=dict(checks=checks,total_blocks=sum(c['blocks'] for c in checks),
            limitation='Saved-report arithmetic validation only; not independent execution, timing calibration, full-output coverage, or statistical significance.')
(BASE/'runtime-number-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
