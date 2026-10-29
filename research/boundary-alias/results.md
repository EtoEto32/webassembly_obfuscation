# 実測・訂正・採否

2026-10-27。保護を解除不能にする研究ではなく、Wasm実装を検証するoracleの試作。新規bugの発見、実プログラム全体の同値性証明、独立した新アルゴリズムの確立は主張しない。

## 校正と実最適化

struct/arrayの2種×7系列（fresh、交互共有、既存入力、callback、global更新、log後trap、null混在）×base/fault/privateの3変種を作成し、未変換/O2/O3を実行した。**42 source module、126 binary、2 engineで2,268呼出し**。このうち252回は入力用seed objectの生成で、stepは2,016回。Wasmtimeによる検証は126/126成功。

|比較（各engine）|件数|単一値の表示|参照番号列|単純な参照列探索|
|---|---:|---:|---:|---:|
|意図的な共有関係の差|42|0検出|42検出|42検出|
|正常側の比較|84|差なし|差なし|差なし|

faultの42比較は14種類の差×3最適化levelであり、42独立bugではない。正常84には14個の未変換base自己比較が含まれ、非自明な正常比較は70/engine。private変種では境界へ出ないallocationを増やしても同じ番号列になった。これはあらゆる内部表現変更に誤報しないことの証明ではない。

binaryサイズは未変換142–187 B（中央値157 B）、O2/O3は63–130 B（中央値87.5 B）。生成時間中央値1.158 ms、最適化process時間中央値O2 14.926 ms/O3 15.067 ms。logger追加による対象binaryの増分は0 B。実生成器版の分類helperは別module51 B。

生データ：[probe-v2/report.json](../../results/boundary-alias/probe-v2/report.json)、[Node](../../results/boundary-alias/probe-v2/node.json)、[SpiderMonkey](../../results/boundary-alias/probe-v2/spidermonkey.json)。

## 実Binaryen生成器

64固定seedから64 moduleを生成し、各未変換/O3×2engineの**256 fresh process**を完了した。128 binaryは全てWasmtimeで検証を通る。ただしprocessが正常終了してもguestが正常実行できたとは限らない。

- 4 seed（14,48,55,63）はstartでtrapし、instantiation失敗。4条件ずつの16件を分離した。
- 残る60 seedのうち、既存表示関数の引数としてGC参照を観測したのは40 seed（全64中40）。Node未変換で計106event。
- 同じ参照が2回以上現れたのは2 seed（17,21）。共有を持つ実例は存在したが、この分布では少ない。
- O0/O3の参照列は各engine64組、計128組で一致。Node/SpiderMonkey間も128条件で一致。
- guest/harnessが捕捉した診断はRuntimeError 324、TypeError 96、RangeError 8、instantiation失敗16。回数は256process全体のログ行数。TypeErrorには既存shellが全引数へnullを渡すためi64への変換に失敗する例、RangeErrorにはtable索引の範囲外が含まれる。これらを新しいengine bugと数えない。

原文のstdoutには**28組の差**があった。24組はnull/cast trapがunreachableへ変わる診断文、4組はstart失敗のstack trace位置。元ログ・全差分を保存し、RuntimeErrorの種類とstack位置を分ける比較で残差は0だった。「ログが全て一致した」とは書かない。仕様で固定されていない診断文の一致を意味保存条件にはしない。

対象の呼出し列は元shellのままで、multi-value結果のJS Array内部を辿らず、null入力で失敗するexportも補修していない。したがって、40/64はアプリ全体のGC coverageではなく、**このharnessの表示箇所での観測率**。

生データ：[binaryen-v2/report.json](../../results/boundary-alias/binaryen-v2/report.json)、[guest別診断](../../results/boundary-alias/audit-v2/guest-outcomes.json)、[原文差の分類](../../results/boundary-alias/triage-v1/report.json)。

## 計測ミスと訂正

`probe-v1` は `--all-features` により最適化器がcustom descriptor用のexact typeを出力し、Wasmtimeの標準設定が拒否した。対象feature集合を明示したv2でやり直した。拒否を意味不一致として数えていない。

実生成器 `binaryen-v1` はprototypeがnullという条件でGC objectを識別したため、表示の再帰処理で `Object.prototype` も数えていた。**46/64、再登場4/64というv1の数値は無効**。v2では別Wasm helperの `any.convert_extern` と `ref.test struct/array` で分類し、11入力×2engineの校正に通った。frozen null-prototype JS objectも負例に含む。v1/v2の128 target binaryは全てbyte一致し、変更は測定側に限定されている。

## 費用

実GC objectをあらかじめ作り、64/256/1,024/4,096 event、1個共有/8個巡回/全freshを3方式で符号化した。36条件×3 fresh Node process=108process、各3 warmup・9測定。これは**hostでの符号化単体**の測定で、実harnessの分類helper・既存表示との併用・stdout I/O・Wasm実行を含めない。

4,096 eventでのprocess中央値の中央値（ns/event）：

|列|既存表示|WeakMap番号|単純探索|
|---|---:|---:|---:|
|1個共有|82.06|57.23|53.30|
|8個巡回|76.39|61.55|56.27|
|全fresh|80.83|75.83|441.19|

全freshでWeakMapが速いのは既知のhash lookupの利点。少数の参照なら単純探索が速く、新発明の性能効果ではない。表示文字列と番号の仕事量も異なるため「新oracleが既存fuzzerを高速化した」と解釈しない。

同条件の全freshのheapUsed増分中央値は表示548,368 B、WeakMap538,664 B、単純探索379,328 B。process最大RSSは約41–42 MiB。JS heapのsnapshot差とprocess全体のhigh-water値であり、正確なGC object占有量やoracle単独の最大live memoryではない。明示GC・JIT・測定順の影響が残る。

生データ：[36条件](../../results/boundary-alias/performance-v1/summary.json)。分布は各条件のmin/max process中央値と9回の生値を保存した。

## 判断

単一値表示から失われる共有情報を追加できるという仮説は支持された。一方、核の番号付けは既知で、強い単純対照と検出能力は同じ。実生成器で自然な不具合を追加発見したわけでもない。**修士研究の主アルゴリズムとしては未確立。** 既存手法の小修正としての価値と、独立した研究貢献の大きさを混同しない。

次は「番号付けをさらに複雑にする」改良を避け、入力型を正しく扱う単純callerとmulti-value観測を対照に置く。そのうえで、共有関係を実際に観測するcall sequence選択に新しい問題設定・アルゴリズム差・実証可能な利益があるか、stateful API testing/active automata learningとの先行性を調べる。単なる既知部品の接続しか残らなければ、新方式として採用しない。

監査：[audit-v2](../../results/boundary-alias/audit-v2/report.json)。9manifestの1,929file hash、126binary再生成、36時間中央値、22分類校正に不一致0。上記28原文差は不一致を隠さず別項目で保存した。主目標は未達でgoal active。利用枠は20%使用・80%残りであり、指定の残り20%には未到達。
