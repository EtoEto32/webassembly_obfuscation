import argparse
import csv
import json
from pathlib import Path
import statistics


def report(directory):
    manifest=json.loads((directory/'manifest.json').read_text())
    perf=json.loads((directory/'performance.json').read_text())
    rows=[]
    for e in manifest['entries']:
        runs=[x for x in perf if x['file']==e['file']]
        times=[x['median_ns']/1000 for x in runs]
        rows.append({'file':e['file'],'length':e['length'],'method':e['method'],'opt':e['opt'],
                     'median_us':statistics.median(times),'min_process_median_us':min(times),
                     'max_process_median_us':max(times),'binary_bytes':e['bytes'],
                     'public_memory_bytes':65536,'private_memory_bytes':e['private_pages']*65536,
                     'median_peak_RSS_KiB':statistics.median(x['peak_rss_KiB'] for x in runs),
                     'raw_transform_ms':e['transformation_ns']/1e6,'processes':len(runs)})
    with (directory/'comparison.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['# 群上rolling照合の測定','',
           '既知point方式の比較であり、新規・優位な難読化方式の認定ではない。',
           '各条件3 fresh process、各process 7 batchの中央値をさらに中央値化。入力はL+16 byteの全零、非一致。',
           'plainは10,000 warmup・200,000 calls/batch、群方式は8 warmup・rolling 8 / recompute 2 calls/batch。',
           '単一host上の診断値。広い実用workloadや秘密の高entropyを代表しない。RSSはNode全体、変換時間は各raw生成1回。','',
           '|L|方式|opt|μs/call (process範囲)|bytes|private KiB|RSS KiB|',
           '|---:|---|---|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f'|{r["length"]}|{r["method"]}|{r["opt"]}|{r["median_us"]:.3f} ({r["min_process_median_us"]:.3f}–{r["max_process_median_us"]:.3f})|{r["binary_bytes"]}|{r["private_memory_bytes"]/1024:g}|{r["median_peak_RSS_KiB"]:g}|')
    (directory/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    for r in rows:
        if r['opt']=='O3':print(json.dumps(r))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);report(p.parse_args().directory)
