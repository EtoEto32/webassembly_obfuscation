# 先行性と読み取った範囲

2026-10-23。原理の独立性を反証する目的で調査した。以下は新規性不存在の網羅的証明、特許性、FTOの法的判断ではない。

|資料|区別・確認範囲|今回との関係|
|---|---|---|
|Peter Hawkins, Alex Aiken, Kathleen Fisher, Martin Rinard, Mooly Sagiv, **Data Representation Synthesis**, PLDI2011, pp.38–49, [DOI](https://doi.org/10.1145/1993498.1993504)、[著者PDF](https://theory.stanford.edu/~hawkinsp/papers/pldi2011synthesis.pdf)|査読会議論文。今回は要旨・導入・§4.1–4.2を確認。全評価の独立再現なし|関係の仕様から具象データ表現と操作を合成する一般構想は既知。本試作の有限環の消去条件を同論文の既出公式と確認したわけではない。|
|Thomas Wahl, Alastair Donaldson, **Replication and Abstraction: Symmetry in Automated Formal Verification**, Symmetry2(2),799–847,2010, [DOI](https://doi.org/10.3390/sym2020799)、[著者PDF](https://www.doc.ic.ac.uk/~afd/papers/2010/Symmetry.pdf)|査読誌のサーベイ。要旨・導入・§5.4の冒頭説明を確認。他の節の全定理を読了したとはしない|状態の対称性による商と代表状態による実行は既存枠組み。検証のための縮約とIP保護は目的が違うが、目的変更だけを新しい原理としない。|
|WebAssembly Community Group, **Relaxed SIMD proposal**, [公式Overview](https://github.com/WebAssembly/relaxed-simd/blob/main/proposals/relaxed-simd/Overview.md)、[2026-10-13 Core仕様](https://www.w3.org/TR/2026/CRD-wasm-core-2-20261013/)|仕様資料、査読論文ではない。relaxed laneselectの許容結果の定義を確認|下記の早期除外に使用。命令仕様自体を発明としない。|

追加の特許検索は `patent "obfuscation" "quotient"`、`patent "data obfuscation" "state" "equivalence"`。既存US6668325B1等の一般的な変換に関する検索抜粋を見たが、今回の限定規則との請求項全文対比はしていない。検索で同じ式が出なかったことを新規性の根拠にはしない。Slicing Obfuscationsの著者PDFを取得しようとしたが直接取得不可で、今回の内容判断に使わない。

本試作の技術的な対象は、更新可能なWasm状態の共通加算について、倍率kから失ってよい精度dを計算する規則と、その全入力操作列に対する成立条件である。読み取り専用の[旧試作](../memory-quotient/README.md)との差は更新の閉性と公開更新を使った回復にある。一般原理は商状態・対称性・合同算術で説明でき、独立した有力な特許の核としては採用しない。

## 先に除外したrelaxed laneselect案

byte a,b,mについて、B=bitselect(a,b,m)、L=MSB(m)?a:b とする。B=L は `(a xor b) & (m xor signmask(m)) = 0` と同値。canonical mask以外でも、値間の関係で安全にできる。しかし環境差にかかわらず正しいプログラムなら、解析者は仕様が許すbitselect側へ固定できる。関係を解くまで動作を決められないという仮説は成立しない。

model.pyは全256^3=16,777,216組についてこの条件を検査し、2,239,488組で一致、うちcanonical maskの組は131,072だった。この有限モデルをWasm実装や実性能評価と呼ばない。命令の環境差を秘密や解析耐性として使う案の早期除外に限る。
