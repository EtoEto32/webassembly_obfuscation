import hashlib
import json
from pathlib import Path
import shutil
import statistics
import sys

p=Path(sys.argv[1]);r=json.loads((p/'checks.json').read_text());m=json.loads((p/'manifest.json').read_text())
rows=[]
for row in r['rows']:
    samples=[x for x in r['performance'] if all(x[k]==row[k] for k in ['family','mode','optimization'])]
    medians=[statistics.median(x['ns_per_call']) for x in samples]
    rows.append({**row,'median_ns':statistics.median(medians),'process_medians_ns':medians,
        'min_process_median_ns':min(medians),'max_process_median_ns':max(medians),
        'median_process_peak_rss_kib':statistics.median(x['maxrss_kib'] for x in samples)})
dest=p/'summary.json'
if dest.exists():raise ValueError('Refuse overwrite')
dest.write_text(json.dumps({'rows':rows},indent=2),encoding='utf-8')
lines=['# Alias circuit measurements','',
 '4000 warmups, 11 batches of 2000 calls, 3 fresh Node processes per condition. Median of per-process medians; host calls included.',
 '','|family|input optimization|mode|bytes|median ns|process median range ns|median peak RSS MiB|',
 '|---|---|---|---:|---:|---:|---:|']
for x in rows:
    lines.append(f"|{x['family']}|{x['optimization']}|{x['mode']}|{x['bytes']}|{x['median_ns']:.2f}|{x['min_process_median_ns']:.2f}–{x['max_process_median_ns']:.2f}|{x['median_process_peak_rss_kib']/1024:.2f}|")
lines.extend(['','Recovered means scalar circuit emitted from that input optimization level; the emitted circuit was not optimized again.',
 'RSS includes Node, JIT, GC, and harness. Zero linear memory does not mean zero heap usage.',
 'The historical checks.json field heap_after_gc was sampled after timed calls; it is not a retained-heap-after-GC result. It is not used in this summary.',
 'All values are descriptive microbenchmark results. No confidence interval or cost-matched superiority claim.'])
(p/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
snap=p/'followup-source';snap.mkdir(exist_ok=False)
for s in Path(__file__).parent.glob('*'):
    if s.is_file():shutil.copy2(s,snap/s.name)
(snap/'hashes.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in snap.iterdir() if x.is_file()},indent=2),encoding='utf-8')
print(json.dumps({'rows':len(rows),'summary':str(dest)}))
