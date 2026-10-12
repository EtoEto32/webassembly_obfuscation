# 次候補の重複確認と、状態を持つ変換の検証条件

調査：2026-10-11から12日（JST）。前のゴール継続ではGC dispatcher候補を実装・比較し棄却した。この記録はその次の探索であり、研究目標は変更しない。新しい難読化方式を採用できたという報告ではない。

## 今回の候補比較

共通の解析者モデルは、Wasm全体・公開入出力・公開メモリへのアクセスを持つが、生成器の内部記録を持たない解析者。単に命令や型が未対応のツールを失敗させることを効果としない。

|候補|具体的な変換と狙い|最も近い根拠|判断|
|---|---|---|---|
|E1: 等価式の合成と最適化後の選別|同じ計算の異なる式を生成し、JIT後も異なるものを選び、単純正規化による同一化を避ける|CROW §II.Cは列挙合成とSMT同値判定。WASM-MUTATE §3.3はe-graph抽出、§3.4は機械語・実行trace・状態の比較を含む|この構成だけの提案は採用しない。新しい目的関数を付けるだけでも差分の説明には不足|
|E2: 剰余数による値の分散|整数を複数の剰余へ写し、復号せず演算して値関係の復元を難しくする|Demissieほか2015 §II.B–Cに符号領域内の演算とResidue Number Codingの説明|Wasm/i32への移植だけなら採用しない。wrap・比較・除算の条件は別途必要だが、それを実装するだけで新しい原理とは言えない|
|E3: 複数メモリへの分散配置|論理番地をbankとbank内番地へ分解し、load/storeの対応を隠す|Drape著者草稿 §1.1、§3のalternating split。ch(i)=i mod 2、各bank内i div 2が直接の先行例|単純stripeを新方式として採用しない。Wasmの複数memoryは配置先の違い。trap/境界の保存は必要条件であり、そのまま新規性とはしない|
|E4: 状態・trapを含む領域の変換合成|値だけでなくメモリ更新と停止前の状態を含む関係を制約にし、複数操作をまたぐ書き換えを探索する仮説|CROWの状態を含む同値性、wasm-mutateの副作用を区別するDFG、一般のeffect-aware compiler/synthesisとの比較が必要|未採用。具体的な独自変換規則は未確定。既存のeffect-aware合成と同じなら棄却する。今回は正しさ判定に必要な反例だけ確認|

E1–E3を再実装して測るだけでは目標へ進まないため、本格実装を増やしていない。E4も、先行研究にtrapという検索語が少ないことだけを理由に新規性を認めない。

## 一次資料と確認範囲

