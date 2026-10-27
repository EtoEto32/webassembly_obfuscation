# 型に合う呼出し・複数戻り値観測の対照実験

2026-10-27。**既存harnessの小さな修正で観測範囲は広がるが、追加の自然発生した誤コンパイルは見つかっていない。呼出し列を型付き値poolで生成する一般案も既存研究と重なる。新アルゴリズムとは主張しない。**

## 固定条件

[実装前計画](caller-plan.md)に従い、前段で保存したBinaryen133の64 seedを再利用した。独立した64個の新規seedを増やした実験ではない。O0/O3の128 binaryは元データとbyte一致。Rust wasmparser0.262.0で関数型・import・exportの対応を抽出し、upstreamのfuzz_shell.jsへcaller/observerを挿入する。対象Wasmは無変更。各条件fresh process、3秒上限、Node24.15.0とSpiderMonkey150.0.1。

- caller `null`：実装元と同じ全引数null。`typed`：既知のi64引数だけBigIntの0n、他の数値は0、参照はnull。非null参照の構築はしない。
- observer `flat`：既存printedが受け取ったGC参照のみ。`multi`：既知のmulti-value戻り値のJS Arrayの各slotも観測する。一般のJS object/GC fieldを走査しない。
- 64 seed × 2 level × 2 caller × 2 observer × 2 engine = **1,024 process**。全process終了、timeout/crashなし。4 seedはstart時にtrapし、各条件でinstantiate失敗。これを関数の正常終了に数えない。

## O0、1 engineあたりの結果

両engineの件数は一致した。表は各64 process。既知関数の呼出し287件を分母とする。別にglobal値表示などの型未取得wrapper呼出し258件があり、全てreturnedだった。全545件をWasm関数の成功率と呼ばない。

|caller / observer|既知関数returned|trap|TypeError|RangeError|GC参照を観測したseed|同一参照が再登場したseed|GC event|
|---|---:|---:|---:|---:|---:|---:|---:|
|null / flat|180|81|24|2|40|2|106|
|null / multi|180|81|24|2|45|2|121|
|typed / flat|193|91|1|2|40|2|109|
|typed / multi|193|91|1|2|46|2|126|

multi-valueの検査slot数はnullで53、typedで77。GCでないslotも含む。型付き呼出しで解消した23 TypeErrorのうち14件はreturned、9件はtrapへ進んだ。さらにseed10では先行するfunc_13が実行されるようになった後、後続func_13_invokerがreturnedからtrapへ変わった。したがって集計差はreturned +13、trap +10である。これは同じmodule instanceへの呼出し列であり、各関数を独立した初期状態から測った結果ではない。因果の細部は未追跡。残るTypeErrorはseed0のharness再入経路のundefined関数参照で、i64変換失敗とは分ける。

共有関係の再登場は依然seed17/21の2本だけで、型付き呼出しやmulti観測で増えなかった。追加のengine不具合検出は0。観測event数増加をbug検出力の増加と同一視しない。

## 比較・測定器の修正

最適化前後512組、engine間512条件で、GC eventの `(初出番号, channel, slot)` 列と呼出しstatus列は一致した。null/flatの256条件は前段の実験の参照番号列とも一致した。数値戻り値・任意の副作用を全て比較したという意味ではない。

初回の[report.json](../../results/boundary-alias/caller-v1/report.json)は、callの比較へ診断用の関数名も含めていたため184組を不一致とした。全240箇所を調べ、元の名前と新しい名前は最適化後のmetadataで同一function indexに対応していた。関数統合でJS関数objectの最初のexport別名が変わったことによるもの。status列の差は0だった。元reportは改変せず保存し、[監査report](../../results/boundary-alias/caller-audit-v1/report.json)でこの区別を修正した。今後のrunnerはcomparison_version=2でlabelsを別集計する。意味が異なる結果を名前の正規化で隠したわけではない。

10手製fixture × 4 mode × 2 engine = 80 process、104 callの校正も実施。i64、数値、非null参照、v128、同一関数別名、importの再export、再入呼出し、trap、同一/別GC参照のmulti-valueを含む。80/80が期待どおり、無効・過大binaryの拒否2/2。非null参照とv128のTypeErrorは対応済み成功とは数えない。校正v1の結果書込み時の例外は部分記録として保存した。

実行時間はprocess全体中央値でNode約51.5–52.6 ms、SpiderMonkey約24.2–24.4 ms。各seed/条件1回で起動・compile込み。warmup後のguest演算費用を分離していないため、各修正の実行時overheadや速度優位性は未確定。追加metadata/helperのサイズはtarget binary増分ではない。

監査は3 manifestの2,807 entry、128 metadata再抽出、128 targetの元binary一致、1,024 stdoutからの再集計、512+512+256比較を確認し、残る不一致0。これは独立した全実験の二重実行ではない。

## 先行研究による棄却条件

Carlos Pacheco, Shuvendu K. Lahiri, Michael D. Ernst, Thomas Ball, **Feedback-directed Random Test Generation**, ICSE2007 pp.75–84（査読会議）。[著者ページ](https://homes.cs.washington.edu/~mernst/pubs/feedback-testgen-icse2007-abstract.html)、[本文](https://homes.cs.washington.edu/~mernst/pubs/feedback-testgen-icse2007.pdf)。abstract、Figure2、§2.1–2.3、関連研究の該当部分を読んだ。型に合う既存結果の再利用、呼出し列の連結、同じobjectの再利用と別object構築、実行feedbackによる候補選択はRandoopで既知。単にGC参照をpoolへ入れて共有/非共有の引数を試すだけでは原理差は弱い。著者報告の大規模評価は未再現。

Lingming Zhang, Binbin Zhao, Puzhuo Liu, Qinge Xie, Peng Di, Jianhai Chen, Shouling Ji, **Weaver: Fuzzing JavaScript Engines at the JavaScript-WebAssembly Boundary**, arXiv:2603.18789v1, 2026-03-19（プレプリント）。[本文](https://arxiv.org/html/2603.18789v1)。abstract/intro、§IIIの型追跡・生成・scheduler、§IV実装、§V-C失敗分類と§V-Dの該当部分を確認。JS/Wasm両方の型、export結果の後続生成への利用、GCを含む生成、validityに基づく選択を扱う。v128/exnref系の境界除外や型推論の限界も記述する。型付きpoolと有効なcallの優先だけを新規性にしない。保存元は[取得manifest](../../results/boundary-alias/caller-priors-v1/manifest.json)。

## 判断

今回の最小修正は強い対照として採用する。修士研究の主題を確立したとは扱わない。次は、単なる呼出し成功の増加ではなく、**標準engineのまま到達可能なGC内部状態を何処まで正しく比較できるか**を検討する。型付き読み出しhelperも既知のreflection/serializationに近いため、対象program無変更という性質だけでは新規性を認めない。最適化による合法的な型・表現変更を誤検知しない観測契約が必要である。実装前に先行技術と反例を確認する。

## 再現

```powershell
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --manifest-path research/boundary-alias/interface/Cargo.toml --release --locked --offline --target-dir .tools/boundary-alias-interface-target
python research/boundary-alias/caller-calibration.py results/boundary-alias/fresh-caller-calibration
python research/boundary-alias/caller-experiment.py results/boundary-alias/fresh-caller
python research/boundary-alias/caller-audit.py results/boundary-alias/fresh-caller-audit
```

各出力先は新規directory。auditは保存済みcaller-v1等を読む。実験には前段binaryen-v2と取得済upstream shellが必要。Cargo.lockとraw stdout/stderrを保存している。
