# 既知のworklist計算による厳しい比較

2026-10-24。[事前計画](guard-import-worklist-plan.md)に基づく。新発明案ではなく、Kの条件合成を既知の分配的データフロー計算として解く比較実装である。

## 方法と論証の範囲

各寿命状態対に必要な等式atomの集合を保持し、局所観測を種にする。追加されたatomだけを前任API edgeのWPで逆伝播する。同じatomを二度追加しない。集合の正規化が定数矛盾を検出した場合はfalseを伝播する。個々のatomが満たせても連言が矛盾する場合があり、この処理を省かない。

共有するWPは意味上 `WP(R ∧ S) = WP(R) ∧ WP(S)` を満たす。copy/constant代入・共通host入力の普遍量化・局所観測との連言はこの性質を保つ。trap終端では後続条件を捨て、局所条件だけを返すため、そこでも成立する。従って局所条件と各atomの伝播で、全連言の反復と同じ条件を得られる。canonical化は論理的同値を保存するという既存実装の前提を用いる。

これはIFDS著者実装でも、一般IFDSへの完全な符号化の証明でもない。生atom集合に加えて等式の矛盾検査を行う。参考文献は有限factと分配的flow関数の先行性を示す。[実装](guard-import-worklist.py)はparser・一段WPをKと共有するので、独立したWasm意味論検査には数えない。

有限のcellと定数から作るatomは有限である。実装の上限は寿命状態対1,024、追加fact250,000、sweep反復1,024で、超過はunsupportedとする。今回の集合で到達はなかった。

## 条件一致

|集合|件数|結果|
|---|---:|---|
|旧import対照|256契約|全初期条件・全寿命状態対の条件が一致|
|may-write対照|128契約|同上|
|1/8/32/96 cell、read/must/may組合せ|16契約|同上|

[旧対照ログ](../../results/state-witness/guard-import-worklist-v1/results.json)、[mayログ](../../results/state-witness/guard-import-worklist-may-v1/results.json)、[chainログ](../../results/state-witness/guard-import-worklist-chain-v1/results.json)。rank履歴なしの全反復版も旧256・may128契約で同じ条件を得た。同じ意味論を別の順序で計算した結果で、400件の実製品不具合ではない。

## 条件生成の費用

両方式ともrank履歴を保持しない。共通parseは計時外・別記録で、状態graph構築・条件生成・出力正規化を含む。3独立process/方式、2warmup＋5測定反復、逐次起動、固定seedによるcase順shuffle。6process、error/timeout0。[全16条件の生データ](../../results/state-witness/guard-import-worklist-cost-v1/results.json)を保存した。代表として必須全書込み・host readありを示す。

|private cell数|atom worklist中央値|全連言sweep中央値|sweep/worklist|
|---|---:|---:|---:|
|1|0.589 ms|0.503 ms|0.86|
|8|1.888 ms|3.839 ms|2.03|
|32|7.745 ms|36.541 ms|4.72|
|96|33.407 ms|281.443 ms|8.42|

may-writeの96 cell二条件は約8.40/8.65倍、1 cellではworklistが遅い。必須全書込み・readなしの無条件一致は約同速度だった。長距離伝播の人工例で、既知の増分処理が全連言の再処理を省けるという結果である。先行著者toolを超える新原理の証拠ではない。

memory計測moduleがZ3をloadするため、両processにZ3を含む。workerにはprocess memoryも保存し、単独CLIのmemoryとはしない。反例rank/入力/実行列を生成しないので、反例付き解析全体の速度ではない。

## 研究判断

KがSMTより速い場合も、有限等式への特化や既知の計算順の効果で説明できる。固有の一般解析能力は示せない。修士研究として残る候補はWasm復元状態と観測契約の対応付け、契約の誤解による誤診の反証、限定条件/反例の再現可能な実装である。自然な用途と主題の独自性が不足するという判断を維持する。

```powershell
python research/state-witness/guard-import-worklist.py results/state-witness/guard-import-controls-v1 results/state-witness/worklist-new
python research/state-witness/guard-import-worklist.py results/state-witness/guard-import-may-controls-v1 results/state-witness/worklist-may-new
python research/state-witness/guard-import-worklist.py results/state-witness/guard-import-direct-chain-v2 results/state-witness/worklist-chain-new
python research/state-witness/guard-import-worklist-cost.py results/state-witness/guard-import-direct-chain-v2 results/state-witness/worklist-cost-new
```
