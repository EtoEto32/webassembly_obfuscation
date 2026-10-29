# 接続グラフへの変換と頂点消去：実装と反証

評価の訂正（2026-10-18）：[解析費用の追試](cost-reassessment.md)を追加した。全件復元できたことだけを棄却理由にしない。既存結果には解析時間の増加があり、別の適応的解析によってその増加が縮まることも測定した。新しい難読化方式の確立には未到達だが、「解析費用の増加がない」という結論にはしない。以下の初回評価は、この追補と合わせて読む。

2026-10-18。**この試作は不採用。新規で有効な難読化方式の確立には至っていない。** 実Wasmを変換・実行し、方式を知る復元器、最適化、アブレーション、別エンジン、費用、一括再現まで検査した。

前の状態鍵案は成立条件の段階で棄却した。今回は別の表現として、演算をグラフの接続判定へ移し、元の演算境界を除去する仮説を実装した。単なる名称変更で別案としたものではないが、接続表現・頂点消去は既知であり、独立した新原理として候補数へ加算しない。

## アルゴリズムと先行研究との差

[実行前の仮説と比較条件](plan.md)、[変換器](prototype.py)。入力は1個のexport関数を持つ純粋なi32式のバイナリ。各bitについてANDを直列接続、ORを並列接続へ写す。XORと否定もBoolean式として展開する。辺はi32 maskを持ち、32bit分の接続判定を同時に実行する。

```text
validate and parse the restricted input Wasm
G := two-terminal switching network of the formula
S := internal vertices introduced at composition boundaries
choose a seeded order of S
for each selected k:
    for each pair i,j of neighbors of k:
        edge[i,j] := edge[i,j] OR (edge[i,k] AND edge[k,j])
    remove k
emit public label DAG and graph data in a private Wasm memory
emit a mask evaluator and V-1 bidirectional propagation sweeps
return the mask of vertices reachable at the output terminal
```

残す端点間の接続は、kを通る経路を隣接頂点間の辺へ置換して保たれる。各bitは独立しており、OR/ANDによる到達集合は単調に増える。V−1回の全辺走査は全単純経路を含めるのに十分で、in-place更新による早い伝播は余分な到達を生まない。

最近接資料はMokhovの *Algebra of switching networks*（2015）。[書誌・URL・実際に確認した範囲](plan.md)を参照。この試作で検査した差は、演算境界を優先して除く選択を難読化へ使うことの効用。既知の代数、インタプリタ化、Wasmへの実装だけを新規性の根拠にしない。Wasm固有性は弱く、private memoryと明確な固定幅演算を使う実装上の利点に限る。

## 入力範囲と意味の制約

- 1～128個のi32引数、i32返り値、1個のexport。local.get、AND/OR/XOR、0/−1定数からなる単一式。
- memory、global、import、call、複数関数、trapし得る命令、浮動小数点、一般の定数、ローカル変数の代入を入力として受け付けない。
- 変換前グラフ1,024頂点、ラベル/辺各100,000を上限とする。展開が大きい式には適さない。
- 出力は内部memoryを1個使い、公開exportは入力と同じ関数1個だけ。今回の全例は64 KiB。十分な実行資源を前提とし、追加メモリによる資源不足まで元と同じとは保証しない。
- 元の対象は全域の純粋演算なので、観測するメモリ副作用や元のtrapはない。これを副作用・trapを含む一般Wasmの同値性へ拡張しない。
- 入力の検証・解析を行うCLIであり、ソースジェネレータだけをWasm変換器と呼んでいるわけではない。ただし対象は上記の狭い式クラスである。

## 攻撃モデルと評価課題

解析者は配布バイナリと方式を知る。元の式、seed、頂点対応表、変換レポート、採点用fixtureは[復元関数](recover.py)へ渡さない。攻撃は公開データセグメント内のラベル計算とグラフを読み、BDDによる記号的接続判定から通常のbitwise Wasmを再生成する。

データ内のヘッダはVM形式の一部であり、秘密の対応表ではない。解析器はこのインタプリタ族を知っている。任意コードが同じヘッダを偽装しても同じ意味だと認定できる汎用検証器ではなく、未知のVM形式の発見時間も測っていない。

主課題は元の頂点番号・構文木の復元ではなく、同じ入出力の通常実装への復元。ABI順に固定したBDDの変数順を使う。BDDには100,000ノード、生成する復元コードには20,000ノードの上限を設け、上限・未対応・誤答を成功と区別する。BDDは一般には指数的に増えるため、常に安いという主張はしない。

## 実測

[一次結果](../../results/invention-20261018/connectivity-elimination-v1/summary.json)、[全O3比較表](../../results/invention-20261018/connectivity-elimination-v1/summary.md)。5式×5方式×raw/O2/O3の75条件。方式は元、既知のAND恒等式によるMBA、グラフ化のみ、内部頂点50%消去、80%消去。割合はアブレーションであり、異なる発明とは数えない。

- V8：元/変換後75本と復元後75本の計150条件、138,480呼出しで不一致0。反復呼出しを含む。
- Ch/Maj/mixed12はBoolean入力全組合せを32laneへ詰めた検査も含む。境界値・各引数のone-hot・固定seedのランダム入力を保存。
- WABT interpreter：75条件×4例、300呼出しで不一致0。
- 定数0/−1、単一入力、否定の端点例：12条件、96呼出しで不一致0。範囲外の5種類を明示的に拒否。
- 入力ラベルを全て定数0へ壊した有効Wasmは619入力で不一致となり、検証器が検出した。
- 復元75/75成功。各式の15条件は同じBDDだけでなく、**復元後のWasmバイト列も同一**になった。

