import json,statistics,sys
from pathlib import Path
import prototype as p
q=p.q;src,runtime,audit,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
read=lambda d,f:json.loads((d/f).read_text())
checks=read(src,'checks.json');attacks=read(src,'attacks.json');times=read(runtime,'summary.json');records=checks['records'];groups=[]
for k in ('fma','horner12','rotation8'):
    for d in ('normal','zero'):
        rs={x['mode']:x for x in times if x['kernel']==k and x['distribution']==d}
        groups.append(dict(kernel=k,distribution=d,deferred_over_eager=rs['deferred']['median_ns']/rs['eager']['median_ns'],residual_over_plain=rs['residual']['median_ns']/rs['plain']['median_ns'],residual_over_deferred=rs['residual']['median_ns']/rs['deferred']['median_ns']))
summary=dict(targets=checks['targets'],inputs=checks['inputs'],calls=checks['calls'],positive_targets=sum(x['mode'] not in ('candidate','uncorrected') for x in records),positive_mismatches=checks['positive_mismatches'],uncorrected_detected=sum(x['mode']=='uncorrected' and x['mismatches']>0 for x in records),candidate_failures=sum(x['mode']=='candidate' and x['mismatches']>0 for x in records),candidate_zero_mismatches=sum(x['mismatches'] for x in records if x['mode']=='candidate'),candidate_nonzero_mismatches=sum(x['nonzeroMismatches'] for x in records if x['mode']=='candidate'),attack_statuses={s:sum(x['status']==s for x in attacks) for s in set(x['status'] for x in attacks)},interpreter_calls=read(audit,'interpreter.json')['calls'],replayed=len(read(audit,'replay.json')),runtime_processes=len(read(runtime,'runtime.json')),ratios=groups)
q.save(out/'summary.json',summary)
lines=['# 零符号の遅延修復：実測','', '5 fresh processの各9batch中央値の中央値。範囲はprocess中央値の最小–最大で信頼区間ではない。共通Wasm loopを含むns/呼出し。phase seed37、通常入力と全零入力を別測定。', '', '| kernel | 入力分布 | 方式 | ns | process範囲 ns | bytes | RSS中央値 KiB |','|---|---|---|---:|---:|---:|---:|']
for x in times:lines.append(f'| {x["kernel"]} | {x["distribution"]} | {x["mode"]} | {x["median_ns"]:.3f} | {x["min_ns"]:.3f}–{x["max_ns"]:.3f} | {x["binary_bytes"]} | {x["rss_kib_median"]} |')
lines += ['', '全方式のlinear memoryは0。RSSはNode/JIT等を含むprocess全体の最高値。binaryは共通wrapper追加前で、residualの元プログラムを含む。', '', '| kernel | 入力分布 | deferred/eager | residual/plain | residual/deferred |','|---|---|---:|---:|---:|']
for x in groups:lines.append(f'| {x["kernel"]} | {x["distribution"]} | {x["deferred_over_eager"]:.3f} | {x["residual_over_plain"]:.3f} | {x["residual_over_deferred"]:.3f} |')
raw=read(runtime,'runtime.json');cap=sum(x['batch']==2**20 for x in raw)
lines+=['',f'{cap}/{len(raw)} processはbatch上限2^20に到達。10msに届かない条件も保存しており、短い通常計算のns値を単独APIの遅延へ外挿しない。', '', '候補抽出の単発analysis_msはWABT readerを除く。元ソースを与えずに抽出するが、変換方式は知っており、zero修復の真正性は機械証明していない。候補の4件の零符号不一致と、元zero経路を残したresidual版の全条件一致を区別する。']
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(summary))
