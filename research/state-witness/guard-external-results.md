# 実復元器への公開観測診断と適用限界

2026-10-24。[計画](guard-external-plan.md)、[入力生成](guard-external-generate.py)、[実行](guard-external-run.mjs)。先行実装のpin/buildは既存の[外部比較](external-results.md)と[Weave比較](weave-results.md)を引き継ぐ。

## 入力と対照

元APIだけで到達させた[8対照](guard-contract-results.md)から、retire内のelem.drop直後に恒偽loopを挿入した。private table長は1/4/16/32で、公開前上書きの有無を比較する。変換器に必要な1page memoryを追加する。元binary/memory追加/loop追加/変換後連続実行を比較し、元API終了結果と元公開tableの関数を実際に呼んだ返値が一致することを先に確認した。検査用exportやprivate tableのpatchは使わない。

[最初の入力](../../results/state-witness/guard-external-inputs-v1/manifest.json)は16変換中12本がvalidationを通った。wasm-migrateのtable.fill(ref.func)を含む上書き4本は、変換出力でfunction宣言参照が不整合となりinvalidだった。これは変換出力のvalidation failureであり、解析失敗や復元不一致に混ぜない。最初の集計v1にはinvalidをcontinuous mismatchにも数える集計式の誤りがあり、[v2](../../results/state-witness/guard-external-v2/results.json)で修正・再実行した。旧ログも保持した。

次に上書き対照を、privateな不変tableからのtable.copyへ変更した。上書き元は元関数aで初期化され、programから変更されないため、この閉じたAPIでの公開動作は同じである。変換器を修正したのではなく入力の別表現である。[入力v2](../../results/state-witness/guard-external-inputs-v2/manifest.json)の16本は全てvalidだった。

## 結果

|backend|入力条件|連続実行不一致|実復元|未到達|復元entry不一致|診断列での公開差|
|---|---:|---:|---:|---:|---:|---:|
|wasm-migrate 実験host|8|0|16|8|0|4|
|Weave 公開JS driver|8|0|16|8|0|0（全16列がtrapで終端）|

[Node実測v3](../../results/state-witness/guard-external-v3/results.json)のwasm-migrateでは、drop前のcheckpointは全て一致し、drop後のcheckpointで上書きなし4条件が異なった。復元entryの終了結果、最初のmaskのtrap、そこまでの公開tableは一致する。しかしmask後も呼べる実験hostでは、2/5/17/33呼出し目のpublishで公開関数返値が202対101となった。公開前上書きの4対照は一致した。これは同じ構成を大きさ違いで展開した4条件であり、独立した4不具合とは数えない。

[Wasmtimeによる再実行](../../results/state-witness/guard-external-cross-v1/results.json)でも、全16復元のtraceがNodeと一致した。API390呼出し、公開table関数24呼出し。これにはentry・中断・再開・連続対照を含み、以前の228診断呼出しとは集計範囲が異なる。

## 契約の制約

wasm-migrateの公開compute APIで変換したbinaryを従来の実験hostへ載せたが、選択entry以外のexportをtrap後に再呼出しする利用法が作者の保証範囲かは未確認である。この結果は**実験adapter上の復元差**であり、製品脆弱性や作者確認済み不具合とは主張しない。

Weaveの固定版`js/weave.mjs`はdrive内のtrapでlifecycleをfailedにし、次のdriveを状態エラーで拒否する。今回、連続8条件と復元16条件でこの拒否を実行確認した。raw export直呼びで制限を回避していない。従ってこのdriverに対して、trap後にcopy/publishする診断列を正当な反例として提出できない。core Wasmはtrap後に他の計算を開始できるが、host libraryの公開契約は別である。

この結果を受け、[終端protocol版](guard-protocol-plan.md)を実装した。復元器の利用規約を無視して広いAPI文脈の反例を当てはめる評価を避けるためである。既知のprotocol automatonという原理自体を新規と数えない。

```powershell
python research/state-witness/guard-external-generate.py results/state-witness/guard-contract-reachable-v1 results/state-witness/local-external-inputs --repair-copy
node research/state-witness/guard-external-run.mjs results/state-witness/local-external-inputs results/state-witness/local-external
python research/state-witness/guard-external-cross.py results/state-witness/local-external-inputs results/state-witness/local-external results/state-witness/local-external-cross
```
