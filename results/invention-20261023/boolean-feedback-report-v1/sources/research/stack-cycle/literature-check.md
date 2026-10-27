# 今回の文献照合の範囲

確認日2026-10-18。検索語は`WebAssembly control flow flattening multi value stack parameters obfuscation`、`WASMixer stack local splitting`、`WebAssembly obfuscation block parameters`等。検索でexactな規則が見つからなかったことを先行研究不存在の証明にしない。

|一次資料|区分・読んだ範囲|今回の含意|
|---|---|---|
|Shangtong Cao, Ningyu He, Yao Guo, Haoyu Wang, *WASMixer: Binary Obfuscation for WebAssembly*, 2023, arXiv:2308.03123v1, [DOI](https://doi.org/10.48550/arXiv.2308.03123)|参照版はpreprint。要旨・書誌、本文§4.2.1 Algorithm 2/3と説明を再確認|分割時のstack保存・復元が最近接。著者実装との同条件比較や論文全体の評価結果の再現はしていない|
|WebAssembly community, *Design Rationale*, [資料](https://github.com/WebAssembly/design/blob/main/Rationale.md)|設計資料。Control Flow Instructions with Valuesを確認|分岐による値受渡しがlocal.get/setを減らすこと、SSA phiとの関係は既知|
|WebAssembly community, *Multi-value Extension*, [資料](https://github.com/WebAssembly/spec/blob/main/proposals/multi-value/Overview.md)|提案仕様。Introduction/Motivationとblock・loopの例を確認|複数のblock/loop引数は標準の構成要素。機能使用自体を発明と呼ばない|
|Binaryen community, version_133, [src/ir/effects.h](https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/ir/effects.h)|実装一次資料。trap effectの注釈、lines 82–103|trap理由同士の差は区別せず、他の観測可能な副作用を跨がない並替えを認める。今回の52件を調査するために確認|
|W3C, *WebAssembly JavaScript Interface*, [Exported Functions](https://www.w3.org/TR/wasm-js-api-2/#exported-functions)|規格。errorからRuntimeErrorへの写像を確認|trapの有無と実装固有のエラーmessageを区別する。message一致までの契約を保証しない|

比較論文としてWASMixerを扱うが、今回の実験対照はその論文の一部に対応するlocal spill dispatcherの自作実装である。WASMixerの命令置換・データ保護等をすべて再現したものではない。既存論文の定量結果を自分の測定値と混ぜない。

今回の最大のReject理由は、標準機能による既知のサイズ削減と既知の分割DPを組み合わせた限定最適化に留まり、解析費用対実行費用の改善も示せないことである。原理が既知という理由だけであらゆる構成差を否定するのではなく、本構成の同条件測定が追加の保護効果を支持しない点も併せて判断した。

WAMO等の本文未取得という既存の調査限界は残る。読めていない2026年論文との技術的同一性や差分を推測で補完しない。今回は新規性を肯定しないため、未確認文献を除外して「初めて」と主張することはない。
