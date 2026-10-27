# Rの先行技術と反証

## 2026-10-27追補

wasm-smithについては[本体比較](smith-results.md)を実施済み。以下の旧表の「本体実行比較は未実施」は初回調査時点の状態。公式0.262.0 crateの無改変版とfeature-offの256条件が一致し、小さな空array候補修正による構築成功の増加を確認した。

**Lingming Zhang, Binbin Zhao, Puzhuo Liu, Qinge Xie, Peng Di, Jianhai Chen, Shouling Ji, “Weaver: Fuzzing JavaScript Engines at the JavaScript-WebAssembly Boundary,” arXiv:2603.18789v1, 2026-03-19。** [本文](https://arxiv.org/html/2603.18789v1)、[書誌](https://arxiv.org/abs/2603.18789)。今回確認した版はプレプリント。査読採択先は未確認。Abstract、III-A/B/C、IVの型表現・生成器・module_shape統合部分を読んだ。JS/Wasmの二重型を追跡し、型に合う既存値を入力・importへ接続する。wasm-smithへmodule shapeを渡す構成が先行する。3エンジンでcoverageと新規bug 2件を報告しているが、今回その実験を再現したわけではない。Rの固定path構築を同一に実装しているか、非null再帰型の扱いの全範囲は未確認。「型を保つ入力供給」「module_shape利用」自体をR固有の新規性とする主張は避ける。

alias/循環したheapを指定する次方向は[2026-10-24の早期調査](../security-screen-20261024.md)にもKorat・generalized symbolic executionの先行性が記録されている。2026-10-27の追加検索は途中で検索サービスが401 token_revokedを返し、代替の接続検索も同じ認証エラーだった。新たな本文を読めたとは扱わない。調査範囲の不足を新規性の根拠にしない。

## 初回調査

確認日2026-10-26。公開ソースの取得先・hash・失敗は `results/gc-witness/priors-v1..v3/manifest.json`。v1はDNS失敗。v2のcode.rsは404で未読。後に正しいcode_builder.rsを固定版から取得した。

|一次資料|区分・読んだ範囲|Rとの関係|
|---|---|---|
|William F. Dowling, Jean H. Gallier, **Linear-Time Algorithms for Testing the Satisfiability of Propositional Horn Formulae**, Journal of Logic Programming 1(3), 267–284, 1984。[著者所属大学のPDF](https://www.seas.upenn.edu/~cis5110/Dowling-Gallier-Horn-sat.pdf)、DOI 10.1016/0743-1066(84)90014-1|査読論文。今回は表紙・抄録の検索抽出を確認。本文の証明は未精読|グラフ上の伝播・call-by-needによる線形処理は既知。RのAND依存worklistを新一般アルゴリズムとしない|
|WebAssembly Core 3仕様。[array.new_fixed等](https://www.w3.org/TR/wasm-core/)|規範仕様。該当命令・型の規則。論文ではない|長さ0のarrayにelement値は不要。関数参照の存在と関数の正常終了は別。これ自体は新発見ではない|
|Binaryen version_133 [heap-types.cpp](https://github.com/WebAssembly/binaryen/blob/version_133/src/tools/fuzzing/heap-types.cpp)|公開実装。Inhabitator、breakNonNullableCycles、getInhabitableと再帰判定（主に912–946、1126–1183、1343–1426行）を読んだ|構築不能なcycleの識別、nullableへの変更、function型での切断は既存。arrayのelementにも必須の非null依存をたどるため、長さ0で構築できる型まで落とす余地がある|
|Binaryen version_133 [fuzzing.cpp](https://github.com/WebAssembly/binaryen/blob/version_133/src/tools/fuzzing/fuzzing.cpp)|公開実装。setupHeapTypes、makeBasicRef、makeCompoundRef、makeRefFuncConstの関係部分を読んだ|既存typeのfilter、新規typeの修復、深さ上限でnullをcastする経路がある。abstract arrayについては空array構築も既に使われる。Rは空array命令そのものを発明したわけではない|
|Thomas Livelyほか、[PR #9282](https://github.com/WebAssembly/binaryen/pull/9282)、2026-10-20作成・10-22merge（UTC）|公開修正、査読論文ではない。metadata、5 patchの変更箇所と主差分を確認|初期/imported module由来の構築不能型を記録して再帰生成を止める。Rがこの既知問題を初めて発見したとはしない。取得したmainのheap-typesにもarray要素依存の規則が残る。main snapshotのcommit照会値はf1f3a483efe97639d3412a0565a2c3278a706e78だが、別リクエストのfileと同一commitだったことは未検証|
|wasm-tools v1.262.0 [wasm-smith/core.rs](https://github.com/bytecodealliance/wasm-tools/blob/v1.262.0/crates/wasm-smith/src/core.rs) と [code_builder.rs](https://github.com/bytecodealliance/wasm-tools/blob/v1.262.0/crates/wasm-smith/src/core/code_builder.rs)|公開実装。非null型の生成に関するTODOとarray_new_fixed_valid/array_new_fixed（6147–6202行）を読んだ|空arrayを生成する命令は実装済み。ただしこの命令の候補判定はelement型の値がstack上にあることを要求している。長さ0ならoperandが不要な点と差がある。全ての別生成経路を調査したわけではなく「wasm-smith全体で作れない」とは断言しない。本体実行比較は未実施|

## 新規性の厳格判定

独立した新しい固定点法、型空性理論、DAG生成法は得ていない。memo化DFS対照は同じ325成功条件で、出力binaryも325組全一致した。

残る研究仮説は「元のGC型を保持したまま、constructorのzero-operand経路と対象アクセスの要求を分け、既存生成器が薄く扱う非null参照の実行を増やす」こと。現状では小規模な生成器改善にとどまる可能性が高く、単独で修士主テーマと認める根拠は不足。実装の機能差があることと、論文の新規性が十分なことは分ける。

最大の反証は、既存生成器に空array候補を足すだけで同じcoverageになること。次段階ではこの簡単な修正を強い比較対象とし、R全体との差が残るか調べる。未知bug数だけで優位性を判断せず、成功した対象操作、型/alias状態の被覆、生成時間、同じseed/予算での分布を測る。

今回同時に調べた他方向: [Bentoの著者project page](https://syssec.informatik.uni-due.de/en/research/research-projects/webassembly-security)は多重memoryによるstack/heap/global分離を既に扱う（Oussama Draissi, Lucas Davi, WWW 2026、abstractのみ読了）。単純なmulti-memory分割を別原理の新案とは数えなかった。資源制限も[YuほかUSENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/yu-zhaofeng)のabstractで既存課題を確認しただけで、新方式として実装していない。
