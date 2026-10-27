# 先行資料と新規性の限界

2026-10-22確認。実際の読了範囲を以下に限定する。一次資料の提案内容、こちらの解釈、今回の実験を混同しない。

| 資料 | 書誌・確認範囲 | 関係と限界 |
|---|---|---|
| [Validation Algorithm](https://webassembly.github.io/spec/core/appendix/algorithm.html) | WebAssembly Core Specification 3.0、表示日2026-10-13。control frame、unreachable、pop_val、i32.add/drop、blockの記述を確認。公式仕様であり査読論文ではない | stack-polymorphicなpopを使う機構は既存仕様。明示的な不整合型はunreachable後でも拒否される。仕様そのものを新規性に数えない |
| [WebAssembly JavaScript Interface](https://webassembly.github.io/spec/js-api/index.html) | Editor's Draft、表示日2026-10-20。validateのアルゴリズムを確認。公式仕様 | byte列の妥当性をBooleanで返す機構は既存。今回の差分候補はCNFの真偽をこの妥当性へ移す生成規則 |
| *Translingual Obfuscation*, Pei Wang, Shuai Wang, Jiang Ming, Yufei Jiang, Dinghao Wu | IEEE EuroS&P 2016、pp.128–144、査読会議。[著者PDF](https://faculty.ist.psu.edu/wu/papers/to-eurosp16.pdf)の要旨・Introduction・§2.1/2.2を今回確認。[大学書誌](https://pure.psu.edu/en/publications/translingual-obfuscation/)、DOI [10.1109/EuroSP.2016.21](https://doi.org/10.1109/EuroSP.2016.21) | C関数をPrologへ移しunification/backtrackingを用いるBABEL。言語特有の機構を別の計算媒体にする一般的着想は既知。今回全実験を再読・再現しておらず、著者の性能・強度をこちらの対照値とはしない |
| *Independence from obfuscation: A semantic framework for diversity*, Riccardo Pucella, Fred B. Schneider | Journal of Computer Security 18 (2010), pp.701–749、査読誌、DOI 10.3233/JCS-2009-0379。[著者所属大学PDF](https://www.cs.cornell.edu/fbs/publications/IndepFromObfuscation.pdf)の表紙・要旨・導入を確認 | 変換による多様性とtype checkingによる防御を意味論的に比較する。型検査器を条件計算器として呼ぶ同一のアルゴリズムを示す資料と判定したわけではない。検索語にtype checkingがあるだけで同一先行例と扱わない |

Wobfuscatorの[IEEE書誌・要旨](https://ieeexplore.ieee.org/abstract/document/9833626)も再確認した。JavaScript計算の一部をWasmへ移す点が関連するが、今回の評価は正当な条件処理の復元であり、同論文の検出回避タスクは採用しない。本文全体を今回再読したとはしない。

検索語は `WebAssembly obfuscation validation unreachable predicate`、`"obfuscation" "type checker" "predicate"`、`"obfuscation" "program validity" boolean`、`"WebAssembly.validate" obfuscation` 等。Wasmのこのblock生成規則と同一の先行例は今回確認できなかった。ただし文献・公報を網羅した証拠はなく、初出や特許性は主張しない。

技術差分候補は、入力ごとのunreachable/nopの生成により、プログラムの実行結果ではなく妥当性を元のBoolean出力へ対応付けること。既存の計算モデル変更から独立した原理かは未確立。今回の入力族では検証器がclauseごとのORへ容易に要約でき、実装と実測は保護上の優位を支持しなかった。機構上の違いと、有用な新規難読化の実証を分ける。
