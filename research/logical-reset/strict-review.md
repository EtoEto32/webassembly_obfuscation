# Jの厳格な再評価（2026-10-24、修士研究へ目的変更）

現在の選定基準は修士研究としての新規性・検証可能性である。過去の請求項案は履歴として保持し、出願を目的に作業を続けない。

## 判定

**Jの広い構成上の新規性は弱い。新しい主方式としての採用を見送る。** 同じinstanceを宣言初期状態へ戻す狭い用途差は残るが、主要な機構の多くが公開実装Weaveに既に存在する。正当性検査の通過と、この用途での高速化は、その機構自体の新規性を示さない。

## 最近接実装の直接比較

[Weave](https://github.com/dphilla/weave/tree/55e36b5f5d5b31d14f1521c3a4327c248ddeba19)をcommit `55e36b5f5d5b31d14f1521c3a4327c248ddeba19`（GitHub commit日時2026-10-08）に固定。公開ソースであり、査読論文とは扱わない。初回9ファイルの取得元とhashは `.tools/weave-review/provenance.json`。追加で[実行比較](../state-witness/weave-results.md)を行い、32復元で元APIとsegment分類が2 engineで一致した。

|観点|Weaveで実際に読んだ実装|Jとの関係|
|---|---|---|
|論理memory容量|[memory.rs](https://github.com/dphilla/weave/blob/55e36b5f5d5b31d14f1521c3a4327c248ddeba19/crates/weave-transform/src/memory.rs)、97行以降のbounds、141行以降のgrow|容量分離・64bit検査・元max・成長域zero-fillは既存|
|segmentの寿命|[DESIGN §1.5](https://github.com/dphilla/weave/blob/55e36b5f5d5b31d14f1521c3a4327c248ddeba19/docs/DESIGN.md)、[emit.rs](https://github.com/dphilla/weave/blob/55e36b5f5d5b31d14f1521c3a4327c248ddeba19/crates/weave-transform/src/emit.rs)1714行以降|物理segmentを保持してflagでinitを制限する構成は既存|
|0長initのtrap|同emit.rsのHelperKind::Init、及び[memory_semantics.rs](https://github.com/dphilla/weave/blob/55e36b5f5d5b31d14f1521c3a4327c248ddeba19/crates/weave-transform/tests/memory_semantics.rs)421行以降|境界の扱いも既存。J独自とはしない|
|table復元|emit.rsのgen_rehydrate（1205行以降）とGrow helper（1528行以降）|保存長への成長・entry再構築を実装。読んだ部分はnative table.size/growを使い、縮小用論理長ではない|
|用途|実行中のcheckpoint/migrationと再開|Jは停止中の同一instanceを初期状態へ戻す。用途・table縮小・高水位再利用に狭い差はある|

この比較からWeaveの誤動作を主張しない。WeaveはJの任意の過去状態への同一instance巻戻しを契約していない。用途を取り違えて差分をバグにしない。

追加でTintoほかの[wasm-migrate](https://github.com/TintoEdoardo/wasm-tools/tree/e28a37cd2c00f0f5026bbc79651a50cbea6172dd/crates/wasm-migrate)の取得済みcommit `e28a37cd2c00f0f5026bbc79651a50cbea6172dd` を読んだ。lib.rs 1085–1167ではcall index以外の命令をそのまま再encodeし、評価側main.rs 153–236は新Engine/Store/Instanceへbytesを復元する。これだけを根拠にプロジェクト全体の機能欠如とは断定しない。取得記録は `.tools/wasm-migrate-review/provenance.json`。

[WAFL](https://github.com/fgsect/WAFL)はcommit `436546bd4ca1edbf5e036a58a71501592f28b4e3` のMemory.cpp 443–508でmemory snapshot、Instance.cpp 500–535でsegment vectorを含むclone、Compartment.cpp 78–141で複数種の状態cloneを確認した。従って「既存runtimeはmemoryしか扱えない」とは言えない。どの呼出経路がどの契約を満たすかの実行確認は未実施。

## 強い性能対照の追加

[pooling実測](../../results/logical-reset/pooling-v1/results.json)。Windows / Wasmtime 50.0.1、5独立process、3 warmup + 15測定round。Pythonのdispatch費用を除くためRust製C API loop内で測定。cached Moduleからのfresh Store/Instance生成・破棄と、再利用instanceのreset+同じ仕事を比較。両方の仕事を1回のWasm呼出しに包み、両方で元のexportを保持した。

|初期memory|仕事|fresh pooling ns/request|J ns/request|processごとの比の中央値|
|---|---|---:|---:|---:|
|64 KiB|64 KiB走査更新|54,607|40,027|0.725|
|256 KiB|64 KiB走査更新|57,721|42,558|0.725|
|4 MiB|64 KiB走査更新|67,515|158,580|2.349|
|4 MiB|1 MiB走査更新|648,870|770,160|1.202|
|4 MiB|grow/drop＋64 KiB走査|71,420|162,595|2.288|

全105条件のprocess中央値、比の四分位数、生データを保存した。小memoryでは有利だが、初期memory全体を消す費用が大きいとpoolingに劣る。通常allocator・pooling・compact設定を含めるが、Linux最適設定の優位を調べた結果ではない。keep_resident設定はWindowsでは効果がないと[公式API](https://docs.wasmtime.dev/api/wasmtime/struct.PoolingAllocationConfig.html)が説明する。新実験のmode別RSSは未測定。過去のNode測定との数値の直接比較はしない。

再現:

```powershell
python research/logical-reset/pooling-inputs.py results/logical-reset/pooling-inputs-local
python research/logical-reset/pooling.py results/logical-reset/pooling-inputs-local results/logical-reset/pooling-local
```

## 次の研究原理

復元機構を追加するJから、復元の正しさを独立に観測するKへ移る。単に同じguardを変更した案にはしない。Kの選定理由・反証条件は [state-witnessの事前計画](../state-witness/plan.md) に固定する。JはKの自作評価対象の一つであり、Kの成功を証明する正解としてのみ扱わない。
