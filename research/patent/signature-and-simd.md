# 共通prototype特許とSIMD候補の追加照合

2026-10-18。出願・権利判断ではなく研究上の比較記録。

## 追加した公開特許

**System and method for obfuscation by common function and common function prototype**, [US8645930B2](https://patents.google.com/patent/US8645930B2/en)。掲載発明者：Christopher Arthur Lattner、Tanya Michelle Lattner、Julien Lerouge、Ginger M. Myles、Augustin J. Farrugia、Pierre Betouin。掲載出願人Apple Inc。優先・出願2010-01-04、A1公開2011-07-07、B2公開2014-02-04。掲載metadataは法的な確認を意味しない。

確認範囲は概要、請求項1–17。共通引数・戻り型への変換、関数の統合、再帰、virtual stack、jump等の構成を記載する。請求項1は共通prototypeだけでなく、再帰関数への統合、stack参照の除去、virtual stackへの変換も含む。請求項7は関数選択を示す引数と共通関数への呼出し置換を含む。したがって「型をそろえる全変換が権利範囲」とは解釈しない。ただし単なるsignature統一を新しい着想とは扱えない。

WASMixerの[§4.2.2](https://arxiv.org/html/2308.03123v1)にもcall_indirect化とopaque predicateが記載される。両者の部品をWasmに移すだけの案は具体化せず、別原理の[SIMD非正規mask](../simd-quotient/README.md)を実装した。

## SIMD構成の検討

|構成要素|先行性・比較|現在の判断|
|---|---|---|
|比較結果を幅のある値で表す|min/maxを使うquantitative logicは既知|非正規値であることだけを新規性にしない|
|unsigned差をsat_subで表す|Wasm標準SIMD命令の意味|命令自体は新しくない|
|Boolean cone全体を融合し、最後だけ正規化|今回の具体的生成規則と各gate正規化対照を比較|サイズ・実行費用低下は観測。差分の独立性は未確立|
|条件式の回復を難化|方式既知のQ(x)=[x>0]による抽象評価|全27条件を小さい追加費用で回復。主難読化方式へ採用する効果を確立できず|

比較表は技術的要素を分けるためのもので、請求項案ではない。新規性・進歩性・FTOを判断せず、family・審査経過の全追跡も行っていない。検索日2026-10-18。検索例：`software obfuscation common function prototype`、`SIMD obfuscation comparison masks`、`obfuscation saturating arithmetic`、`Boolean min max robust semantics`。検索で完全一致が見つからないことを特許性の根拠にしない。
