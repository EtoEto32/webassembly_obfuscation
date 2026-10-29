# 混合resourceの前向き検査と条件の維持

2026-10-24。[事前計画](guard-holdout-plan.md)を固定してから96 moduleを生成した。memory/table/混合各32本、半分は乱数body、半分はtrapで片側の書込みを隠すprefixを持つ。実アプリ分布を模したものではない。full/public/returnsとreenter/terminalの6契約、各4初期storeを検査した。

## 結果

|項目|実測|
|---|---:|
|module / 契約 / 初期store|96 / 576 / 2,304|
|一致条件を満たすstore|1,846|
|うち条件に合わせて生成 / 乱数のまま|1,102 / 744|
|反例があるstore（全て乱数のまま）|458|
|各engineのAPI呼出し|173,588|
|各engineの共通trapでの列終了|15,353|
|得られた反例列の最大長|2|
|別array式の検査義務|2,838 UNSAT / 0 unknown|

[Node結果](../../results/state-witness/guard-holdout-v1/results.json)、[生成入力・条件](../../results/state-witness/guard-holdout-v1/manifest.json)、[Wasmtime追試](../../results/state-witness/guard-holdout-cross-v1/results.json)、[式の照合](../../results/state-witness/guard-holdout-check-v1/results.json)。Wasmtimeでは別途101,630回の純粋定数関数呼出しでtable参照を照合した。NodeとWasmtimeの件数を独立テストケースとして加算しない。肯定例では全単発APIと16本の乱数列を実行しただけであり、その有限実行を全列の証明とはしない。検証式も共有parserから作った限定model上の検査である。

|契約|無条件一致|条件付き一致|満たす初期storeなし|
|---|---:|---:|---:|
|full / reenter|41|50|5|
|full / terminal|41|51|4|
|public / reenter|57|35|4|
|public / terminal|58|34|4|
|returns / reenter|66|26|4|
|returns / terminal|92|0|4|

terminal/returnsの96条件は専用の一回判定とも一致した。乱数例を追加しても一般的なアルゴリズム新規性が強くなったわけではなく、契約の組合せと実装に対する反証範囲が広がった。

## 初期条件が途中で壊れる例

混合例mixed-15では、full/terminalなら初期tableの1cellについての条件で一致するが、full/reenterではどの初期storeも一致しない。原因をmemoryだけに縮めた3対照を[guard-drift.py](guard-drift.py)で作った。形式的な最小化ではない。[binary・条件・Wasmtime trace](../../results/state-witness/guard-drift-v1/manifest.json)、[Node trace](../../results/state-witness/guard-drift-v1/results.json)に保存した。

公開memoryの先頭をA（65）とする。passive dataはAとBの二つ。元APIのprefixで、左は両方drop済み、右はBだけdrop済みへ到達する。追加exportやprivate patchは使わない。

* `mask` はAを先頭へinitし、Aをdropし、Bをinitする。左は最初にtrap、右はAを書いてから最後にtrapする。最初のmemory[0]がAなら一回の観測は同じである。
* `clear-traps` は両側のmemory[0]を0にしてからdrop済みBのinitでtrapする。
* `clear-returns` は同じ0への書込みをして正常終了する。
* `clear-preserves` はmemory[0]をAにしてから共通trapする。

full/public契約の全API列についての条件は次のようになった。

|clearの種類|reenter|terminal|
|---|---|---|
|0を書いてtrap|充足不能|memory[0] = 65|
|0を書いて正常終了|充足不能|充足不能|
|65を書いてtrap|memory[0] = 65|memory[0] = 65|

`clear-traps → mask` では、最初の共通trap後も続けられると、2回目に左0・右65になる。終端契約なら2回目へ進めない。一方、`clear-returns` の後なら終端契約でも続けられる。このため「trapの前後で同じ条件を一回確認する」だけでは不十分で、継続可能なAPIによって条件が維持されるかが必要となる。一般的な不変条件・最弱前提の既知の性質を、Wasmのpartial writeとhost契約へ具体化した例である。

returns契約では全て無条件一致となった。3対照×6契約をNode/Wasmtimeで照合し、それぞれ診断API108回・状態準備API84回が一致した。これは人工的な反例であり、新しい実製品不具合ではない。

## 再現

出力先は未作成のdirectoryを指定する。

```powershell
python research/state-witness/guard-holdout.py results/state-witness/local-holdout
python research/state-witness/guard-holdout-cross.py results/state-witness/local-holdout results/state-witness/local-holdout-cross
python research/state-witness/guard-holdout-check.py results/state-witness/local-holdout results/state-witness/local-holdout-check
python research/state-witness/guard-drift.py results/state-witness/local-drift
```
