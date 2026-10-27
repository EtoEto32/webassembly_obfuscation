# 既知の等式WPによる強い対照

2026-10-25。Kの新規性を反証するために、汎用SMTだけでなく、既知の等式解析を用いた独立backendを追加する。

Markus Müller-Olm / Helmut Seidl / Bernhard Steffen, *Interprocedural Herbrand Equalities*, ESOP 2005, pp31–45, DOI10.1007/978-3-540-31987-0_4。[著者公開PDF](https://www.uni-muenster.de/imperia/md/content/informatik/agmueller-olm/publications/esop05-herbrand.pdf)のabstract/Introduction、§2–3の一部、§4の代入・未知値規則とTheorem1を読んだ。特にPDF p7に、等式連言に対する未知値代入を異なる二値へ簡約する規則がある。全証明や著者実装の再現ではない。大学の書誌で査読ESOP会議論文であることを確認した。

## 比較の範囲

Wasmから有限control graphへのloweringは既存parserと区間effectを共有する。その後の等式連言の正規化・代入逆像・任意入力・固定点は、Kのcanonical/pullback/close/transformを呼ばずに別実装する。汎用IRは同時代入、等式要求、共通未知値の代入、その省略可能性だけを持ち、segmentやWasm命令を持たない。

may-writeはcellごとに「何もしない／未知値を同じ左右cellに代入する」の選択として合成する。Kの全maskを無書込みと全上書きの二極へまとめる補題は使わない。条件合成の出力を初期条件だけでなく全control stateで照合する。

これは2005年論文全体の再実装ではなく、その既知の規則をcopy/constantだけの小さいIRへ適用した自作対照である。原論文の再帰手続きや一般のHerbrand項を再現したと記さない。Wasm frontendの独立検証でもない。

初期256契約、may版128契約、長いchain16契約を比較する。性能を測る場合、同じ解析結果・同じ前処理範囲を揃え、条件だけを生成する方法同士を比べる。反例rankの保存を省いたK worklist/sweepと比べ、SMTを読み込まない。未知値処理の違いだけを新発明として数えない。
