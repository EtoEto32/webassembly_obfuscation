# Weaveによる正常な復元対照

2026-10-24。[事前計画](weave-plan.md)どおり、Weave固定commit `55e36b5f5d5b31d14f1521c3a4327c248ddeba19` のlibraryと公開JS adapterを実行した。library sourceは変更せず、transform-only CLIを追加した。20ファイル・361,425 bytesのGit blob / SHA-256を確認し、Cargo.lockとbuildログを保存した。

[Node結果](../../results/state-witness/weave-v1/results.json)と[Wasmtime結果](../../results/state-witness/weave-cross-v1/results.json)で、8変換条件・**32回の到達した復元比較がすべて一致**した。非空passive保持、非空passive破棄、空passive破棄、active dataの4種をKあり・なしで検査した。各条件の無移行対照も元binaryと一致した。Wasmtime側は公開ABIのmemory/control globalsを独自のhostで復元し、Node公開adapterの結果と行単位で一致した。

これはWeave全体の正当性証明ではない。有限loopを追加してentry/back-edge checkpointを発生させた小さな系列であり、wasm-migrateのblock境界と同じ中断位置ではない。両者の速度比較もしていない。Weaveが既に実装するsegment寿命再現の有効性を、読み取りだけでなく実行でも確認した結果である。

## 検査器側の重要な条件

Weaveはexportをwrapperへ変換し、呼出し時にcontrol globals等を更新する。従って元のK probeの非破壊性は、別の変換後の物理metadataにそのまま成り立つわけではない。保存後にsourceを観測して破棄し、復元先も観測専用とresume専用に分けた。これをしないで発生した再開失敗をWeaveの欠陥として数えてはいけない。

checkpoint時の追加観測はsegmentに限定した。table/globalをrehydrateする前の全state比較は行っていない。実行後のmemory[0]と元APIの正常/trapを主oracleにした。

## 再現

```powershell
python research/state-witness/fetch-weave.py --out .tools/weave-fresh
python research/state-witness/prepare-weave.py --root .tools/weave-fresh
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --release --manifest-path .tools/weave-fresh/Cargo.toml -p weave-probe *> .tools/weave-fresh/build.log
python research/state-witness/weave-run.py results/state-witness/local-weave --build .tools/weave-fresh
python research/state-witness/weave-cross.py results/state-witness/local-weave results/state-witness/local-weave-cross
```

公開依存の取得にはnetworkが必要。今回buildはfetch後に`--offline --locked`で実行した。保存したlockfileを使うことで依存のversionも固定できる。
