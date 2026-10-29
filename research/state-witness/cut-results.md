# 公式testへ中断点を作る生成器：結果と反証

2026-10-24。[事前計画と仮説変更](cut-plan.md)、[集計JSON](../../results/state-witness/cut-analysis-v1/results.json)。**動作する検査生成器と外部実装の反例は得たが、未知の原理を発明したとは結論しない。**

## 入力と生成規則

固定した公式specのmemory_init/table_initから、引数・戻り値なしのexport関数、最上位のdrop、既知のstack消費完結命令という条件で14 moduleを選んだ。17のdrop位置ごとに、有限・副作用なしのloopを挿入する。tableのみの7 moduleには、wasm-migrateのhost契約を満たすため1page memoryを追加した。元APIは元の名前で呼び出す。

```text
for each accepted closed module M:
    for each zero-argument, void exported function f:
        for each top-level data.drop / elem.drop at p:
            verify the restricted stack-empty body profile
            make M' by inserting N copies of (loop (br_if 0 (i32.const 0))) at p+1
            check original M and M' agree without migration
            transform M' with each checkpoint implementation
            count actual polls in the uninterrupted execution
            for each reachable poll:
                suspend, capture before observing, restore to a fresh instance, resume
                compare the original entry outcome and projected guest state
                separately report segment differences before and after resume
```

loopは条件が定数falseでback-edgeを取らず、値も残さず、guest storeを変更しない。追加命令のfuel/time/resource消費はこの意味保存条件から除く。入力がこのrestricted profileを満たす場合の局所論証であり、任意のWasmへ無条件に使える証明ではない。

tableの内容は、元の参照先が引数なし・i32定数を返す純粋関数であることを構文で確認してから、その返却値で照合した。これは公式由来fixtureのtag oracleであり、一般の関数参照同値を解くものではない。globalを持つseedは対象外とした。

## 無移行と復元の比較

0個、入口へ1個、drop後1個、drop後2個の4条件を測定した。各条件17例 × 2変換器 × Kあり・なしの68変換がすべてvalidationを通った。合計272条件のcontinuous比較に不一致0。cut前後の元APIとguest stateも一致した。

以下はKありの行だけを示す。Kなしでもentryの成功/trap結果とmemory/tableの分類は同じだった。

|挿入|wasm-migrateの到達復元数|entry成功/trap不一致|差の出た元module数|Weaveの到達復元数|Weaveのentry不一致|
|---|---:|---:|---:|---:|---:|
|0個|0|—|—|0|—|
|入口へ1個|17|0|0|34|0|
|drop後1個|31|4|4|34|0|
|drop後2個|48|8|4|51|0|

0個版は中断に到達していないので、復元成功0件として数えない。変換器のpoll生成規則が異なるため、構文上のloop数と中断数も一致しない。全4条件、plain/observedを含めた到達復元は**1 engine当たり430回**。Nodeと独立したWasmtime hostの全272行が一致した。同じ反例の2 engine再現や複数中断点を、別々のbugとして数えない。

元API差の出た4 moduleは `memory_init/suite.8`、`memory_init/suite.10`、`table_init/suite.16`、`table_init/suite.18`。data/element寿命が復元に反映されない場合の反例であり、独立した4原因と主張しない。著者確認も得ていない。対象commitとlocal host契約に限った意味保存の結果である。

## アブレーションから分かったこと

二つのdelimiterを必要条件とする当初説明は棄却した。1個でも同じ4 moduleを検出し、2個版は同じ問題に遭遇する中断点を増やしただけだった。入口へ置くだけでは差が出ず、寿命変更後へ置くことがこの系列では有効だった。ただし、比較数も異なるので一般的な費用対効果の優越とはしない。

事後に「最初に到達した点だけ」「最後に到達した点だけ」の各17回を抽出すると、drop後1個版は前者0、後者4のentry差だった。後者の選択を事前登録した独立評価ではないため、未見programでの検出率予測に使わない。

## 状態差をそのまま不具合にできない

drop後2個版のwasm-migrateでは、中断直後のsegment差46回に対し、再開後にも残るsegment差は26回だった。20回では後続の再実行によってsegmentの差が解消した。さらに、再開後のsegment差だけが残り、entry結果とmemory/tableが同じケースが18回あった。これら18回は追加observerが見つけた差であり、元APIの不正やセキュリティ影響は未証明である。

従って、完全state snapshot契約、再実行を許すcontinuation契約、元APIの観測同値を区別する必要がある。Kのdescriptorは原因の分類に使えるが、state相違の件数を脆弱性件数に変換してはいけない。

追試：[18回の残存差の分類](context-results.md)では、元programの限定APIモデルで16回の同一観測と2回の反例を得た。復元器内部の再開制御を含む証明ではないため、この2回を上流の追加bugとして集計しない。

## 新規性の反証

Weaveの既存[`hard_features.rs`](https://github.com/dphilla/weave/blob/55e36b5f5d5b31d14f1521c3a4327c248ddeba19/crates/weave-transform/tests/hard_features.rs)には既に`data.drop → loop → memory.init`をcheckpoint後に検査する手書きtestがある。従って「dropをまたぐ中断を作る」という原理自体は既存である。今回の差は、公式binaryから位置を抽出する実装、複数の復元器に対する共通評価、observer差と元API差の分離にあるが、これだけで強いアルゴリズム的新規性が成立するとは断言できない。

同commitの`spec-corpus.sh`と`spec-corpus-inputs.py`を読んだ範囲では、抽出moduleのtransform/validationとprovenanceを検査していた。別の`differential.rs`や`semantic-conformance.sh`には実行・復元の意味比較がある。これらを「既存手法は検証していない」とまとめるのは誤りである。

## 再現と費用

`prepare-migrate-target.py`は既存libraryのpublic `func_index`を指定する別CLIだけを作る。上流の変換本体を変更しない。既存の[依存build手順](external-results.md)と[Weave build手順](weave-results.md)の後に実行する。

```powershell
python research/state-witness/prepare-migrate-target.py
$env:CARGO_HOME = Join-Path (Get-Location) '.tools/wasm-migrate-cargo'
cargo build --offline --locked --release --manifest-path .tools/wasm-migrate-build/Cargo.toml --bin wasm-migrate-target
python research/state-witness/cut-generate.py results/state-witness/spec-v4 results/state-witness/local-cuts --delimiters 1
node research/state-witness/cut-run.mjs results/state-witness/local-cuts results/state-witness/local-cut-run
python research/state-witness/cut-cross.py results/state-witness/local-cuts results/state-witness/local-cut-run results/state-witness/local-cut-cross
```

`--delimiters 0/1/2`、`--placement entry/after-drop`で対照を生成する。出力先は新しいdirectoryにする。CLI追加scriptは既存fileを上書きしない。最初の特定buildを参照するため、別パスへの配置時はscript内のbuildパスの調整が必要。

17例・68変換の生成は今回の単回測定で約4.43秒だった（WABT起動・検証・file出力含む）。反復性能実験とはしない。修正後の生成器で再生成し、[reproduction入力](../../results/state-witness/cut-inputs-reproduction-v1/manifest.json)の136 Wasm binaryが初回とbyte単位で一致し、[結果JSON](../../results/state-witness/cut-reproduction-v1/results.json)も一致した。

修士研究としては「復元検査で何を観測すべきか」という実証候補が強まった。一方、完全に別原理の新アルゴリズムを確立した、という当初の強い目標は未達である。
