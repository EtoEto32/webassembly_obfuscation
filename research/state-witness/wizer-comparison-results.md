# Wizerの著者配布CLIによる直接確認

2026-10-25。[事前計画](wizer-comparison-plan.md)、[実測結果](../../results/state-witness/wizer-comparison-v1/summary.json)。今回使ったのは公式Wasmtime 50.0.0 (`ebe5e8df1`, 2026-10-20) の `wizer` subcommandである。配布ZIPのSHA256はGitHub release digestと一致した。Python package 50.0.1をCLI版番号として推測した最初の取得は404で、公開release一覧から実在する50.0.0を選び直した。

## 実行結果

|入力|Wizerの結果|後続の観測|
|---|---|---|
|active/passiveの順序2通り × 初期化時memory上書き有無|4/4受理|両engineで返値/trap/公開memoryが一致|
|initializer内のdata.drop|明示的未対応|復元実行なし|
|後続APIだけにあるdata.drop|明示的未対応|復元実行なし|
|到達不能なprivate関数だけのdata.drop|明示的未対応|復元実行なし|
|後続APIだけにあるtable.init|明示的未対応|復元実行なし|

受理した4出力はWABT validationを通過した。元側だけinitializerを実行し、その後は両側へ同じ5 APIを呼んだ。各engineで20観測対、元API40呼出し、元initializer4呼出しを実行し、差は0。NodeとWasmtime Python間でも観測列が一致した。初期化済みmemory値、passiveからのcopy、active由来segmentの0長initの成功/境界trapを含む。

## sourceとの対応

[固定releaseのrewrite.rs](https://github.com/bytecodealliance/wasmtime/blob/v50.0.0/crates/wizer/src/rewrite.rs) は元active dataを空のpassive segmentにし、元passive dataはそのまま保持する。snapshot memoryの初期化dataは末尾へ追加し、元data indexを維持する。[lib.rs](https://github.com/bytecodealliance/wasmtime/blob/v50.0.0/crates/wizer/src/lib.rs) は寿命を動的に取得できないことを説明してdrop命令を拒否する。

読んだ範囲は7 source/config fileのうち、主にlib.rsのAPI・validation、rewrite.rsのdata/data-count処理、parse/infoのdataの扱いである。全Wizer実装の検証や著者の全testの再現ではない。source provenanceは[固定commit](../../.tools/state-witness-wizer-review-v1/provenance.json)と[実行したrelease](../../.tools/state-witness-wasmtime-cli-v50.0.0/provenance.json)に分けて保存した。両版のlib.rs/rewrite.rsのSHA256は一致する。

## Kの新規性への影響

segmentの状態が復元の正しさに関係すること、active/passiveを区別して保存することは先行実装にある。Wizerはこのprofileを誤って受理するのではなく、範囲外として拒否する。未対応4例を不具合・誤検出・Kの勝利と数えない。

Kは復元器の代替ではない。Kが条件を出せる例がWizerの拒否集合に含まれても、それだけでは新しい解析能力や重要な実用途を証明しない。Wizerに安全な対応拡張を実装した結果でもない。この対照は、既存技術の差を厳しく区分する証拠である。

```powershell
python research/state-witness/wasmtime-cli-fetch.py .tools/state-witness-wasmtime-cli-v50.0.0
python research/state-witness/wizer-comparison.py results/state-witness/wizer-comparison-new
```

初めの行は未取得の場合だけ実行する。既存directoryへの上書きは拒否する。
