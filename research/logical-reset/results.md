# Jの実験結果

追加実験：[Wasmtime poolingとの105条件比較](strict-review.md)を実施。小memoryではJが有利だが、4 MiB / 64 KiB処理ではpooling比2.349倍。新しい費用対照と採否は同資料を優先する。

2026-10-24。性能と正当性の限定実験であり、特許性の実証ではない。

## 正当性と負の対照

主記録は[probe-v3](../../results/logical-reset/probe-v3/results.json)。empty/small/medium/declarativeの4構造例を使う。同一fixtureの初期memory/tableサイズ等を変えたもので、4つの独立した実アプリではない。各例は38関数・34関数exportを持つ。

|検査|結果|範囲|
|---|---:|---|
|Node full差分比較|25,704操作比較、不一致0|4 raw + 3 O3、各24 epoch ×153操作|
|Node全方式の比較|30,338比較|fullに加え、不完全3方式の最初の反例までを含む|
|Wasmtime full差分比較|8,148操作比較、不一致0|同じ7条件、各12 epoch ×97操作|
|不完全resetの反例|21件|plain/no-bounds/no-drop ×7条件で各最初の差|
|対応外の有効binary|9例拒否|import/start/state export/型/最大容量等|
|Binaryen parse拒否|5本|declarativeを参照するtable.initを持つ元本＋4変換|

各epochの原本はraw sourceからfresh instanceを作り、変換側だけをreuse/resetした。O3変換の比較でもraw原本を正解側に用いる。数値結果、trapの有無、global、論理memory全byte、table内容を比較する。tableではfixtureの3種類の関数を入力123で区別する。一般関数の外延的同値性検査ではない。観測用memory/table exportは変換後の検査専用binaryにのみ加え、性能測定には入れない。

Nodeの元実行trapは10,294件、反復memory比較量は6,302,597,120 byte。Wasmtimeはtrap 3,335件、1,555,300,352 byte。これらは反復した観測量で、異なる入力の網羅数や強い安全性保証の代用にしない。境界値、seed 20261024の疑似乱数、重複copy、0長/OOB、静的offset overflow、store値評価の副作用、書込み後trap、grow/drop後resetを含む。

`plain`は初期memory/global等を戻しても物理容量とdropを戻せず、epoch 1で差が出た。`no-drop`もepoch 1のinitで差が出る。`no-bounds`では前epochの成長で残る物理領域へのアクセスを通し、epoch 1–5に差が出た。これらは要素の必要性を示す対照で、正しい既存resetの代替ではない。

[cross-v1](../../results/logical-reset/cross-v1/results.json)のWasmtimeは50.0.1。同じCPU上の別engineであり、別アーキテクチャ評価ではない。[boundary-v1](../../results/logical-reset/boundary-v1/results.json)は9本をWABTでvalidateしてから変換側の拒否を検査した。optional tableなし等、受理範囲の全構文はまだテストしていない。

`probe-v1`はBinaryenのdeclarative segment parse拒否で停止した初回記録。`probe-v2`で未対応として分離し、`probe-v3`で比較元をrawへ統一した。v2/v3を独立した成功例として加算しない。rawのdeclarativeはNode/Wasmtimeで実行したが、当該O3条件の成功は主張しない。エンジンのtrapとoptimizerの入力拒否は別集計である。

## 性能

主記録は[performance-v2](../../results/logical-reset/performance-v2/results.json)と[rawログ](../../results/logical-reset/performance-v2/raw.json)。双方のpublic APIを仕事に必要なものへ縮小してからO3に通す[bench-inputs-v1](../../results/logical-reset/bench-inputs-v1/manifest.json)を使う。34exportの初期版performance-v1は参考値とし、より大きなfresh生成費用を主効果に使わない。

環境はWindows、Intel Core i9-11900K 3.50GHz、Node 24.15.0 / V8 13.6.233.17-node.48、`--no-liftoff`。5 fresh process、各2 warmup round＋15計測round。各roundの方式順をseed付きでshuffleする。通常150 request/sample、n=65,536では30 request/sample。事前compiled Moduleからのfresh生成と、同じinstanceのreset＋仕事を比較し、両側で結果検査も計測内に含める。コンパイル時間を含めない。CPU affinityは固定していない。

以下は65,536 byteを処理したrequest当たりの時間。単位μs。時間列はprocess内中央値の5process中央値、比率はprocessごとの比率の中央値と四分位範囲である。

