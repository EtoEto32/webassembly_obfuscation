# 先行研究・一次資料と新規性の反証

2026-10-26調査。主目的は修士研究。特許性の判定ではない。

|資料|区分と実際に読んだ範囲|この候補との差・反証|
|---|---|---|
|Junyoung Park, Yunho Kim, Insu Yun, [RGFuzz: Rule-Guided Fuzzer for WebAssembly Runtimes](https://insuyun.github.io/pubs/2025/park:rgfuzz.pdf), IEEE S&P 2025。実装は[KAIST RGFuzz](https://github.com/kaist-hacking/RGFuzz)|査読論文。Abstract、§4.4、非決定性対処、§8制限を読了。artifactの題名表記は“Fuzzing WebAssembly Runtimes Using Compiler Rules”と異なる。全実験の追試はしていない|NaN正規化やgrow回避を採用。論文時点ではRelaxed SIMD未対応。Qは未変更の命令が返したtupleの許容性を検査する。ただし現在のRGFuzz全コードの対応状況は未監査で、「最新実装でも未対応」とは断定しない|
|Matt Windsor, Alastair F. Donaldson, John Wickerson, [C4: The C Compiler Concurrency Checker](https://johnwickerson.github.io/papers/c4_issta2021.pdf), ISSTA 2021, DOI [10.1145/3460319.3469079](https://doi.org/10.1145/3460319.3469079)|査読会議の4頁tool paper。Abstract、§1、§2冒頭を読了。C4実行は未実施|許容結果集合を求め、意味を精緻化する変換を加えたプログラムを検査する既存手法。非決定的計算を単一出力一致ではなく集合所属で調べる一般原理は新規ではない|
|[WasmRef-Isabelle: A Verified Monadic Interpreter and Industrial Fuzzing Oracle for WebAssembly](https://doi.org/10.1145/3591224), PACMPL 2023|査読論文。今回は書誌・abstractのみ。本文や数値評価未読|形式意味論に基づくWasm fuzzing oracleは既存。Qの小さい未証明モデルを、これに相当する検証済み実装と呼ばない|
|[Wasmtime fuzzing](https://docs.wasmtime.dev/contributing-fuzzing.html)、[deterministic execution](https://docs.wasmtime.dev/examples-deterministic-wasm-execution.html)|公式実装資料。非決定性、NaN、Relaxed SIMD、stack exhaustionの節|回避・正規化・決定設定は既存の実用策。未変更コードの検査範囲を拡大する余地はあるが、回避している事実だけで新規性を証明しない|
|[Binaryen v133 fuzz_opt.py](https://github.com/WebAssembly/binaryen/blob/version_133/scripts/fuzz_opt.py)、[PR8676](https://github.com/WebAssembly/binaryen/pull/8676)|公開実装。取得したsourceのD8比較条件、Two-Opt比較条件とPR差分を確認|Relaxed SIMD生成自体は既に可能。NaN/Relaxed SIMDでbefore/afterや他VM比較を制限する箇所がある。Qはその空白に関係するが、Binaryen全fuzzerより優れる評価はしていない|
|[Core数値意味論](https://webassembly.github.io/spec/core/exec/numerics.html)、[公式relaxed_laneselectテスト](https://github.com/WebAssembly/spec/blob/aa4dcf44b8de3f3f3270ca067422172518ecc341/test/core/relaxed-simd/relaxed_laneselect.wast)|仕様と公式テスト。NaN、共通parameter、swizzle、laneselect規則、当該WAST全体|共通選択は仕様の既知性質。公式テストは二回の同じ命令の結果一致も既に検査する。Qの「複数回の整合性検査」を初出と主張できない|
|[Relaxed SIMD issue125](https://github.com/WebAssembly/relaxed-simd/issues/125)、[PR145](https://github.com/WebAssembly/relaxed-simd/pull/145)|2023年の公開技術議論。本文とbyte選択を認める議論、2023-09-07のmerge表示、修正差分を確認|byte単位とlane単位の食い違いは既知の問題。今回のSpiderMonkey不一致を新発見や新脆弱性として数えない|
|[Binaryen PR9208](https://github.com/WebAssembly/binaryen/pull/9208)|2026-10-05 mergeの公開修正。タイトル・merge・参照issue9207のみ確認。差分は未読|bitselect/laneselectのprecompute修正は既にある。今回の発見ではなく、今後optimizer検査を続ける際の既知対照候補|
|[Dagstuhl: Utilising and Scaling the WebAssembly Semantics](https://drops.dagstuhl.de/storage/04dagstuhl-reports/volume15/issue06/25241/html/DagRep.15.6.51/DagRep.15.6.51.html), §4.8 Testing, 2025|研究会報告。通常の査読研究論文と区別。Testing節のみ|仕様oracle、invariant検査、mutation testing、非決定性の課題は既に議論されている。Qの研究方向自体が未着手とは言えない|

## リポジトリ内の最も近い既存案

[I](../profile-repair/algorithm.md)は共通swizzle profileを持つ部分決定化を実装済み。そのcross-engine.pyは複数出力を一つのprofileで説明できるかも検査する。QはNaNの評価ごとの選択、コピーの同一性、lane選択、O3出力の元プログラムへの所属検査を加えたが、共通profileの発想を別の発明として数え直すことはできない。

## 調査範囲の限界

`relaxed SIMD oracle testing`、`relaxed SIMD profile fuzzing`、`WebAssembly nondeterminism symbolic testing`、`relaxed_laneselect pblendvb`等で探索した。対象は読了資料に限り、存在しないことの証明ではない。保存したsourceは`results/choice-scope/priors-v2`と`priors-v3`にURL・SHA256付きで残す。v1はsandbox内DNS失敗の記録で、読了sourceではない。

主題として残る可能性は「Wasmの非決定的命令を正規化せず検査する実用的なoracleと評価」である。一般SMT・既存集合oracleとの差、実際に増える検査範囲と有効性を示す必要がある。新しいアルゴリズムを確立したとの結論には至っていない。
