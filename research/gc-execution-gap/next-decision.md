# 次方向の先行性と選定条件

2026-10-27。R/Sの入力構築は、単純対照との比較と今回の到達性測定を経ても独自効用を示せていない。元の修士研究目標を「計数器が動いた」で達成扱いにしない。

## 実際に追加確認した一次資料

- **Binaryen version_133**の[生成器](https://github.com/WebAssembly/binaryen/blob/version_133/src/tools/fuzzing/fuzzing.cpp)。`makeTrappingRefUse` は多くの場合nonnull値を使い、既存localの参照を再利用して同じobjectへの読み書きを作る。`makeArrayBoundsCheck` と `makeArrayGet/Set` は動的な長さ検査とfallbackを組み合わせる。したがって「nullとOOBを防ぎ、同じobjectを再利用するGC生成」だけでは差がない。`fuzz_opt.py` の `Two` は複数moduleのlink/optimization比較も既に行う。
- **Fuzzing JavaScript Engines by Fusing JavaScript and WebAssembly (MAD-EYE)**、Jiayi Lin, Changhua Luo, Mingxue Zhang, Lanteng Lin, Penghui Li, Chenxiong Qian、ICSE 2026、DOI [10.1145/3744916.3764551](https://doi.org/10.1145/3744916.3764551)、査読済み。[会議ページ](https://conf.researchr.org/details/icse-2026/icse-2026-research-track/34/Fuzzing-JavaScript-Engines-by-Fusing-JavaScript-and-WebAssembly)と著者公開PDFを照合し、PDFの3〜5ページを描画して§2/3とAlgorithm 1を確認した。imports/exportsのprobe、制約付きsplice、変数・object shapeを使うJS生成が既存。著者PDFは21発見/20確認/18修正、会議abstractは21/18/13と異なるので混ぜない。いずれも著者報告で今回未再現。
- **Execution-Aware Program Reduction for WebAssembly via Record and Replay**、Doehyun Baek, Daniel Lehmann, Ben L. Titzer, Sukyoung Ryu, Michael Pradel、ASE 2025採択と著者が明記する[arXiv v2](https://arxiv.org/html/2506.07834v2)。abstract・構成・問題設定を確認。関数と他部分の相互作用を記録再生するRR-Reduce/Hybrid-Reduceが既存であり、「実行記録でWasmの縮約を速くする」一般案は採用しない。28programの評価は今回未再現。全節精読は未完了。
- **Compiling WebAssembly Concolic Execution with Staging, Continuations, and Snapshots**、Dinghong Zhong, Alexander Y. Bai, Mikail Khan, Guannan Wei、OOPSLA 2026論文の[拡張版](https://arxiv.org/html/2608.18327v2)。abstract・構成・§1の動機を確認。continuation/snapshotにより入口からの再実行を避けるGenWasymが既存。184benchmarkの速度値は著者報告で未再現。GC対応の全範囲は未確認。
- [GC仕様の実装者による型rollingの説明](https://github.com/WebAssembly/gc/discussions/578)、[現行仕様の型表現規則](https://webassembly.github.io/spec/core/valid/conventions.html)。module-relative、rec-group-relative、canonicalの区別は既知の要件。単に正しい型canonicalizationを実装すること自体を新発明としない。旧Overviewに残るequi-recursiveな説明を現行iso-recursive仕様と混同しない。

## 原理の異なる次方向の比較（いずれも新規性未確立）

|方向|狙う不足と仕組み|最大の反証・既知技術|次の採用条件|
|---|---|---|---|
|実行可能なGC操作列の生成|値構築に加え、必要なnonnull/length条件を満たす操作列を生成し、成功したsiteを増やす|Binaryenの既存guard生成、型/構造保存mutation、通常の制約充足で説明可能|既存guard方式が到達できない具体例と同一時間での改善が必要。現時点では主案にしない|
|型関係を保つmodule群による文脈検査|同値/非同値の型関係行列を固定し、独立moduleの配置・type index・compile順序を変える。link結果とref.test/castの関係が文脈から独立か確認|仕様テスト、Binaryenの型生成器/Two、MAD-EYEの境界検査、一般metamorphic testingで代替可能かもしれない|既存の単純なpairwise検査と比べ、module文脈を構成する規則に残る具体的差分を先に調べる|
|GC結果を区別する観測器|opaque参照の戻り値だけでなく、有限のfield/alias観測を比較する|通常のgraph serialization、既存loggingやchecksum、K案の状態観測に近い。観測器が新たに状態を可視にすると最適化条件が変わる|最適化で正当に変わるprivate表現を誤報せず、現行oracleが見逃す観測可能な差を検出できるかが必要|

次は2番目の型文脈検査を**先行性を反証するための調査候補**として優先する。R/Sのheap初期化とは検査対象・原理が違うが、まだ採用済みの新アルゴリズムではない。正式な設計・実装前に、Binaryenのtype fuzzingと公式recursion/linkingテストが同じ文脈操作を既に行っていないかを読む。差がなければ、同じ既知手法を別名で実装する作業に進まない。

今回のgoal turnは、512条件の実生成器比較、1,764主呼出し、3engine校正、1,004binary再生成、近接文献の追加確認によるprogress。主テーマの確立は未達でactive。最新利用枠は18%使用・82%残り。20%停止目安には未到達。無関係な既存論文本文と根元READMEを保持した。
