# 実用共有memory標本と、起動後に読めない寿命差

2026-10-24。[事前計画](post-start-plan.md)、[十分条件の論証](post-start-proof.md)、[実行結果](../../results/state-witness/post-start-v1/applications.json)。**ffmpeg.wasm core-mt 0.12.10には明示dropがあるが、起動後の寿命差を問題にする自然な例にはならなかった。**

## 固定した標本

公式repositoryの[core-mt package設定](https://github.com/ffmpegwasm/ffmpeg.wasm/blob/main/packages/core-mt/package.json)と[利用手順](https://github.com/ffmpegwasm/ffmpeg.wasm/blob/main/apps/website/docs/getting-started/usage.md)を確認し、npmのcore/core-mt両方を0.12.10に固定した。tarballのregistry SHA512を照合し、wasmとpackage.jsonだけ取得した。アプリ/installerは実行していない。目的抽出なので[従来242本](coverage-results.md)へ混ぜて使用率を計算しない。

|package|binary bytes|passive data|memory.init|data.drop|全readerの関数|
|---|---:|---:|---:|---:|---|
|@ffmpeg/core|32,232,419|0|0|0|なし|
|@ffmpeg/core-mt|32,718,323|7,320|7,320|7,320|startの22605だけ|

[最初の静的結果](../../results/state-witness/modern-census-v2/results.json)と取得[provenance](../../results/state-witness/modern-census-v2/provenance.json)を保存した。coreのSHA256は`9f57947a5bd530d8f00c5b3f2cb2a3492faa7e5d823315342d6a8656d0a6b7b7`、core-mtは`be2c97605366b78f3f13e21b52e81a55a79e1f29c133b03a68ec187b1a2ec41a`。

## 過大近似の到達検査

export関数に加え、到達不能code、global/table初期化、active/passive/declarative element内も含む全literal関数参照をrootにした。direct/tail callの閉包からreaderを探した。GCのarray segment操作4種もreaderに含めた。

coreは15,583 rootから22,280関数、core-mtは15,783 rootから22,605関数が到達集合になった。どちらもreaderは0。core-mtのstart関数22605はこの集合に含まれない。正常instantiation完了後、保留内部frame/continuationがなく、違いがsegment寿命だけであるなら、その相違は将来の通常API観測に影響しない、という十分条件が成立した。shared memoryの内容やhost状態を含めた復元の正しさは判定していない。

start途中のcheckpointや、復元変換がstartを追加exportする場合にはこの結論を流用できない。後者では変換後moduleを再検査する必要がある。ffmpegのhost実装や実復元を動的に実行した結果でもない。

## 検査器の対照

[19 control](../../results/state-witness/post-start-v1/controls.json)で事前指定の静的判定に一致した。private start、exportされたstart、直接/多段/tail call、elementを通る間接call、global/table/ref.func参照、dropのみ、0長init、unreachable後のreader、GC reader4種を含む。

うち通常の15 controlでは、二つのinstanceのmemoryを揃え、片方だけdata.dropしてentryを呼んだ。Node24.15/V8 13.6とWasmtime50.0.1の各15組・30 entry call・15準備callが一致した。7組は差なし、8組は差ありだった。静的「不明」の中にも、実際のこのentryでは差が出ない対照がある。reader到達を不具合と誤認する検査ではない。GC4種はnative validationと静的分類で検査し、この動的件数へ入れていない。

## 研究判断

後続の[escape対照](../../results/state-witness/post-start-escape-v1/manifest.json)では、非exportのreader関数をstart内のimportへ渡す、globalへ格納する、tableへ格納する3経路を作った。hostが保持した参照を起動後に呼ぶと、寿命差によりreturn/trapが分かれた。各engine3組・6参照call・3準備callで一致した。export関数だけをrootとする意図的mutantは3例とも誤って安全とした。全literal参照をrootへ入れる必要性の対照であり、新しい実製品bugではない。

時間・resource pressure/OOMを対象外とする前提を出力にも明記した[再実行v2](../../results/state-witness/post-start-v2/applications.json)でも、19 controlとffmpegの到達結果は同じだった。segmentの物理領域解放によるメモリ消費差まで無影響とはしていない。

これはKを有利に見せる結果ではない。自然なdropを発見しても、起動後にその寿命が観測できなければ、Kの複雑な条件合成は必要ない。既知の到達検査だけで十分な実用例だった。追加した検査器を独立した発明数に加えず、過大な実用性主張を避けるための適用判定として保持する。

## 再現と実行上の記録

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/state-witness/census-native/Cargo.toml --release --offline --locked --target-dir .tools/state-witness-census-graph-target
python research/state-witness/post-start.py .tools/state-witness-ffmpeg-0.12.10-v1 results/state-witness/local-post-start
```

依存cacheと公開npm標本が必要。第三者の取得用scriptは[fetch-modern-corpus.py](fetch-modern-corpus.py)。初回の通常network取得はDNS失敗、公開npm取得の権限拡張後は成功した。最初のmodern-census-v1はrelative path処理で停止し、sourceをabsolute化してv2を作った。これらをWasm解析失敗や意味上の反例に数えない。
