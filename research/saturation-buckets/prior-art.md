# 先行技術と確認範囲

調査日2026-10-22。次の対応は技術比較であり、特許の有効性・侵害・取得可否についての判断ではない。

| 資料 | 区分・確認範囲 | 関係 |
|---|---|---|
| WebAssembly Community Group, *WebAssembly 128-bit packed SIMD Extension* | [公式仕様文書](https://github.com/WebAssembly/spec/blob/main/proposals/simd/SIMD.md)。Saturating integer arithmetic、拡大積、shift、narrowの仕様を確認。論文ではない | u8/u16のnative飽和、同一shift量を全laneへ適用する仕様が生成則の前提。命令の新規性は主張しない。 |
| Tigress, *Encode Data* | [公式技術資料](https://tigress.wtf/encodeData.html)。codec説明・summaryを確認。動的に更新される文書、査読論文ではない | 異なる表現で計算し、対応する演算はdecodeせず処理する一般方針、複数の表現を持つcodecは既存。今回の狭い飽和更新の商を同じページで確認したわけではない。 |
| Mayan Moudgill, Vladimir Kotlyar, *Method for recognition of full-word saturating addition and subtraction*, US7171438B2 | [公開公報のHTML](https://patents.google.com/patent/US7171438B2/en)。B2公開2007-01-30。書誌、説明中の認識手法、BITS/COND/REACHの記述を確認。請求項全体の対比は未実施 | データフロー方程式を解き、通常のコードをnative飽和演算へ認識・置換する技術。native命令化だけでは新規性の根拠にならない。今回の任意低bitを保持する表現と完全に同一と断言しない。 |
| Sabine Glesner, Jan Olaf Blech, *Classifying and Formally Verifying Integer Constant Folding* | ENTCS 82(2), 410–425, 2004、[DOI](https://doi.org/10.1016/S1571-0661(05)82600-3)。出版社由来の検索抽出で書誌・要旨を確認。直接本文は403、著者公開PDFは取得失敗 | 異なる算術を置換する一般条件と整数剰余算術の形式検証。本文を読めていないため、今回の飽和商の恒等式が既に掲載されているとは主張しない。検索上の年2003と出版年2004を区別する。 |

最も近い技術の系統は、幅を変える整数表現と演算に適合するdata encoding、およびnative飽和へのcompiler lowering。具体的な差分候補は、論理上限に合わせたAを選び、下位bitを毎回一つの値へ戻さず、正しく計算できる集合全体を許す生成則にある。

しかしDは上位bitだけを取る簡単な写像で、演算族も飽和平行移動に制限される。一般の符号化・商・固定小数点という概念を新発明とは数えない。同一の生成則を持つ先行例の有無は未確定であり、現在の調査で特許上の新規性が立証されたとはいえない。

保護効果については別の否定材料がある。通常版と同じ公開問い合わせで等価処理が得られ、標準8bit表現の方が高速だった。最も強いReject理由は「既知の表現・飽和最適化から独立した差分と、追加の保護効果の双方が弱い」である。特許公報の一般的な記述だけで今回の全構成の先行性を確定した、という理由ではない。

WASMixer等の完成ツールをこの実験で再実行してはいない。native8とcanonicalは明示した基本原理を自作実装した対照。未対応ツールやクラッシュを防御成功に数えない。