|初期memory|仕事|fresh|full reset|full/fresh median [Q1,Q3]|
|---|---|---:|---:|---|
|1ページ|work-only|49.560|27.410|0.551 [0.494, 0.558]|
|1ページ|grow-drop|58.093|34.107|0.588 [0.583, 0.613]|
|4ページ|work-only|51.300|30.160|0.582 [0.558, 0.588]|
|4ページ|grow-drop|56.383|36.067|0.646 [0.624, 0.649]|

`grow-drop`はmemoryを1ページ・tableを3要素成長し、segment init/drop後に同じbyte loopを実行する。2種類の仕事は共通loopの変種である。n=0/64/4096も保存し、16条件のfull/fresh中央値は0.041–0.646。小さな仕事ほどfresh生成費用が支配的なので、一般アプリの高速化率としない。

同じfull binaryをもう一つのinstanceで測る`fullCopy`とのmedian比は0.985–1.048。work-onlyでは通常の内容復元`plain`でも正しく、full/plainは1.001–1.056。数%の差は校正のばらつきと同程度であり、新しい速度優位と主張しない。grow/dropを含む仕事ではplainは不正なので、性能対照から外す。

## サイズ・変換費用・memory

全34exportを持つsmall rawのbytesはsource 848、full 1,885、plain 985、no-bounds 1,489、no-drop 1,883。O3では順に823/1,627/897/1,138/1,605。APIを縮小した性能用binaryでは、work-onlyのsource/full/plainが102/242/214 byte、grow-dropが285/630/356 byte（両memoryサイズで同じ）。

full変換の経過時間は4例で41.387–44.091 ms。WABT validate/逆変換/再生成のsubprocess時間を含み、Python process起動を含めない。probe-v3の全生成は2.610 s。一回の測定で変換時間の分布は未取得。

性能processの最終RSSは52,768,768–61,112,320 byte、`maxRSS`は72,692–88,216 KiB。複数方式を同一processで測るため方式別memory差は推定できない。logical resetは物理memory/tableを縮小せずhigh-waterを保持する。work-onlyの線形memoryは1/4ページ、grow-dropのreuseは最初の成長後2/5ページを保持するというコード上の容量上限があるが、RSSの内訳として実測した値ではない。passive segment保持も追加費用となる。

## 第三者binaryへの適用範囲

[corpus-screen-v2](../../results/logical-reset/corpus-screen-v2/results.json)で、既に取得済みNoWaSetの220ファイルを読み取り専用で検査した。出典は[NodeWasmStudy](https://github.com/michelledaviest/NodeWasmStudy)、保存commit `53118203addbc9d421deb83289c282dfe7f27173`。各binaryのSHA256を結果へ保存した。実行・書換え・再配布はしていない。

非空219本は全てinterface/memoryの必要条件で対応外、空ファイル1本はvalidator拒否。拒否理由は重複を含み、state export 192、imports 153、bounded/private memory32条件129、memory数44、最大容量38、start 8。最初のdefault validationでは3本拒否だったが、threads有効化とcustom section error無視の追加診断で2本はcoreとして通ることを分離した。元の診断も保存している。scope外をvalidator不正と数えない。

これは全opcodeを解析する互換性試験ではなく、早期除外の検査である。反面、現状の制約が第三者コーパス全体を除外することは実用性の明確な弱点である。今回の成果は自作構造例に対する試作の成立までである。

## 判断

memory内容のみの復元が不十分となる反例と、論理状態を連動させた修正は支持された。全入力の等価性、時間非干渉、物理memory消去、広いアプリへの適用、調整済みWasmtime poolingへの優位、特許新規性・進歩性は支持範囲外。主特許候補への昇格を保留する。

## 一括再現と保存監査

[reproduction-v1](../../results/logical-reset/reproduction-v1/steps.json)で別出力先への生成・Node・Wasmtime・拒否検査・性能測定を再実行し、全5段階が終了コード0だった。主試験70本と性能入力24本の計94binaryが以前の出力とbyte一致した。Node結果JSONも一致し、Wasmtimeの8,148比較も再確認した。同じfixtureの再現を独立した応用例に加算しない。

再現時の65,536byteのfull/fresh中央値は、small work-only 0.517、small grow-drop 0.598、medium work-only 0.584、medium grow-drop 0.634。[初回保存監査](../../results/logical-reset/audit-v1/results.json)は16manifestの796hash entryと31local linkを確認した。無関係なpaper/main.texとpaper/README.mdのhashは作業前と同じだった。
