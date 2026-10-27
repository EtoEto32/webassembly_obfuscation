# 元entryだけを使うhost効果の復元比較

2026-10-24。[計画](guard-import-entry-plan.md)、[入力生成](guard-import-entry-inputs.py)、[Node実行](guard-import-entry.mjs)、[Wasmtime追試](guard-import-entry-cross.py)。前の公開memory実験に残った「非entry APIの呼出しが保証されるか」という限界を、別の元programで取り除くための対照である。

元programが公開する関数はentryだけである。host.touchという元からあるimportを呼び、指定された条件ではmemory[7]へ0を書く。host呼出し列も移行対象としてadapterが明示的に保存する。外部ネットワークやファイルI/Oは使わない。Weave側では公開serviceのsnapshot/restoreを使い、復元準備で外部効果を発生させない。

## 結果

4元fixtureを両復元器へ変換した8binaryは全てvalidationを通った。各fixtureでhost書込み有無の2条件を実行した。元/変換後の無移行結果は全て一致した。

|Nodeでの観測|wasm-migrate|Weave|
|---|---:|---:|
|fixture × host条件|8|8|
|到達したcheckpointからの復元|24|24|
|checkpoint未到達|8|8|
|最終entry return/trapの差|0|0|
|host呼出し列の差|0|0|
|元guest memoryの差|4|0|

[Node結果](../../results/state-witness/guard-import-entry-v1/results.json)。4差は1byte/4byteの二つのサイズ対照×stop1/stop2で、同じ既知の寿命復元問題に関係する。host書込みがある条件に限り、元は先頭byte0のままtrapする一方、復元後はdata Aから17を再度書いてからtrapした。いずれのcheckpointでも保存時のhost traceは空で、再開後にtouchを1回だけ呼んでいる。host効果の二重実行やskipによる差ではなかった。

書込みなし、stop0、mask前に元bytesへ修復する対照、init長0の対照は一致した。Weaveは24復元の全てで元entry結果・host trace・guest memoryが一致した。trap後にdriverへ再入する手順は使っていない。

[Wasmtime追試](../../results/state-witness/guard-import-entry-cross-v1/results.json)もmigrate24復元で同じ4memory差・host trace差0となった。72 entry呼出しと48回の実際のtouch呼出しを実行した。snapshotで引き継いだtrace要素は新たなhost呼出し数に加算していない。WeaveのJS driverをWasmtimeで再実装した比較ではない。

## 意味することと限界

同じentryが同じtrapで終わり、host呼出し列も同じでも、公開memoryが異なる場合を実証した。非entry APIのサポート有無に依存しない例になった一方、importsを含むこのprogramは現行K parserの受理対象外である。実対象での現象を再現できたことと、解析器がそのprogramを直接診断できたことを混同しない。

追補：[同期import profile](guard-import-results.md)を別に実装し、これらの元binaryの指定された継続部分について条件を生成できるようになった。元のclosed parserのimports拒否は維持する。後の実装を、この実験時点で自動診断済みだった証拠として扱わない。

これは単一固定commit、管理したlocal host、手書きfixtureの実験である。新しい独立した4bug、作者確認済み脆弱性、一般のhostサービス移行の正しさは主張しない。外部公開・報告はしていない。

```powershell
python research/state-witness/guard-import-entry-inputs.py results/state-witness/local-import-inputs
node research/state-witness/guard-import-entry.mjs results/state-witness/local-import-inputs results/state-witness/local-import-node
python research/state-witness/guard-import-entry-cross.py results/state-witness/local-import-inputs results/state-witness/local-import-node results/state-witness/local-import-cross
```
