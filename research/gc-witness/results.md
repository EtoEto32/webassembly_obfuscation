# Rの結果と採否

**2026-10-27追補:** 最小修正を加えた実wasm-smithとの512試行と、実生成物への2,022入力呼出しを[追加結果](smith-results.md)に保存。以下は2026-10-26時点の初期試験であり、「本体比較が次段階」という記述は追加試験により更新された。主テーマの独自効果は引き続き不足。

2026-10-26。**限定した生成範囲の差は確認した。独立した新アルゴリズム、修士主テーマとして十分な新規性はまだ確立していない。** 調査・実装・実験の進捗であり、研究goalはactive。

## 構築と実行

`results/gc-witness/screen-v1/`。22手設計構成＋64固定seed型graph、計86構成・500型。500型にはfunction型も含む。384の対象型/path taskを3方式で処理した。86個の実アプリという意味ではない。

|方式|生成成功|構築不能/要求不能|node予算超過|
|---|---:|---:|---:|
|再帰tree|315|59|10|
|memo化DFS+DAG|325|59|0|
|worklist+DAG|325|59|0|

予算は2048構築node・深さ64。同じ生成物に対するwasmparser検証、Node 24.15.0、Wasmtime Python 50.0.1、SpiderMonkey 150.0.1の実行を行った。965出力binary、3エンジン計2,895実行でrun=1。最大12段の自己参照arrayアクセスを含む。全入力の証明ではない。

77小型構成では独立した「構築済み型集合の全探索」が2,338状態を訪問し、worklistと判定一致。500型中442型が構築可能で、array要素も必須依存とする保守的規則では406型。この差36は、Binaryen本体のAPIを呼んだ値ではなく、対応範囲について規則をPythonで再現した対照。

## 実Binaryen生成器

`binaryen-v1/`はversion_133の実 `wasm-opt -ttf --initial-fuzz` を4種の初期module×32 seedで実行。全128生成が成功し、別のwasmparser検証も通過。入力は1024byte、同じseedを型条件間で使い、import/exportを保存した。対象typeは同一validator内のcanonical型IDで照合した。

|初期型|出力に対象constructorがあるseed|対象constructor命令総数|observe(null)で構築が成功したseed|
|---|---:|---:|---:|
|nonnull自己参照array|19/32|270|0/32|
|nullable自己参照array|23/32|134|1/32|
|i32 array|19/32|55|2/32|
|nonnull自己参照struct|19/32|349|0/32|

動的値は`binaryen-exec-v1/`。対象constructor/get/setの**後**にcounterを追加し、Wasmtimeで10万fuel・linear memory上限16MiB等の設定で実行した。128中103 returned、25 trap、fuel/compile/instantiate失敗0。target get/setの成功は全条件0。constructor命令の存在を成功した構築やcoverageとして数えると誤る。

これは1つのexportをnull引数で1回呼ぶ限定観測。全entry・nonnull入力・別seedに一般化しない。Rを同じfuzzerに統合した比較でもなく、Rの12段アクセスとこの0件を直接のcoverage倍率にしない。現状のfixture選択だけから実bug発見能力の優位は言えない。

## 反例と計測確認

`controls-v1/`に5つのraw/counter付き実行対を保存。空arrayへのget、構築不能structへのnull cast、構築後trap、結果型を構築できない関数の呼出しはtrap。成功するarray getではconstructor counter=2、access counter=1。他にinvalid default constructor、非対応継承、非対応abstract nonnullの3拒否対照。counterの配置によって失敗した命令を成功に数えていないことを確認した。

Binaryenの診断用WAT出力を手動で1回試した際にfeature flagを省略して入力検証エラーとなった。本体生成・計測は適切なGC等のflagで実行しており、この手動設定エラーはツールの欠陥に数えない。

## 費用

`performance-v1/`。9 fresh process、各3 warmup batch＋9測定batch。6条件×20回/バッチ。数値は**Pythonの計画とWAT生成**であり、Wasm実行時間ではない。

|方式|process中央値の中央値 ms/plan|3 processの中央値範囲|Python追跡peak bytes|
|---|---:|---:|---:|
|tree|0.19603|0.19298–0.19773|107,972|
|memo|0.03723|0.03689–0.03777|152,415|
|worklist|0.03816|0.03812–0.03845|161,976|

worklistはmemoより約2.5%遅く、優位性を示していない。メモリは別passのtracemallocであり、native engineや全processのRSSではない。Python GCや短い測定の影響もある。

出力サイズはtree60–2231B、DAG76–1286B。幅2・長さ9のchainではtree511構築node/2199B、両DAG9node/301B。幅4・長さ21ではtreeが予算超過、両DAG21node/863B。この差は既知の共有で説明できる。各binaryのassembly＋validator subprocess費用はbuild.jsonに保存（単発診断値）。エンジン毎のコンパイル＋1実行時間も保存したが、反復benchmarkではないため速度優位の主値にしない。

## 再現監査

`audit-v1/report.json`: 8manifest・2,564file hash、取得した一次source9件、965binaryの再生成、memo/worklist325組のbyte一致、9process中央値の再計算で不一致0。既存paper/main.texとpaper/README.mdのhashも維持。検査対象はR関連の保存物でありrepo全体ではない。

## 修士主テーマへの判定

現時点では**主テーマ採用は保留**。空arrayによる構築とpath要求の区別は実装できたが、既存の型空性判定・memo化・zero-length命令との技術差は狭い。未知エンジンbugは未発見、実GCアプリcorpusは未評価。

続ける価値が残るのは、元moduleの型identityを保持したテスト入力生成という用途。次の採用条件を固定する。

1. GCコンパイラの実出力から対象型/entryを抽出し、継承を含めた適用率を測る。toyでしか現れない場合は主テーマにしない。
2. 最新の生成器へ統合し、単に空arrayの生成条件を緩めた修正版、memo化のみの版、Rを同じseed・時間・type集合で比較する。
3. 成功したGC操作・型組合せ・alias状態のcoverageに差があるか測る。値生成成功率だけでは不十分。
4. 最小証拠が同じalias配置に偏る問題を解決し、構築不能性と生成予算超過を別々に報告する。
5. 構築規則の健全性と対象外を明文化し、実bugまたは既知bug回帰集合で検出の効用を確かめる。

簡単な空array修正で全効果が説明できるなら、生成器の改善・実装上の知見として保存し、独立した新アルゴリズムを名乗らない。
