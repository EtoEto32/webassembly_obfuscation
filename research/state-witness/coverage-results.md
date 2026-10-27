# 実アプリ由来corpusの寿命命令調査：否定的な結果

2026-10-24。[事前計画](coverage-plan.md)。取得済みのNoWaSet/NodeWasmStudy 220 fileとWasm-R3の23 file、計243 fileを対象にした。空の1 fileを除く242本を最後まで静的解析できたが、明示的な`data.drop` / `elem.drop`は0本だった。これらのcorpusで自然な寿命破棄をまたぐ復元問題を実証できた、とは言えない。

## 結果と検査器の差

初回の[WABT disassembly調査](../../results/state-witness/coverage-v1/results.json)は、225本完了、15本出力上限、2本validation失敗、1本空だった。全体の使用率を完了subsetだけから出さないため、wasmparserによるnative scannerを追加した。

[native結果](../../results/state-witness/coverage-native-v1/results.json)はWABT完了225本の命令数と全て一致した。残る15本は出力展開をせず最後まで読めた。WABTの2失敗はlinking custom metadataのversionと既定設定のthreads拒否で、wasmparserのall-featuresによるcore validationは通った。custom metadataまで同じ検査をしたわけではなく、既存validatorのbugとは扱わない。空fileだけは引き続きparseできない。

|corpus|対象file|native完了|passive dataを持つ|明示dropを持つ|memory.init命令数|
|---|---:|---:|---:|---:|---:|
|NoWaSet/NodeWasmStudy|220|219|0|0|0|
|Wasm-R3取得分|23|23|10|0|1,742|

NoWaSetにはshared memoryを持つ1本があるが、そのbinaryにもpassive dataや明示dropはなかった。R3は記録をstandalone replayへ変換したデータであり、見つかった1,742命令を元アプリにそのまま存在した命令数とは扱わない。静的存在数であって実行回数ではない。

入力と取得記録のSHA256、元URL、native実行fileのhash、Cargo.lock、scanner sourceを保存した。NoWaSetはcommit `53118203addbc9d421deb83289c282dfe7f27173`、R3は`576f499476060026f6c18cf6edd255ffcbeb5e4f`。新たな外部ファイルは取得していない。現在のWeb全体や2026年の全Wasmの無作為標本ではない。

## 仮説への影響

別に目的抽出した[ffmpeg.wasmの2標本](post-start-results.md)では、core-mtに7,320個の明示dropが見つかった。ただし全readerが非公開startに集中し、起動後の通常APIから到達できなかった。元corpusの0件を置き換える結果でも、Kの自然な不具合事例でもない。

Kの定数bulk profileの実装検査と、実復元器の小さな反例は残る。一方、「自然なアプリの寿命破棄で広く発生する問題」という動機は、この調査で支持されなかった。小例を増やしてこの不足を埋めたことにしない。修士研究として採る場合も、限定意味論の条件・反例・契約境界に価値を絞り、自然な用途の検証は未達とする。

寿命操作が実用上どこにもないという結論でもない。[公式Linking convention](https://github.com/WebAssembly/tool-conventions/blob/main/Linking.md?plain=1)のShared Memory and Passive Segments節では、thread生成時の再初期化を避けるため、共有memoryのstart関数でpassive segmentのinit/dropを行うと説明する。この領域はKの現行shared/start除外にかかる。しかもstartだけで使われるsegmentなら、起動後APIから寿命差を観測できない可能性がある。命令を発見することと、復元後に意味差が出ることも分ける必要がある。

## 再現

```powershell
python research/state-witness/coverage.py results/state-witness/local-coverage
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/state-witness/census-native/Cargo.toml --release --offline --locked --target-dir .tools/state-witness-census-target
python research/state-witness/coverage-native.py results/state-witness/local-coverage results/state-witness/local-coverage-native
```

Rust scannerはwasmparser0.227.1、serde_json1.0.142を使う。offline buildは既存cacheがある環境の手順であり、第三者が依存なしでbuildできるという意味ではない。これは静的調査であり、243 fileのアプリを実行したという結果ではない。
