# 公開wasm-migrateでの復元反例と原因の切り分け

2026-10-24。**外部の公開変換器を実行し、復元後の元APIの結果差を確認した。Kの新規性の証明ではない。** [事前条件](external-plan.md)を固定してから実験した。外部への報告や公開はしていない。

## 対象と実行条件

[Tinto / Marchiori / Vardanega, JSA 168 (2025), 103532](https://doi.org/10.1016/j.sysarc.2025.103532)に対応する[公開wasm-migrate](https://github.com/TintoEdoardo/wasm-tools/tree/e28a37cd2c00f0f5026bbc79651a50cbea6172dd)。本文のabstract、設計§3.3、評価・discussionの該当箇所を読み、公開評価driverも確認した。論文はempty operand stackでのcheckpointを前提としている。今回の例はその条件を満たす。ただし、論文の全benchmarkやネットワーク移行を再現したものではない。

固定commitのlibraryを最小Rust workspaceでbuildした。元sourceのprivate moduleから公開関数をimportする箇所でbuildが失敗したため、`wasm-mutate/src/lib.rs`の`mod module`を公開し、そのmoduleの`missing_docs` lintだけを許可した。関数本体には変更を加えていない。公開API `WasmMigrate::new().compute(&bytes, true)` を使用し、最初のdefined関数を対象とした。

local host adapterは公開評価driverと同様に`memory`と`checkpoint_memory`のbytesを保存し、fresh instanceの`host.restore_memory`で戻す。`host.should_migrate`の所定回数で停止を要求する。要求によるtrapと、要求に到達しない自然なtrapを区別する。original / transformed continuous / checkpoint-restoredの三条件を比較した。

## 主記録

[external-v3](../../results/state-witness/external-v3/results.json)、[Wasmtime追試](../../results/state-witness/external-cross-v1/results.json)。4 fixture × plain / observedの8変換binaryがvalidationを通過し、全8条件でoriginalとcontinuousが一致した。Node 24.15 / V8 13.6とWasmtime 50.0.1で結果JSONの行が完全一致した。

fixtureはmemory[0]を第1blockで11、第2blockで22にし、最後に0長`memory.init`を実行してから1を加える。非空passive dataを保持する例、途中でdropする例、空segmentをdropする例、active dataの例を比較した。plainにはKのobserverを付けない。

|第2checkpointから復元|無中断の期待値|復元後|Kによるsource / resumedのsegment観測|
|---|---|---|---|
|非空passiveを保持|正常終了・23|正常終了・23|成功 / 成功|
|非空passiveをdrop|trap・22|**正常終了・23**|**trap / 成功**|
|空passiveをdrop|正常終了・23|正常終了・23|trap / trap|
|active data|trap・22|trap・22|trap / trap|

第1checkpointでは4 fixtureとも処理の一部が飛ばされ、23→12または22→11という別の結果差があった。transformed WATではresume用localが選択したregion以降も非0のままで、後のregionをskipする。第3checkpointは全条件で未到達として記録し、復元結果に数えない。

8変換条件 × 到達した2checkpoint = 16比較のうち10不一致。ただしplain / observedの重複と同じ原因の変種を含むため、**10個の新規bugという集計はしない**。単一commit・local adapterでの二つの意味上の問題候補であり、作者確認済みのbug、脆弱性、CVEとは主張しない。

## 原因に対する介入実験

[external-isolate-v1](../../results/state-witness/external-isolate-v1/results.json)では、二つの因子を独立に補った。これはupstreamそのものの測定と区別する。

- segment因子：Kがsourceで空を観測した場合だけ、fresh instanceの検査専用helperで`data.drop`を再実行する。既知の寿命再現であり新規方式ではない。
- selector因子：対象がこの2region・localなしfixtureの形であることを検査し、選択regionに入った後にresume localを0へ戻す。汎用の修正版ではない。region再実行が無害な代入・dropに限定している。

|selector介入|segment介入|比較数|元API不一致|
|---|---|---:|---:|
|なし|なし|8|5|
|なし|あり|8|4|
|あり|なし|8|1|
|あり|あり|8|0|

segmentだけ補うと、第2checkpointのdrop例の不一致が消え、他の制御フロー差は残る。selectorだけ補うと逆になる。この限定例では、二つの原因を混同せず説明できる。一般の非冪等regionやtable/global/stackを正しく復元する修正の証明ではない。

## 再ビルドと再実行

元188 sourceにlicense、build用test宣言の参照先、root manifest/lockを加えた195ファイル、3,509,314 bytesを公開固定commitから再取得し、Git blob SHA-1とSHA-256を確認した。独立した`.tools/wasm-migrate-reproduction`を作って同じ修正を適用した。Cargo.lockと修正後sourceも初回と一致し、[external-reproduction-v1](../../results/state-witness/external-reproduction-v1/results.json)の**16 Wasm binaryがbyte単位で一致、結果JSONも一致**した。

fresh directoryでの手順（Rust toolchainとCargoの公開依存が必要）：

```powershell
python research/state-witness/fetch-migrate.py --out .tools/wasm-migrate-fresh
python research/state-witness/prepare-migrate.py --root .tools/wasm-migrate-fresh
python research/state-witness/repair-migrate-build.py --root .tools/wasm-migrate-fresh
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --release --manifest-path .tools/wasm-migrate-fresh/Cargo.toml -p wasm-migrate-probe
python research/state-witness/external-run.py results/state-witness/local-external --build .tools/wasm-migrate-fresh
python research/state-witness/external-cross.py results/state-witness/local-external results/state-witness/local-external-cross
python research/state-witness/external-isolate.py results/state-witness/local-external results/state-witness/local-external-isolate --build .tools/wasm-migrate-fresh
```

初回Cargo.lockは最小workspaceへ合わせて更新される。完全な依存固定で追試する際は保存した`upstream-Cargo.lock`をbuild directoryへ配置し、`--locked`を付ける。キャッシュ済み環境では`--offline`を使った。

v1はoracleが途中のskipを見落とすことと未到達checkpointを復元対象にする誤りがあり、主結果にしない。v2で修正し、v3で空・active対照を追加した。失敗履歴も残している。

## 修士研究として支持される範囲

Kは自作mutant以外でも意味状態の欠落を説明できた。しかし、元APIの差はKなしでも見つかり、0長probeとdrop再現は既存技術である。現時点の貢献候補は、Wasm復元の検査契約、state分類、観測可能性、反例の原因切り分けを一貫して評価する手順と実証である。検査アルゴリズム自体の優位、複数独立実装への一般化、未報告性は未確立である。
