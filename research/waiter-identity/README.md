# H: 通知で共有メモリの実体関係を検査する試作

2026-10-24。**動く別原理の候補であり、特許新規性は未確立**。shared WebAssembly.Memoryの別ラッパーを、内容を書き換えずに同じ実体ごとへ分ける。公開予算方式Fとは異なる、同期queueの関係を利用する境界検査である。

`===`では見落とすclone後のaliasを確認した。290分割条件・904メモリhash照合を通過し、worker往復・grow・realmを含む追加11条件も検査した。ただしqueueを変更するため、検査offsetの外部wait/notifyを排除する必要がある。並行byte更新への限定対応も評価した。正しいhost登録IDが使える場合は、その方が速く前提も単純。

[計画](plan.md)、[アルゴリズムと安全条件](algorithm.md)、[先行資料と請求項案](novelty-analysis.md)、[実測と限界](results.md)、[日本語草稿](paper-draft.md)。

## 再現

Python3.9、Node24.15.0/V8 13.6、WABT1.0.42を使用。全て新規小容量のmemoryと作業領域のファイルだけを使う。ルートから未使用出力先を指定する。

```powershell
python research/waiter-identity/probe.py results/waiter-identity/repro
node research/waiter-identity/boundary-audit.cjs results/waiter-identity/probe-v3/sources/partition.cjs results/waiter-identity/repro/pair.wasm results/waiter-identity/repro-boundary
python research/waiter-identity/bench.py results/waiter-identity/repro-performance
node research/waiter-identity/interference.cjs results/waiter-identity/repro-interference
python research/waiter-identity/concurrent.py results/waiter-identity/repro-concurrent
python research/waiter-identity/footprint-audit.py results/waiter-identity/repro-footprint
python research/waiter-identity/setup-spidermonkey.py
python research/waiter-identity/cross-engine.py results/waiter-identity/repro/pair.wasm results/waiter-identity/repro-cross
python research/waiter-identity/cross-engine.py results/waiter-identity/repro/pair.wasm results/waiter-identity/repro-ordinal-cross --implementation partition-ordinal.cjs
python research/waiter-identity/ordinal-order-audit.py results/waiter-identity/repro-ordinal-order
python research/waiter-identity/ordinal-bench.py results/waiter-identity/repro-ordinal-performance
```

boundary-auditの第一引数は保存した旧版。旧版の弱点と修正版を比較するために必要である。性能と正当性を同時実行しない。

APIは`await partition([memoryA,memoryB,...])`。`labels`と同じ呼出しで捕捉した`memories`を返す。後段はこの配列へ結び付ける。元の入力配列を後から読み直さない。`byteOffset`は既定0、同じbyte offsetを全memoryに使う。非shared、零長、範囲外は拒否。失敗・deadlineは非aliasではなく判定不能。

この試作は共有実体の同定であり、メモリオブジェクトの全semanticsの等価性、任意の敵対的workerとの隔離、既存サービスへの脆弱性の実証ではない。

追加反例5試行では、外部waiterと別memoryへの通知により、件数が一致したまま独立memoryを誤結合した。排他前提を内部で確かめられる方式ではない。限定試作として保存し、主特許候補へは採用しない。

並行版`partition-concurrent.cjs`では登録競合に有限再試行を加えた。同じcellの更新中は成功が少なく、書込み範囲から選んだ別cellでは900/900成功した。checkerはguestの同期操作不使用だけを局所確認し、全actorの管理はhostに依存する。[実測](results.md)。元の静止版と並行版の性能結果を混同しない。

SpiderMonkey150.0.1でも共通290条件等が一致した。setupはMozilla公式の約18MB archiveを`.tools/`へ取得し、公式checksumを照合する。shell adapterのtimer制約があるため、browserでの完全な検証と扱わない。

同一agentのPromise解決順と通知件数で一括復元するordinal版も、両engineの共通条件を通過した。n=k=64で単一timer・群別await版0.161705msに対し0.054230ms。k=1では遅く、registryにも劣る。順序前提を人工的に破る小模型で件数・代表検査を通る誤分割を確認した。条件付きの性能改良として保存し、特許新規性の確立とは扱わない。
