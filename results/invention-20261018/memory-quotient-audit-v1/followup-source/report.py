"""Render existing measurements without rerunning or changing them."""
import argparse
import csv
import json
from pathlib import Path


def main(folder):
    if (folder/'comparison.csv').exists() or (folder/'comparison.md').exists():raise ValueError('Refuse overwrite')
    manifest=json.loads((folder/'manifest.json').read_text())
    perf={r['wasm']:r for r in json.loads((folder/'performance.json').read_text())['rows']}
    rows=[]
    for r in manifest['rows']:
        p=perf[r['wasm']]
        rows.append({**{k:r[k] for k in ['fixture','mode','optimization','bytes']},
            **{k:p[k] for k in ['median_ns','process_median_min_ns','process_median_max_ns','median_peak_RSS_KiB']}})
    with (folder/'comparison.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines=['# O3の入力条件の測定','',
        '各値は3 fresh Node processの中央値。1 processにつきwarmup 10,000、20,000呼出し×9回。ホストのループ・呼出し・checksumを含む。recoveredは入力側の最適化条件で分類し、回復出力自体へO3を再適用していない。ばらつきが大きく、速度の優劣を判定しない。','',
        '|例|方式|bytes|中央値 ns/呼出し|process中央値の範囲 ns|peak RSS KiB中央値|',
        '|---|---|---:|---:|---:|---:|']
    for r in rows:
        if r['optimization']=='O3':lines.append(f"|{r['fixture']}|{r['mode']}|{r['bytes']}|{r['median_ns']:.3f}|{r['process_median_min_ns']:.3f}–{r['process_median_max_ns']:.3f}|{r['median_peak_RSS_KiB']}|")
    (folder/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);main(ap.parse_args().folder)