- [CROW会議公開本文](https://www.ndss-symposium.org/wp-content/uploads/madweb2021_23004_paper.pdf)：MADWeb 2021。§IIの定義3–5と§II.Cを確認。純粋ブロックの候補列挙・SMT判定がある。著者実装は今回未実行。
- [WASM-MUTATE本文](https://arxiv.org/pdf/2309.07638)：2023プレプリント、2024 Computers & Security。取得したPDFの§3.3、§3.4 Algorithm 2を確認。e-graphだけでなく、JIT機械語・状態・traceを確かめるループが記載される。名前の違う「最適化に残る変換生成」を新方式としない。著者パイプラインは今回未実行。
- [wasm-mutate DFGソース](https://raw.githubusercontent.com/bytecodealliance/wasm-tools/main/crates/wasm-mutate/src/mutators/peephole/dfg.rs)：2026-10-12確認。DFGBuilder.color、new_color、is_subtree_consistent、get_dfgのコメントと関連部分を確認。副作用で色を切り替え、同色の式部分を扱う説明がある。main参照で固定commit未確定、取得内容は論文当時の版と同一とは限らない。全ソース監査・実行はしていない。get_dfgが基本ブロック内であることからツール全体が領域変換をできないとは断定しない。
- [Assessment of Data Obfuscation with Residue Number Coding](https://profs.scienze.univr.it/~ceccato/papers/2015/spro2015.pdf)：2015。§II.B–Cおよび符号領域で対応する演算の説明を確認。値を戻さずに演算すること自体は既存。全演算の境界条件の実装監査は未実施。
- [Generalising the Array Split Obfuscation 著者草稿](https://www.cs.ox.ac.uk/stephen.drape/papers/draft-gensplit.pdf)：刊行情報は[著者業績一覧](https://www.cs.ox.ac.uk/people/stephen.drape/publications.html)でInformation Sciences 177(1), 2007を確認。草稿§1.1、§2の関係、§3のalternating splitを確認。刊行版との全差分は未確認。

WAMO（DOI 10.1145/3774904.3792297）は今回も出版社本文を取得できなかった。タイトル・書誌の索引情報だけで中身を推測しない。新しい2026年のe-graph論文も第三者索引で見つかったが、一次本文未確認で主要判断には使っていない。

検索語：

```text
obfuscation program synthesis superoptimization equality saturation diversified instruction selection wasm
WebAssembly obfuscation memory alias multi memory address encoding
obfuscation instruction scheduling data dependency synthesis egraph
"WAMO" WebAssembly obfuscation 2026
"WAMO" "Yitong" pdf
"WAMO" "WebAssembly" github
"obfuscation" "residue number" encoding
"obfuscation" "predication" traps
"Wasm" "obfuscation" "e-graph"
"obfuscation" "memory" "striping"
"array" "obfuscation" "splitting" memory layout
"CROW" "Code Diversification" pdf
"obfuscation" "trap" "WebAssembly" semantics
"Generalising the Array Split Obfuscation" Drape pdf oxford
"obfuscation" "effect" "synthesis" memory
"obfuscation" "predicated execution"
```

## 実行した反例：同じtrapでも同じ意味とは限らない

`trap-state.cjs`は3つの小さなWasmを生成し、各4入力を別々のインスタンスで試す。外部importなし、1ページの公開memoryを用いる。

- original：memory[0..3]へ7を書き、その後100/dを計算。
- reordered：先に100/dを計算し、その後同じ場所へ7を書く。
- pure_prefix：d XOR 0を先に計算し、originalと同じ順でstore・除算。

dが1、3、0xffffffffならoriginal/reorderedは同じ戻り値とmemoryを持つ。d=0では双方がtrapするが、originalのmemory先頭は7、reorderedは0になる。pure_prefixは4入力とも戻り値またはtrapとmemoryが一致した。

これは自作の不正な並べ替えに対する反例であり、既存ツールのバグや先行研究の不足を発見した実験ではない。既知の意味論上の注意を次候補の検証条件として具体化したもの。GC候補はこのような公開memoryを使わないため、今回の反例を理由に前回の出力検証を無効とは扱わない。

Node/V8版、12実行の結果、ソース・バイナリSHA-256、生成コマンドは`artifacts/trap-state.json`。アセンブラは既存環境のBinaryen 133。再現：

```powershell
node trap-state.cjs C:/path/to/binaryen-version_133/bin
```

## 次の作業と判定条件

1. E4について、effect-aware equality saturation、メモリを扱うsuperoptimization、alias依存の難読化を一次資料で比較する。既存手法と違う変換規則・適用条件を特定できなければ、E4も採用しない。
2. 差分を特定できた候補に対し、観測関係を「returnまたはtrap、外部から観測できるmemory/global、host呼出し列」と定義する。今回はmemoryだけの小反例であり、host呼出しの検証基盤は未実装。
3. 候補の復元対象と解析者情報を固定し、通常版・既存方式・候補・要素除去版で意味保存、解析への効果、コストを比較する。E4の比較実験は未実施。

未完了の中心は、先行研究と異なる有望な変換そのものの確定である。この反例テストや文献整理を新アルゴリズムの成果へ置き換えない。研究目標の達成に向けて作業を継続中。
