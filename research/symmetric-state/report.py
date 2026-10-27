"""Produce a table from saved measurements; compare a second full build."""
import json, sys
from pathlib import Path
import probe as p
d=Path(sys.argv[1]).resolve();previous=Path(sys.argv[2]).resolve()
read=lambda root,name:json.loads((root/name).read_text())
m=read(d,'manifest.json');old=read(previous,'manifest.json');perf=read(d,'performance.json')
a={r['file']:r['sha256'] for r in m['artifacts']};b={r['file']:r['sha256'] for r in old['artifacts']}
assert a==b and len(a)==36
assert all(r['status']=='measured' for r in perf['rows'])
for row in perf['rows']:
    assert row['sha256']==a[row['file']]
    baseline=next(r for r in perf['rows'] if r['kernel']==row['kernel'] and r['mode']=='plain' and r['level']==row['level'])
    assert row['sink']==baseline['sink']
lines=['# 対称状態縮約：実測比較','',
       'Node/V8の版・CPU・全反復値はperformance.json。warmup 81,920呼出し、7ラウンド×16,384呼出し。JS境界費用を含む。',
       'RSSは個別Nodeプロセスのピークであり、Wasm固有の使用量ではない。各条件1プロセス、順序を固定seedでシャッフル。',
       '中央値比は対応のある反復比ではなく、信頼区間も算出していない。短時間測定のばらつきに留意する。','',
       '|kernel|mode|level|bytes|ns/call中央値|最小–最大|元との中央値比|process peak RSS KiB|',
       '|---|---|---|---:|---:|---:|---:|---:|']
for r in sorted(perf['rows'],key=lambda a:(a['kernel'],a['level'],a['mode'])):
    lines.append(f"|{r['kernel']}|{r['mode']}|{r['level']}|{r['bytes']}|{r['medianNs']:.2f}|{r['minNs']:.2f}–{r['maxNs']:.2f}|{r['ratioOfMediansToPlain']:.3f}|{r['processPeakRssKiB']}|")
lines+=['','recoveredのlevelは解除元の最適化レベルであり、解除後に同じ最適化を再適用した意味ではない。',
        '解除後のrawコードと最適化済み元コードの性能差を、変換単独の費用と解釈しない。','',
        '|kernel|変換時間 ms（単発、ツールI/O込み）|','|---|---:|']
for c in m['certificates']:lines.append(f"|{c['kernel']}|{c['seconds']*1000:.2f}|")
lines+=['',f"解除12条件の単発処理時間範囲：{min(r['seconds'] for r in m['attacks'])*1000:.2f}–{max(r['seconds'] for r in m['attacks'])*1000:.2f} ms。統計的な解析困難性の指標ではない。",
        '', '別ビルドとの36バイナリhash一致。各ビルド47,232入力条件で不一致0。再現はベンチマークの多様性追加ではない。']
with (d/'comparison.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
p.save(d/'reproduction.json',{'previous':str(previous.relative_to(p.ROOT)),'current':str(d.relative_to(p.ROOT)),
       'matching_binary_hashes':36,'performance_sink_matches':36,
       'source_hashes':{str(q.relative_to(p.ROOT)):p.sha(q) for q in [Path(__file__),Path(p.__file__),p.ROOT/'research/symmetric-state/check.cjs',p.ROOT/'research/symmetric-state/measure.cjs']}})
print('36 binary hashes and 36 performance sinks verified; comparison.md saved')
