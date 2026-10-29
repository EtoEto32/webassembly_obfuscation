"""Summarize saved measurements without rerunning or changing them."""
import json,sys
from pathlib import Path
main,runtime,audit,controls,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
read=lambda f:json.loads(f.read_text(encoding='utf-8'))
checks=read(main/'checks.json');manifest=read(main/'manifest.json');times=read(runtime/'summary.json')
checks={k:v for k,v in checks.items() if k not in ('localResults','hashes')}
rows=[]
for t in times:
    m=next(x for x in manifest if x['file']==t['file'])
    rows.append(dict(**t,bytes=m['bytes'],linear_memory_bytes=17*65536 if m['state'] else 0,prepare_ms=m['prepare_ms']))
by={x['mode']:x for x in rows}
result=dict(checks=checks,rows=rows,replay=read(audit/'replay.json'),controls=read(controls/'controls.json'),
    original_over_certified=by['original']['median_ns']/by['certified']['median_ns'],
    original_over_recovered_state=by['original']['median_ns']/by['recovered-state']['median_ns'],
    original_over_recovered_io=by['original']['median_ns']/by['recovered-io']['median_ns'])
(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 有限環残差方式の実測比較','',
 'O3、5 fresh processの各9 batch中央値の中央値。範囲は5つのprocess中央値の最小–最大であり信頼区間ではない。時間は共通Wasm loopを含むhelper 1回当たり。', '',
 '| 方式 | 時間 µs | process中央値の範囲 µs | binary bytes | 線形memory bytes | process最大RSS中央値 KiB |',
 '|---|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'| {r["mode"]} | {r["median_ns"]/1000:.6f} | {r["min_ns"]/1000:.6f}–{r["max_ns"]/1000:.6f} | {r["bytes"]} | {r["linear_memory_bytes"]} | {r["rss_kib_median"]} |')
lines+=['',f'原型/129反復: {result["original_over_certified"]:.2f}倍。原型/全scratch再構築版: {result["original_over_recovered_state"]:.2f}倍。原型/I/O回復版: {result["original_over_recovered_io"]:.2f}倍。',
 '', 'plainとI/O回復版は全memoryの保存契約を持たない。scratch保存を含む比較はoriginal・certified・recovered-state間で行う。通常word式は解析器が発見した式ではなく、独立した下限側の対照。',
 '', 'RSSはNode全processの最高値であり方式単体の使用量ではない。binaryはbenchmark wrapper追加前、線形memoryは固定ページ宣言から算出。',
 '', 'main-v2のprepare_msは既に得た式の再コンパイルとO3処理を含む1回の時間であり、元DAGからの発明方式の変換時間や攻撃開発時間ではない。読取・回復本体の測定はreplay.jsonおよびrecovery.jsonに別記する。',
 '', 'plainはcalibration上限2^22に達したため10ms目標に届かず、各batchは約4.2ms。1ns程度の値はJIT内の共通loop・inliningを含み、単独JS呼出しの遅延ではない。']
(out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k.startswith('original_over')}))
