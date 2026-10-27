# 状態被覆と商の回復費用（2026-10-19）

**実Wasm変換と測定は完了したが、特許・論文の主発明には採用しない。** 状態の複製で静的な全状態解析の費用は増えた。しかし、少数の代表状態を調べる適応的解析が大部分を省略でき、公開I/O学習の問い合わせ列も複製数で変わらなかった。状態分割自体に近い先行研究もある。回復成功だけを不採用理由にはしていない。

[事前仮説](plan.md)、[構成と意味保存](algorithm.md)、[測定と判断](analysis.md)、[先行研究・公報](prior-art.md)、[日本語草稿](paper-note.md)。研究全体の[評価方針](../evaluation-policy.md)に従う。

## 実装範囲

`prototype.py transform input.wasm output.wasm --copies 256` は、指定形式の最大16状態・二文字DFA scannerを実際のバイナリから読み取り、状態被覆へ変換する。任意のWasmを処理する実装ではない。公開APIは `run(pointer:i32,length:i32)->i32` と固定1pageの `memory`。各入力byteの下位bitを文字とする。非exportの第2memoryに遷移表を置き、公開memoryの内容・load順・trapを保存する。非exportはバイナリの秘匿を意味しない。

最大32,768状態。追加memoryは最大6page。imports、共有memory、memory growth、任意の副作用、他の公開APIは非対応。モジュールの生成・実行に必要な資源を利用できることを前提とする。追加memoryによるinstantiate時の資源不足まで同値とはしない。

`prototype.py recover input.wasm output.wasm` はバイナリ中の表とコードを抽出し、全状態の分割改良により小さなDFAを作る。raw/O3の再生成照合で対応するテンプレートを検査する。seed・元DFA・隣のJSONは読まない。一般の逆コンパイラではなく、別の最適化形や初期化を消去された形は未対応となり得る。

`learn.cjs` は公開APIのみを呼ぶL*観測表の学習器。真の等価性oracleは持たず、長さ8以下の全語と2,000個の固定random語で反例を探す。`adaptive.py` は表から95個の継続語の出力を調べ、同じfingerprintを持つ状態を代表1個にまとめる。どちらも出力候補の完全な同値性を自己証明しない。

## 結果

主結果は[quotient-lift-v3](../../results/invention-20261019/quotient-lift-v3/)。4モデル × 元/表のみ/複製16/256/2048 × raw/O3 = 40条件。静的回復32本・公開I/O回復40本を加え112本。

|検査|結果|
|---|---|
|WABT/Node validation、値・trap・全公開memory|112本、231,280呼出し、30,688 trap、不一致0|
|別エンジンWABT|672呼出し、2,688 memory probe、不一致0|
|全状態解析|32/32で等価DFAを回復|
|代表状態の適応的解析|32/32で同じ静的回復cloneを得た。最大33物理状態をprobe|
|公開I/O学習|40/40の候補を事後の積探索で同値と確認。各条件3 fresh process|
|有限探索の限界|長さ32の例外語を両heuristicが見逃す対照を保存|
|拒否・モデル検査|3種の有効だが範囲外のWasmを拒否。384モデル条件で商・被覆に不一致0|
|再現|v2/v3の112本のbyte一致。query transcriptも同一モデルの全方式で一致|

正当性の差分試験は全Wasm・全入力の数学的同値性の証明ではない。実行負荷は10,000回warmup、3,000呼出し×11標本、条件ごと3 fresh process。64byte/call。120 processを直列実行した。全表・ばらつきは[summary.json](../../results/invention-20261019/quotient-lift-v3/summary.json)に保存。

例として16状態モデルのO3では、単純表版111.20 ns/call・319 bytesから、複製2,048版240.73 ns/call・393,347 bytesへ増加。全状態解析は0.0454 msから91.1778 msへ増えたが、適応的解析は2.8493 msで候補を回復した。公開学習は両方3,097問い合わせ。この増分効果を認めつつ、表拡大に比例する困難さとは主張しない。

## 再現

既存のPython 3.9.0（標準library）、Node 24.15.0/V8 13.6.233.17、WABT 1.0.42、Binaryen 133を使用。WABTのmulti-memoryはこの版で既定有効。Binaryenには `--enable-multimemory` を渡す。`.tools/` を使用し、`WASM_TOOLS_ROOT`で変更できる。外部サービス、秘密鍵、新規依存の取得は不要。

測定hostはWindows x64、Intel Core i9-11900K、16 logical CPU。[実行環境の観測](../../results/invention-20261019/quotient-lift-v3/environment-observed.json)と[最終監査](../../results/invention-20261019/quotient-final-audit-v1.json)を保存した。

リポジトリrootから、未使用の出力名を指定する。既存の結果を上書きしない。性能測定中は他の実験を同時実行しない。

```powershell
python research/quotient-lift/run.py results/invention-20261019/quotient-local
python research/quotient-lift/interpreter.py results/invention-20261019/quotient-local results/invention-20261019/quotient-local-interpreter
python research/quotient-lift/controls.py results/invention-20261019/quotient-local-controls
python research/quotient-lift/adaptive.py results/invention-20261019/quotient-local results/invention-20261019/quotient-local-adaptive
python research/quotient-lift/audit.py results/invention-20261019/quotient-local-audit.json
```

`audit.py`は保存済みの主結果を監査する。`run.py --compare <既存結果dir>`で生成バイナリの一致も検査できる。ソースcopy/SHA256、実測JSON、WAT/Wasm、WABTログを保存。v1はWABTの不要なenable flag指定で停止した実装不備、v2は学習時間にload等を含めた初回値。v3では学習時間を分離し3回測定した。これらの不備を解析耐性には数えない。

新規で有効な主発明の確立は未達。外部公開・push・出願は行っていない。