有限の実行試験を全入力の形式証明とは呼ばない。BDD一致は対応するBooleanモデルの同値性を支えるが、パーサ・コード生成器・エンジンまで機械的に証明したものではない。

### アブレーションと費用

以下はO3の参考値。実行時間はJSからの呼出し・引数渡しを含む中央値、解析時間は同じ範囲のモデル構築とBDD計算の中央値。

|式|元 ns/call|グラフのみ ns/call|80%消去 ns/call|グラフ解析 ms|80%消去の解析 ms|
|---|---:|---:|---:|---:|---:|
|Ch|70.3|302.3|145.3|0.107|0.067|
|Maj|69.5|494.5|199.2|0.168|0.109|
|mixed12|160.9|591.4|286.7|1.171|0.434|
|parity16|161.7|67,872.7|10,439.1|232.027|71.863|
|blend24|174.2|671.1|383.6|10.935|2.877|

消去により伝播する頂点が減る一方、辺ラベルの計算は増える。例えばparity16のラベル数は33→2,932、O3サイズは3,987→37,364 bytesになった。動的な走査回数は減り、実行は速くなる。しかし今回の記号的解析も速くなり、保護目的の差にはならなかった。

変換時間は15回の単発測定で約56.6～68.3 ms。validation/disassembly/assemblyの外部プロセス起動を含む。線形memoryは元/MBA/復元後が0、グラフ群が64 KiB。75 fresh processのmaxRSSは38,748～40,524 KiBで、JS/V8と測定器を含む値であり、差をWasmのmemory費用と同一視しない。

実行時間は1バイナリごとにfresh processを使い、128回の事前実行後、128呼出し×9回を測定した。解析時間は同一プロセス内の3回。実行順はseed付きshuffle。CPUはi9-11900K、Node v24.15.0/V8 13.6.233.17-node.48。CPU隔離、JIT tierの記録、プロセス単位の反復、信頼区間はなく、微小な倍率差を有意差と主張しない。Pythonの解析時間とV8の実行時間の倍率をそのまま比較しない。

### 保持した失敗と修正

初回復元器はBinaryenが除いた末尾のゼロを「データ不足」と誤認し、最適化後30条件を拒否した。Wasmの初期memoryのゼロ充填をモデル化して75条件すべてを復元できた。初回ログ・ソースを残す。このパーサ不備を保護効果へ数えない。

また、初期の解析時間には通常式だけ追加disassemblyが入っていたため、方式間比較に使わない。[揃えた範囲の再測定](../../results/invention-20261018/connectivity-elimination-v1/analysis-timing.json)で両方のモデル構築とBDD計算を測り直した。時間範囲の修正前後で全75の正規形hashは一致した。

## 判断と限界

最大のReject理由は、既知の接続代数から独立した新規性が未確立で、狙った境界消去が今回の方式既知の復元を難しくしなかったこと。インタプリタとして残ること、命令数が多いこと、元の中間頂点が存在しないことから保護を結論できない。

Ch/Maj/parity16は既知の簡単な関数で、保護成功を示すベンチではない。mixed12/blend24も人工的なbitwise式であり、各bitが独立するためI/Oからの真理値表学習が可能である。n引数の全Boolean入力は最大ceil(2^n/32)回のpacked問い合わせで列挙できる。この上界は計算による説明で、全24入力の学習を今回実行した記録ではない。大規模なアプリケーションの保護へ一般化しない。

NotDec、StackSight、WASMixer、SaMBAの本体を今回実行した比較ではない。通常のbitwise式と基本MBAは対照であり、既存の最先端方式を代表しない。任意のグラフ表現やWasm難読化が保護不能という証明でもない。

以上からこの試作のseed・消去率・頂点数を増やして延命しない。新しい有効なアルゴリズムを求める研究目標は未完了のまま継続する。

## 再現

Python 3.9標準ライブラリ、Node 24.15.0、WABT 1.0.42、Binaryen 133。既存`.tools`の実行ファイルを使用する。別の配置なら`WASM_TOOLS_ROOT`を設定し、その下に`wabt-1.0.42/bin`と`binaryen-version_133/bin`を置く。外部サービス・課金・追加npm packageは不要。

リポジトリルートから新しい出力先を指定する。

```powershell
.\research\connectivity-elimination\reproduce.ps1 -OutputDirectory results/invention-20261018/connectivity-elimination-fresh
```

個別のバイナリ変換・方式既知の復元も可能。

```powershell
python research/connectivity-elimination/prototype.py input.wasm transformed.wasm --fraction 0.8
python research/connectivity-elimination/recover.py transformed.wasm recovered.wasm
```

一括再現を[別出力先](../../results/invention-20261018/connectivity-elimination-replay-v1/summary.json)で完走済み。同じ入力の再検査であり、件数を独立な入力として二重計上しない。初回の983ファイルと再現の801ファイルの数の差は、初回の失敗・修正履歴を保持したため。全入力、Wasm/WAT、復元結果、個別測定、ソースsnapshot、hash inventoryを保存している。

[再現監査](../../results/invention-20261018/connectivity-elimination-audit.json)で両inventoryを照合し、入力側75バイナリ・復元後75バイナリ・テスト入力の完全一致を確認した。[監査スクリプト](audit.py)は保存物の同一性を検査するもので、新規性や全Wasmの正しさを認定するものではない。
