# R: GC参照値の構築可能性と共有した構築証拠

2026-10-26、実験前の仮説。主テーマとして未採用。

Qの失敗は、集合oracleの一般原理が既知で、強い列挙対照に対する追加効果が乏しかったことと、仕様の選択肢を狭めたモデルが誤検出を生んだことだった。Rは結果oracleではなく、非null GC入力を実際に構築する生成器を対象にする。

## 問題と仮説

合法なWasm型でも、その非null値を空のストアから作れるとは限らない。非nullの自己参照を要求するstructは、その最初のinstanceを作れない。一方、その型をelementに持つarrayは `array.new_fixed 0` によって作れる。関数の参照も、返り値の構築可能性とは独立に存在できる。

H1: 型の依存を有限固定点で解き、構築順の証拠を持つことで、深さ制限だけの生成より非null値を多く作れる。
H2: 証拠をtreeではなく局所変数を共有するDAGとして出力すると、重複fieldのある型で、同じ型・同じ対象操作を有限の生成予算内に置ける。
H3: ただし、memo化した通常の構築器にも同じ効果があるなら、新しい一般アルゴリズムの優位性とは認めない。Wasmのテスト生成への具体的適用・実証として残るかを別判定する。

型の空性判定、AND/ORグラフ、固定点、hash-consing、DAG共有はいずれも既知。単にWasmへ移植したことを新原理とは呼ばない。

## 範囲

最初はCore GCのfinal struct/array/function、numeric/vector field、nullable/nonnullable concrete reference。継承・abstract nonnull reference・descriptor・continuation・shared GCは範囲外と明示する。実binaryから型sectionを読む。元moduleの関数や副作用は実行せず、同じ型sectionを持つ独立した生成fixtureを作る。任意moduleの意味保存変換ではない。

入力値のaliasが変わるため、共有DAGとtreeは同値プログラムではない。構築成功と対象操作への到達率を比較し、両者の全意味同値性を主張しない。共有率の偏りは実用fuzzerへ統合するときの重要な制約。

## 事前比較・成功条件

- 深さ/総constructor数を制限する再帰tree生成、memo化再帰生成、worklist+DAGを比較。同一型集合・対象型・予算を使う。
- 生成した.wasmの検証、Node/Wasmtime/SpiderMonkeyの実行で型test・field読出し・array lengthを照合。合法だが空の型は構築不能とし、trapを正常な値生成に数えない。
- 非nullable自己cycle、相互cycle、nullableで切れるcycle、長いchain、重複field、空arrayによる切断、関数型による切断、無関係type indexを含める。
- 独立な小モデル列挙で判定を検査する。数値は独立アプリ数と区別する。
- 時間、binaryサイズ、生成器メモリ、生成数/成功数/拒否/未対応を記録する。
- Binaryen/wasm-smithの実装を読み、実生成物でも課題が存在するか確認する。toyだけで主テーマへ昇格させない。
- 未知の実bugを見つけることは初期実装の必須条件ではない。ただし主テーマ採用には、強い生成baselineとのcoverage/到達率比較、実際のGC型corpus、規則の健全性説明が必要。

## 既存技術の初期照合

Binaryen fuzzing.cppにはnonnullable再帰の限界でnullからref.as_non_nullを作り、実行時trapを許容する説明がある。wasm-smith core.rsには非null自己参照の構築不能性を理由にnullableに限定するTODOがある。これらは問題の先行認識を示す。固定versionと該当関数を取得して確認し、最新全体の未対応を一つのTODOだけから断言しない。

採用最大の障害: 既知のmemo化構築だけで差を説明できること、生成器が既に同等の経路を持つこと、実corpusで非nullの対象が少ないこと。
