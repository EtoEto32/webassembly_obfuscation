# GC参照の境界同一性を比較する試作

2026-10-27。**既存の単一値表示が失う共有関係を、Wasm本文を変えずに検査できた。ただし、初出順の参照番号付けは既知であり、この実装だけで修士主テーマの新規性が確立したとは判断しない。** [実装前計画](plan.md)、[実測と限界](results.md)、[先行研究との差](prior-art.md)。

例：2回の戻り値が同じstructの場合も、異なるstructの場合も、Binaryen133の `printed` は通常 `object(null), object(null)` と表示する。追加oracleは前者を `0,0`、後者を `0,1` と表す。fieldを読み出さず、値を引数へ戻す操作も追加しない。元の関数呼出しがすでにJSへ公開した参照だけが対象となる。

## 処理

1. 実行ごとにWeakMapと採番カウンタを初期化する。
2. 校正実験では既存host入力の参照を先に登録する。
3. import引数・export戻り値の参照が初出なら新番号を割り当て、再登場なら既存番号を記録する。nullは独立tokenとする。
4. 別実行の生のaddressを比べず、eventと番号列を比べる。通常の値・trapの比較も保持する。

同じ観測順の列に対し、この番号列が一致することは、各位置間の参照同一性が一致することと同値。これは既知の集合分割の正規表現であり、新しい定理として主張しない。未観測のheapやfield内容については何も保証しない。

## 再現

Windows / Python3.9 / Wasmtime Python50.0.1（検証とWAT変換）/ Node24.15.0 / SpiderMonkey150.0.1 / Binaryen133。既存 `.tools/import-alias-quotient-python`、`.tools/spidermonkey-150.0.1/js.exe`、`.tools/binaryen-version_133/bin/wasm-opt.exe` を使用する。追加npm package不要。

```powershell
python research/boundary-alias/experiment.py results/boundary-alias/fresh-probe
python research/boundary-alias/real-generator.py results/boundary-alias/fresh-generated
python research/boundary-alias/benchmark.py results/boundary-alias/fresh-probe results/boundary-alias/fresh-performance
python research/boundary-alias/triage.py results/boundary-alias/fresh-generated results/boundary-alias/fresh-triage
```

全て新規directoryを指定する。`real-generator.py` は64固定seed、生成/最適化10秒、各実行3秒の上限。標準fuzzerの `--no-fuzz-memory --no-fuzz-oob` を選ぶ。生成物へ独自の変換は加えない。追加JS loggerと、struct/arrayを判別する小さな別Wasm moduleを用いる。Wasm本文を変えなくても追加host処理やGC挙動への影響が完全にゼロとは主張しない。

対照の表示関数は `results/type-context/priors-v2/fuzz_shell.js` からverbatim抽出する。実生成器実験は同じupstream shell全体へ追加loggerを挿入する。手製fixtureに対して表示関数だけを使った実験と、実fuzzer harnessの実験を区別している。

保存済みデータの監査：`python research/boundary-alias/audit.py results/boundary-alias/fresh-audit`。この監査は保存済みv2系列を読み、126binary、36条件の時間中央値、22分類校正、9manifestを検査する。別の新規出力先を用いた全工程を二重実行済みという意味ではない。

**範囲外**：型固有fieldの意味、循環heap全体、function identity、custom descriptor、JSPI、GC回収タイミング。上記の実生成器版では表示関数が渡されたGC参照だけを数える。

追補：[型付きcallerとmulti-value観測の対照実験](caller-results.md)を追加した。64 seed・1,024 processで最小修正の効果と限界を測定した。新しい独立したseed群ではない。GCを観測したseedは40→46、同一参照が再登場したseedは2のまま。一般的な型付き呼出し列生成はRandoop/Weaverに近く、新方式とは主張しない。関数別名による184組の診断差も意味差から分離した。
