# 既知の等式解析との比較：K固有の能力・速度差は残らなかった

2026-10-25。[事前計画](guard-herbrand-plan.md)に沿う反証実験。本文を確認したESOP2005の等式WP/未知値規則を、copy/constantだけの汎用IRに適用した。著者実装の再現や一般Herbrand項の完全な実装ではない。

## 実装の独立範囲

[copy-equality.py](copy-equality.py)はWasm/segmentを持たない有限graphのbackendである。同時代入、等式要求、左右へ共通の未知値を入れる操作、省略可能な操作を扱う。等式の正規化はgraph連結成分で別実装し、Kのcanonical/pullback/close/transformを呼ばない。may-writeはcellごとの選択を合成し、Kの無書込み/全上書きへの簡約を使わない。

[lowering](guard-herbrand.py)は既存のWasm parserと区間effectを共有する。したがって、Wasm意味論を独立に検証した結果ではない。backend同士が共通のfrontend bugを見逃す可能性は残る。

## 同じ条件が得られるか

|入力集合|契約数|初期条件と全状態条件の一致|
|---|---:|---:|
|初期import対照|256|256|
|may-write対照|128|128|
|長さ1/8/32/96のchain|16|16|
|必須/任意書込みで結論が変わる2-import対照|4|4|
|合計|404|404|

全反復版と既知のfact worklist版の両方で一致した。400/404は既存の試験であり、今回新たな独立Wasm programを404本作った意味ではない。raw resultsは[基本](../../results/state-witness/guard-herbrand-atomic-v1/results.json)、[may](../../results/state-witness/guard-herbrand-atomic-may-v1/results.json)、[chain](../../results/state-witness/guard-herbrand-atomic-chain-v1/results.json)、[区別対照](../../results/state-witness/guard-herbrand-atomic-pair-v1/results.json)に保存した。

## 同じ出力・前処理範囲での費用

4方法それぞれ3独立process、各条件2 warmup+5測定。実行順を固定seedで入れ替えた。conditionのみを生成し、全方法とも反例rank履歴を保存しない。Wasm parse時間を別記し、graph作成/loweringを測定内に含める。全12 processが完了し、timeout/error0。全workerでZ3未ロードを検査した。Windows working setとpeakも記録した。

代表としてhostが公開storeを読み、必ず上書きするchainを示す。単位ms、process内中央値のprocess間中央値。

|chain長|K worklist|汎用等式 worklist|K全反復|汎用等式 全反復|
|---:|---:|---:|---:|---:|
|1|0.560|0.342|0.498|0.324|
|8|1.849|0.992|3.928|2.409|
|32|7.920|3.380|37.138|24.143|
|96|34.392|9.381|293.609|191.055|

全16人工chain条件では汎用等式worklistがK worklistより約1.5–3.7倍速かった。[生値・process間ばらつき](../../results/state-witness/guard-herbrand-cost-v1/results.json)。汎用等式版はlowering時に観測集合・代入を用意し、反復中のWasm向け条件構築を減らす。これも既知の実装上の改善であり、逆にこの対照を新発明と数え直さない。

この速度比は人工入力の条件計算についてであり、実アプリでの全処理時間、著者の最良実装、一般Wasmの解析性能を表さない。Kから再生可能な反例を得る全pipelineと、この条件のみのbackendの性能比較でもない。

## 研究判断

汎用SMTに対する過去の速度差だけを、K固有の解析能力・速度優位の根拠にすることはできなくなった。適切な既知の等式解析を対照にすると、同じ条件が得られ、今回の実装では速度もKを上回った。現状のKを「新しい解析アルゴリズム」を主張する修士研究の主テーマとして推奨しない。

Wasm復元の契約・元APIの反例・観測器の干渉を区別した実証研究としては再検討できる。しかし自然な用途で既存評価の判断を改善する証拠が必要であり、今回の計算速度だけではその未達を埋められない。

```powershell
python research/state-witness/guard-herbrand.py results/state-witness/guard-import-controls-v1 results/state-witness/herbrand-new --schedule atomic
python research/state-witness/guard-herbrand-cost.py results/state-witness/guard-import-direct-chain-v2 results/state-witness/herbrand-cost-new
```
