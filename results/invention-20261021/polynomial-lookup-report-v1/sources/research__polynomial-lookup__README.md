# 静的リストの多項式表現：全体変換と回復費用

2026-10-21。局所decoderの抽出から離れ、元のnext/recordを実行時から除く
方向を実Wasmで検査した。**構造の削除と回復費用の増加は観測したが、
既知の集合多項式・補間から独立した新規性は未確立。主発明には採用しない。**
有限環残差方式の既存の構成的提案は維持し、研究全体を完了扱いにしない。

- [事前計画と先行資料](plan.md)
- [生成規則、攻撃モデル、意味保存](algorithm.md)
- [論文用分析](paper-note.md)
- [実測比較表](../../results/invention-20261021/polynomial-lookup-report-v1/comparison.md)
- [正当性](../../results/invention-20261021/polynomial-lookup-main-v2/checks.json)
- [解析の反復測定](../../results/invention-20261021/polynomial-lookup-audit-v1/analysis-timings.json)

## 確認した範囲

- 7入力集合（3既存サイズ、全u32乱数64件、端点13件、重複、空集合）。
  list/array/poly/poly-pruned/recoveredのraw/O3、70条件・92,230呼出しで不一致0。
  raw/O3は独立アプリではなく同じ対象の2形態。全入力の実験的証明ではない。
- 多項式28条件（poly14、pruned14）すべてから辞書を回復。元のsourceや他の
  source形態を解析入力に使っていない。O3でも係数による回復が成立した。
- WABT別実行器で各条件3入力、計210probe。Nodeの全入力の再試験ではない。
- 56生成物の再生成byte一致。元listはこの56本に含めず、保存hashを別に管理。
- 元field配置の変更2条件とlist順序変更で、同じ辞書は同じ多項式になる。
  ただし配列化対照でも同じことが起き、これだけは追加保護の証拠にならない。
- i64 Hornerの独立BigInt検査4,312組。欠けたkey範囲処理、value商の欠落、
  32bit積への誤変更の3負例を検出。公開memory・write・cycle・範囲外の4入力拒否。

## 費用

4データ集合×4方式×hit/miss×3 fresh process＝96 process。128回×16 iterationの
warmup後、約5msを目標に1024〜2^18回へ校正し、9batchの中央値を採用。
最終値は3process中央値の中央値。速い対照は上限に達し5ms未満になる。
入力はWasm内の配列から読み、返り値のchecksumを全batchで確認する。
同じquery列を各方式に使う。固定順でなくseed21102132でprocess順を混ぜた。

128件のO3では、hitがlist約61.9ns、array約16.6ns、poly約927.5ns、
pruned約623.4ns。missは約153.5/37.8/312.0/310.7ns。
prunedはpolyのhitを約33%短縮するが、既知の零多項式除去による改善。
全方式1page、peak RSSはNode全processの値で、方式単体のmemoryではない。

3 fresh Python processと3つの公開分割seedによる128件の回復中央値は、
arrayが読取込み約21.7ms、poly-pruned約669.6ms。うち回復本体は約0.35msと
647.8ms。増加を認めるが、標準Pythonの素朴な因数分解と専用array readerの比較。
NTLの最適化版、人間の解析時間、未知方式の認識費用は未測定。実行時間との
単純な比を安全性指標にはしない。同費用の既存obfuscatorとの優位性も未確立。

## 再現

Python3.9、Node24.15.0、WABT1.0.42、Binaryen133。追加package不要。
共通readerは`research/isotope-swizzle/prototype.py`と
`research/connectivity-elimination/prototype.py`。既存3入力は
`results/invention-20261021/notdec-baseline-v1`を使う。リポジトリrootから
未作成の出力先を指定する。重い測定を他処理と並行させない。

```powershell
python research/polynomial-lookup/run.py results/polynomial-new/main
python research/polynomial-lookup/performance.py results/polynomial-new/main results/polynomial-new/runtime
python research/polynomial-lookup/audit.py results/polynomial-new/main results/polynomial-new/audit
python research/polynomial-lookup/extra.py results/polynomial-new/main results/polynomial-new/extra
python research/polynomial-lookup/report.py results/polynomial-new/main results/polynomial-new/runtime results/polynomial-new/audit results/polynomial-new/extra results/polynomial-new/report
```

単独CLI：`python research/polynomial-lookup/prototype.py transform INPUT.wasm OUTPUT.wasm --mode poly-pruned`。
回復CLI：`python research/polynomial-lookup/prototype.py recover INPUT.wasm OUTPUT.wasm`。

main-v1は56条件の初期実装。零の商多項式を毎回評価する費用を切り分けるため、
prunedを加えたmain-v2を主結果とした。v1とv2を独立した検証数に合算しない。
今回はテスト不合格・解析timeout・クラッシュを保護効果に算入したものはない。

## 残る研究課題

静的構造を消しても同じ辞書を回復する課題は残るが、今回は既知の単変数
因数分解へ直接帰着する。件数・次数や係数表を増やすだけを新案としない。
次の案には、元プログラムに基づく別の具体的生成規則と、既知の構造削除だけでは
得られない費用上の効果が必要。NotDecの環境は未構築で、本成果はその型回復を
阻止した実験ではない。未対応を耐性として数えていない。
