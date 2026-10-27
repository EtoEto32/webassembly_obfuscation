# 現memoryを利用する共有退避の生成

2026-10-23。**同じ符号化表現を保つ保存処理の改良を実装した。新しい保護原理・独立した特許性は未確立。** 先行するcoded side-informationに近い。保存量は減ったが、修復の一時値は別に必要で、総メモリ削減とは主張しない。

[事前計画](plan.md)、[規則・最小性の限定論証](algorithm.md)、[先行技術と判断](prior-art.md)、[実測集計](../../results/invention-20261023/side-save-report-v1/report.md)。

|copy構造|入口保持する独立byte値（basis→side）|side修復temporary i32数|basis→side実行中央値ns|O3 core byte（basis→side）|
|---|---:|---:|---:|---:|
|swap16|4→1|4|8.055→7.697|1298→1484|
|rotate32|32→4|31|59.394→51.209|6355→6881|
|ladder64|10→1|10|36.815→36.977|11094→13807|

保存次元は2seedとも上表の値。性能はseed211070のみ、同じB同じcopy列で比較。rotate32は中央値で約13.8%短縮、swap16はprocess間のばらつきが重なり明確な高速化としない。ladder64は約0.4%増。code sizeと宣言local総数は増加した。plainの約3.49/9.59/14.56倍の実行時間である。

主正42実行条件37,184呼出し、うち期待trap19,152で不一致0。6境界状態、各byteのみ255の状態、固定seedランダム64状態から連続runし、毎回全64KiBの物理像とdigestを検査した。12のbad条件はtrap前修復を省き、全て反例を得た。同じ3人工copy構造の派生版と回復版であり、42アプリの評価ではない。

変更していない既存の回復器がbasis12とside12をraw/O3とも元sourceとbyte一致するWasmへ戻した。別WABTは正294呼出し・168trap・最終memory1,652点で一致。54本byte再生成、3つのsource未対応拒否を確認。3bit小モデル6,048問題は全16subspace探索の最小値と一致、状態prefix145,152比較も一致。追加4次元1,000問題は全67subspaceの最小値と一致した。全Wasm処理系の数学的同値証明ではない。

性能は27 fresh process×7 batch、warmup32,768、約15msへcalibrate、全batch10ms以上。別Wasm moduleからsafe fail値を変えてrunを呼ぶ。正常出口のみで、繰り返すと状態が安定する固定copy列。3process中央値の中央値を使用。Node全体RSS、coreサイズ、変換時間を記録し、register/stack実測・CPU affinity・他CPUはなし。side変換81.27–132.45ms、回復43.04–127.24msは各条件1回の診断値。

## 再現

Windows、Python3.9.0、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。追加Python package不要。`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使用し、`WASM_TOOLS_ROOT`でも指定可能。repository rootから未作成の出力directoryへ実行する。

```powershell
python research/side-save/model.py results/new-side/model
python research/side-save/holdout.py results/new-side/holdout
python research/side-save/run.py results/new-side/main
python research/side-save/performance.py results/new-side/main results/new-side/runtime
python research/side-save/audit.py results/new-side/main results/new-side/audit
python research/side-save/report.py results/new-side/main results/new-side/model results/new-side/holdout results/new-side/runtime results/new-side/audit results/new-side/report
python research/side-save/prototype.py INPUT.wasm OUTPUT.wasm --seed 211070
```

共有helperはprefix-repairのprototype/recover/check、copy-centralizer/model、isotope-swizzle/prototype、connectivity-elimination/prototype、loss-flag/bench。snapshotに同梱する。対象の実Wasm source profile、前提、非対応機能はalgorithm.md。主難読化方式の発明目標は引き続き未達で、今回の費用改善は補助部品として保持する。
