# 実ffmpeg binaryの制御変種：7,320寿命差と同じ起動後memory

2026-10-24。[計画](post-start-live-plan.md)に基づく追加実行。**実復元器の不具合や動画変換の再現ではない。** 起動後の到達性がないsegmentを保持した制御変種を用い、内部状態差と元APIの差を混同しないための対照とする。

## 固定入力と変換

入力は`@ffmpeg/core-mt`0.12.10の32,718,323 byteの実配布binary。SHA256は`be2c97605366b78f3f13e21b52e81a55a79e1f29c133b03a68ec187b1a2ec41a`。元ファイルは変更していない。passive data 7,320個は全て非空で、内容は計5,258,971 bytes。start関数22605に全memory.init/data.dropがあり、元exportやliteral function referenceからこの関数に戻る到達経路はない。

[native抽出器](census-native/src/bin/start-drop-sites.rs)で、全data.dropの命令範囲を取得した。省略変種はstart内の7,320箇所を同じbyte長のnop列に置き換え、他の命令・data bytes・関数indexを保つ。[builder](post-start-live-build.py)は元hashと、各segmentに一つのdropがあることを検査する。観測版二本には元関数の後ろへzero-length init probeを追加し、新exportは検査だけに用いる。観測版の追加exportを元API到達性へ含めない。

変種のbare binaryと観測版二本はWABT1.0.42のvalidationを通過した。[入力・変換metadata](../../results/state-witness/post-start-live-input-v1/manifest.json)と全hashを保存した。bare変種にも到達検査を適用し、起動後readerなしという十分条件が元binaryと同じであることを確認した。

## 実行結果

Node24.15.0、Wasmtime50.0.1で、各binaryを別process内の一instanceとして逐次起動した。元の宣言通り1 GiB shared memoryを用意した。workerや並行アクセスは起動していない。実行前の空き物理memoryは約45.9 GBあり、3 GiB以上の条件を満たした。host関数は呼ばれたら失敗するstubであり、全起動・probe中のhost呼出しは0だった。

|engine|入力|live probe|trap probe|probe前後のmemory hash|
|---|---|---:|---:|---|
|Node|元のdropあり|0|7,320|一致|
|Node|drop省略|7,320|0|一致|
|Wasmtime|元のdropあり|0|7,320|一致|
|Wasmtime|drop省略|7,320|0|一致|

全四起動で1,073,741,824 bytesのmemory hashは`6140c107f9808d428cc60bb77194815843b83b4082504f260673eed6d50aa784`だった。export table `Ia`の長さも17,281で一致した。tableの全参照同値を動的に確認したという意味ではない。全29,280 probe callは非破壊な0長initである。

[実行結果](../../results/state-witness/post-start-live-v1/results.json)、[bare変種の再走査](../../results/state-witness/post-start-live-v1/retained-scan.json)を保存した。4 worker完了、error/timeout0。compile/instantiateの単発時間もlogにあるが、warmupや反復による性能実験ではなく、engine間の速度比較には用いない。

事前計画に含めたpure定数返却exportは入力に見付からず、**元exportのAPI実行数は0**である。JS glue・動画変換・実復元処理を実行したとはしない。元APIから寿命差を観測できないという判断は、動的な網羅試験ではなく、[到達性の十分条件と論証](post-start-proof.md)による。変種と元binaryのコード差も到達しないstart関数内だけである。時間・resource圧力/OOM、private debugger、保持された活性continuationは前提から除く。

## Bindingとharnessの区分

初回preflightはWasmtimeのshared memory有効化が必要だった。`wasm_threads=True`に加え`shared_memory=True`を設定した後、配布Python bindingの`SharedMemory._as_extern`がC unionの要求する一重pointerに二重pointerを渡すTypeErrorを再現した。これはWasmの実行差として数えていない。

[local adapter](post-start-live-bindings.py)は既存SharedMemoryの所有権を保持し、C unionへ一重pointerを渡す。そのアダプタで小controlのstore8/load8値47とhost側byte47の一致を検査してから本実行へ進んだ。[preflight log](../../results/state-witness/post-start-live-v1/preflight.json)にstock bindingのerrorと補正後の結果を残した。依存package自体は書き換えていない。アダプタは固定版のprivate bindingに依存し、別versionでの互換性は主張しない。作者への報告や確認は行っていない。

## 研究判断

実配布binaryに制御された寿命差を作ると、全内部状態一致を要求する検査は7,320差を報告する。一方、その差は元APIの起動後のreaderから観測できない。この対照は、内部差の件数をアプリ不具合件数へ換算しない理由を補強する。自然に発生した復元不具合やKの条件合成が必要な実例を発見した結果ではない。到達検査という既知原理の適用であるため、新しい一般アルゴリズムが確立したという判断にはしない。

全内部状態を一致させることが明示された契約なら、この7,320差の検出自体は正当である。元APIへの影響がないことだけで「先行検査器の誤検出」と扱わない。契約を切り替えずに評価ラベルだけを変更することはしない。

## 再現

既存の固定入力と依存環境から、rootで新しい出力directoryを指定する。

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/state-witness/census-native/Cargo.toml --release --offline --locked --target-dir .tools/state-witness-census-graph-target
python research/state-witness/post-start-live-build.py .tools/state-witness-ffmpeg-0.12.10-v1/core-mt/ffmpeg-core.wasm results/state-witness/live-input-new
python research/state-witness/post-start-live.py results/state-witness/live-input-new results/state-witness/live-new
```

初回の固定入力取得は[元のcorpus追加記録](post-start-results.md)を参照する。この32 MB inputと派生binaryは小artifact v3に含めない。
