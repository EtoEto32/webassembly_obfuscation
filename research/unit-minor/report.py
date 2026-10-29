# -*- coding: utf-8 -*-
import argparse
import csv
import json
from pathlib import Path
import prototype as p


def run(main,audit,runtime,output):
    main,audit,runtime,out=map(lambda s:Path(s).resolve(),(main,audit,runtime,output)); out.mkdir(parents=True,exist_ok=False)
    checks=json.loads((main/'checks.json').read_text()); recovery=json.loads((main/'analysis.json').read_text())
    summary=json.loads((runtime/'summary.json').read_text()); analysis=json.loads((runtime/'analysis.json').read_text())
    model=json.loads((audit/'model.json').read_text()); rr=json.loads((runtime/'runtime.json').read_text())
    transforms=json.loads((main/'transforms.json').read_text())
    rows=[]
    for row in summary['rows']:
        name=row['name']; modes=row['modes']
        a={x['mode']:x for x in analysis if x['name']==name and x['opt']=='O3'}
        b={x['mode']:x for x in summary['binaries'] if x['name']==name}
        for mode,values in modes.items():
            item=dict(name=name,mode=mode,runtime_ns=values['median'],process_min_ns=values['range'][0],process_max_ns=values['range'][1],bytes=b[mode]['bytes'],linear_memory_bytes=b[mode]['linear_memory_bytes'])
            if mode in a: item.update(read_median_ms=a[mode]['read_median_ms'],symbolic_median_ms=a[mode]['symbolic_median_ms'])
            rows.append(item)
    metrics=[]
    for row in summary['rows']:
        name=row['name']; v=row['modes']; a={x['mode']:x for x in analysis if x['name']==name and x['opt']=='O3'}
        metrics.append(dict(name=name,polynomial_over_plain=v['polynomial']['median']/v['plain']['median'],polynomial_over_constant=v['polynomial']['median']/v['constant']['median'],symbolic_over_constant=a['polynomial']['symbolic_median_ms']/a['constant']['symbolic_median_ms'],read_plus_symbolic_over_constant=(a['polynomial']['read_median_ms']+a['polynomial']['symbolic_median_ms'])/(a['constant']['read_median_ms']+a['constant']['symbolic_median_ms'])))
    facts=dict(positive_conditions=checks['positiveConditions'],positive_calls=checks['positiveCalls'],inputs=checks['inputs'],positive_mismatches=sum(x['mismatch'] for x in checks['results'] if not x['negative']),positive_traps=sum(x['traps'] for x in checks['results'] if not x['negative']),negative_conditions=checks['negativeConditions'],recoveries=sum(x['status']=='recovered' for x in recovery),recovery_conditions=len(recovery),model_cases=model['cases'],regenerated=len(json.loads((audit/'replay.json').read_text())),interpreter_calls=sum(x['calls'] for x in json.loads((audit/'interpreter.json').read_text())),controls=len(json.loads((audit/'controls.json').read_text())),processes=summary['processes'],batches=summary['batches'],short_batches=summary['short_batches'],maxRSS_KiB_range=[min(x['measurement']['maxRssKiB'] for x in rr),max(x['measurement']['maxRssKiB'] for x in rr)],transform_ms_range=[min(x['transform_ms'] for x in transforms),max(x['transform_ms'] for x in transforms)])
    p.save(out/'report.json',dict(facts=facts,rows=rows,ratios=metrics))
    with (out/'comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
    lines=['# 行列式変換の実測比較','', '2026-10-22。main-v2、audit-v1、runtime-v2が主結果。','',
           '| 式 | 方式 | 実行 ns/回（process中央値の範囲） | O3 bytes | 読取・証明 ms | 記号計算 ms |','|---|---|---:|---:|---:|---:|']
    for x in rows:
        read=f'{x["read_median_ms"]:.3f}' if 'read_median_ms' in x else '—'
        sy=f'{x["symbolic_median_ms"]:.3f}' if 'symbolic_median_ms' in x else '—'
        lines.append(f'| {x["name"]} | {x["mode"]} | {x["runtime_ns"]:.3f} ({x["process_min_ns"]:.3f}–{x["process_max_ns"]:.3f}) | {x["bytes"]} | {read} | {sy} |')
    lines+=['','| 式 | 実行 poly/plain | 実行 poly/constant | 記号計算 poly/constant | 読取＋記号計算の中央値和の比 |','|---|---:|---:|---:|---:|']
    for x in metrics: lines.append(f'| {x["name"]} | {x["polynomial_over_plain"]:.3f} | {x["polynomial_over_constant"]:.3f} | {x["symbolic_over_constant"]:.3f} | {x["read_plus_symbolic_over_constant"]:.3f} |')
    lines+=['', '```json',json.dumps(facts,indent=2,ensure_ascii=False),'```','',
            '記号計算は同一Python process内11反復の中央値。読取はvalidation、WAT変換、kernel照合、8通りのparity rank検査を含む。コンパイル時間を含まない。解析器を開発した人間の時間は測っていない。',
            '実行は各方式3 fresh process×9 batch。共通Wasm入力更新・checksum loop、warmup16,384回、batch目標10ms、最大2^24回。CPU affinity/frequencyは未制御。約1nsの通常式はこのloopとJIT最適化を含む値で、JavaScript API呼出しの時間ではない。',
            '各行列式版は非公開linear memory 128KiB、元式・回復式は0。RSSはNode/JIT全体を含み、Wasmのみの消費量ではない。変換時間は各1回の生成・tool呼出し込みで分布推定ではない。',
            '全18条件を回復。polyの解析本体には増加があるが、3小式での限定値である。同等の実行費用に調整した他方式、一般的な逆コンパイラ、人間の読解実験は未実施。大規模行列・多数入力へ外挿しない。',
            'v1の速度測定はplain/recoveredが全てbatch目標未達だったため、capとwarmupを増やしたv2へ更新。v1の正当性件数や速度sampleは加算しない。']
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    inputs=[main/'checks.json',main/'analysis.json',main/'transforms.json',audit/'model.json',audit/'replay.json',audit/'interpreter.json',audit/'controls.json',runtime/'summary.json',runtime/'analysis.json',runtime/'runtime.json']
    p.save(out/'input-pins.json',{str(x):p.digest(x) for x in inputs})
    p.save(out/'pins.json',{str(f.relative_to(out)):p.digest(f) for f in out.iterdir() if f.is_file()})
    print(json.dumps(dict(facts=facts,ratios=metrics)))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('main'); ap.add_argument('audit'); ap.add_argument('runtime'); ap.add_argument('output'); a=ap.parse_args(); run(a.main,a.audit,a.runtime,a.output)
