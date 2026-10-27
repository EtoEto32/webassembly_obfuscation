# 外部heap観測の実測

2026-10-27。生データは[probe-v2](../../results/heap-observer/probe-v2/report.json)、[generated-v1](../../results/heap-observer/generated-v1/report.json)、[bounds-v1](../../results/heap-observer/bounds-v1/report.json)、[performance-v2](../../results/heap-observer/performance-v2/report.json)。主実行はNode24.15.0・SpiderMonkey150.0.1、最適化器Binaryen133。対象を新しい不具合のあるprogramと偽って扱わない。

## 小例・反例

9系列（scalar/packed/array/deep/alias/cycle/recgroup/subtype/NaN正対照）×2変種×O0/O3-open/O3-closedで54 target binary、元型から9 helperを作った。2 engineで108 process。全て正常観測、open-worldの36比較はsnapshot一致。8系列の意図的な内容差について、O0/O3-open ×2 engineの32比較をsnapshotは全て識別した。境界identityは全32比較を識別できなかった。NaN payloadだけを変えた正対照4比較は同じsnapshotになった。これは用意した差への検出であり、自然発生したcompiler bugの検出ではない。

closed-worldの36比較中32は元helperから見たsnapshotが変わった。多くは元typeへのtestが一致しなくなった例である。Binaryenが明示的に仮定する「外から参照の内容を検査しない」という条件に反するので、この32件を誤コンパイルとして報告しない。array系列の4件はこの設定でも同じだった。closed-worldで必ず内容が変わるとは言わない。

独立した期待値18条件（9系列×2 engine）ではi64最小値、packedの255/65535、負の0のbit、循環の自己参照、共有child、subtype追加fieldを確認した。追加のnull/空array/末尾要素差/深いchild差では16 binary・64 process・32比較が期待どおりだった。要素上限8ならarrayの63番目の差を見逃し、node上限1ならchild内部の差を見逃す。上限を広げると両方を識別した。観測上限がある以上、全heap同値とは主張しない。

初回probe-v1はRust版差によるbuild不成立の後、実行ファイル不在で停止した部分記録。probe-v2を有効測定とする。生成器接続の最初の試行はPython module名衝突で出力directory作成前に停止し、衝突を分離してからgenerated-v1を実行した。これらはengine拒否や解析耐性ではない。

## 実生成器

前段で固定したBinaryen64 seedのO0/O3をそのまま使用した。同じ64 seedを複数段で測っており、独立sample数を水増ししない。64/64でhelper生成成功。128 targetは前段とbyte一致、2 engineで256 process終了、timeout/crashなし。4 seedのstart trapは全条件でinstantiate失敗（計16 process）として別集計した。

O0・Nodeで、46 seedから126 snapshot、190 object recordを得た。31 truncationがあり、全到達heapを読んだわけではない。1 objectはunmatched/opaqueだった。これはseed51のexternref要素の先であり、対象GC typeが一致しなかったものとして保存し、field復元成功に数えない。共有・循環を含むsnapshotは最適化前後128比較、engine間128比較で一致した。追加の自然不具合検出は0。

同じtyped/multi callerだけを使った前段との256比較で、guest呼出しstatusとboundary GC event列は一致した。追加observerが任意の実行へ非干渉という証明ではない。snapshotを取得するのは既存呼出しがすでに渡した値だけで、getterを対象へ追加してその最適化を妨げる方法ではない。

helperのbinary sizeは実生成物で177–2,584 byte（中央値741 byte）、小例で108–179 byte（中央値141 byte）。生成時間はprocess起動・入力検証込み、実生成物の中央値9.854 ms、小例10.032 ms。target binary増分は0。これらの実生成物は汎用fuzzer出力であり、productionアプリの外的妥当性は未評価。

## 費用と単純対照

array長0/8/64/1024、各5方式、各3 fresh Node processの60 process。各processで3 warmup sample、9 measured sample、各sample100 snapshot。下表はprocess内中央値の3 process中央値、ns/snapshot。読み出し後のJSON encodingを含み、module compile・targetのget呼出し・stdout I/Oは含まない。短時間の探索測定であり、性能差の統計的有意性は主張しない。

|array長|境界identityのみ|汎用・上限8|汎用・全要素|手書きloop・上限8|手書きloop・全要素|
|---:|---:|---:|---:|---:|---:|
|0|487|1,370|1,270|828|822|
|8|457|2,151|2,389|925|963|
|64|463|2,310|4,208|1,026|2,942|
|1024|443|2,434|16,548|1,037|10,294|

手書きloopは同じgetterを用い、型を既知のarrayに固定して直接読む強い単純対照。各processで汎用版とJSONが完全一致することを確認した。汎用版が高速・高機能な新しい読出し原理を持つ、とは言えない。自動型処理・共有/循環対応の費用を払っている。境界identityは観測内容自体が少ないため速度だけを比べて優劣判定しない。

N=1024で出力は上限8が158 byte、全要素が3,189 byte。process RSSは約38–44 MBで、snapshotのpeak memoryではない。測定区間のheapUsed差もGCを含む一時使用量の差で、保持量・割当総量ではない。performance-v1の境界対照は単一参照の自明な等価比較だったため、Mapを使う対照と手書きloopを加えたv2を主値とした。v1も保存している。

## 監査と判断

[audit-v1](../../results/heap-observer/audit-v1/report.json)で1,246 manifest entry、256 Wasm binaryのWasmtime検証、73 helperの再生成byte一致、元type section entry列がhelperの先頭へそのまま残る73条件、期待値18条件、拒否5条件、target無変更128条件、raw stdout再読256件、前段との256比較を確認し、不一致0。追加bounds/performanceの監査はcheckpointに記録する。

現段階で支持されるのは、対象無改変・複数標準engine・既知の型構造を使う外部読出しが動き、単純出力比較より多い状態差を小例で観測したこと。既存Two handlerに対する追加検出、独立選定した既知不具合での効用、production GCプログラムの評価は未達。主テーマへの昇格は保留する。
