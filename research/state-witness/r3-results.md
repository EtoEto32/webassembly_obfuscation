# Wasm-R3-Benchでの適用範囲と実行検査

2026-10-24。[段階ごとの事前計画](r3-plan.md)。実アプリ由来の単独replay binaryへKを適用できるかを検査した。復元器の新たな不具合を発見したという結果ではない。

公開benchmarkの固定commitは`576f499476060026f6c18cf6edd255ffcbeb5e4f`。全27本54,252,889 bytesのうち、取得前に固定した1 file 4 MiB以下・合計32 MiB以下という上限に収まる23本を取得した。boa、commanderkeen、ffmpeg、jscの4本は未取得。各fileはGit blob hashとSHA-256を照合した。原webアプリを再収集・recordしたものではない。

## 静的な適用範囲

[最初の監査](../../results/state-witness/r3-audit-v1/results.json)は2受理・21未対応だった。一部はWABTが表示する`@custom "name"`を閉じたmoduleのprofileが受理しないことが原因だった。別scriptでname sectionだけを除いたところ、[二回目](../../results/state-witness/r3-audit-v2/results.json)は11受理・12資源上限未対応となった。K本体の受理規則は変えていない。

[Wasm仕様](https://webassembly.github.io/spec/core/binary/modules.html#custom-section)ではcustom sectionをcore意味から除外する。前処理はname section以外のbyte列を保存し、元fileも保持した。debug表示やcustomSections APIまで同じとは主張しない。受理11本の前処理後/observer付binaryはWABT validationを通過した。

元codeの命令数は[再現可能なopcode集計](../../results/state-witness/r3-opcodes-v1/results.json)にも保存した。受理11本すべてでdata.drop/elem.dropは0である。

## 実行結果

[Node](../../results/state-witness/r3-run-v1/results.json)では11本それぞれを元/名前除去/observer付で一回ずつ実行し、計33実行のAPI結果とexported memoryをbyte単位で比較した。10本は3条件とも正常終了し、pathfindingは3条件ともtrapした。11本とも条件間で相違はなく、observerの実行前/後の連続二回観測22箇所でも状態差はなかった。

Wasmtimeの[初回](../../results/state-witness/r3-cross-v1/results.json)は500,000,000 fuelで5本正常・6本fuel枯渇だった。いずれも同じengine内の3条件の結果とメモリは一致した。未完走6本だけをfuelなしで[再試行](../../results/state-witness/r3-cross-native-v1/results.json)し、5本正常・pathfindingがtrapとなった。双方ともmemoryは256pages、child process全体45秒の上限を維持し、timeoutは0。fuel枯渇を正常完走に数えない。

[集計](../../results/state-witness/r3-analysis-v1/results.json)では10本の正常終了と1本の同じtrapが両engineで一致した。各条件のメモリSHA-256も11本すべてで一致した。engine内では実byte比較、engine間ではhash比較であり、同じ証拠強度として記述しない。元binaryのprivate globalsと全table identityを直接比較した実験ではない。

pathfindingは追加の[資源診断](../../results/state-witness/r3-limit-v1/pages-1024.json)でも、V8上限256pagesでは216pages、1024pagesでは794pagesまで増えた後に`unreachable`となった。上限を増やしても正常完了は確認できていない。資源制約との関係を疑う材料ではあるが、原因を断定せず、Kの変換が原因の不具合やbenchmark作者の不具合として報告しない。

全実行はwarmupなしの単発である。ログの時間/RSSは診断値であり、速度改善・observer overheadの統計比較には使わない。反復性能は既存の小例実験と区別する。

## 寿命差の研究に使えるか

受理集合には、bullet/mandelbrot/pacalcでそれぞれ49/23/12個のpassive data segmentがあった。しかし元codeを調べるとmemory.initはそれぞれ49/23/12箇所、data.drop/elem.dropはいずれも0だった。残る8本はactive segmentのみ、またはsegmentなしだった。

このため、実アプリ由来のbinaryへobserverを適用して動かせたことは確認できたが、segment寿命変更をまたぐ復元の問題をこのcorpusで自然に評価できたとは言えない。人工的なdropを追加するなら別の変異実験であり、実アプリの欠陥として扱わない。

## 再現

```powershell
python research/state-witness/fetch-r3-review.py .tools/local-r3
python research/state-witness/fetch-r3-review.py .tools/local-r3 --download
python research/state-witness/r3-audit.py .tools/local-r3 results/state-witness/local-r3-raw
python research/state-witness/r3-strip-name.py .tools/local-r3 results/state-witness/local-r3-normalized
python research/state-witness/r3-audit.py results/state-witness/local-r3-normalized results/state-witness/local-r3-audit
python research/state-witness/r3-run.py results/state-witness/local-r3-audit .tools/local-r3 results/state-witness/local-r3-normalized results/state-witness/local-r3-node
python research/state-witness/r3-cross.py results/state-witness/local-r3-audit .tools/local-r3 results/state-witness/local-r3-normalized results/state-witness/local-r3-wasmtime
```

fetcherは指定日以前のcommitを取得し、inventoryを保存する。厳密な同版再現では保存済みinventoryのcommitを使う。`--fuel 0 --names fib,mandelbrot,multiplyDouble,multiplyInt,pathfinding,sandspiel`で今回の未完走分を再試行できる。取得物の外部公開は行っていない。
