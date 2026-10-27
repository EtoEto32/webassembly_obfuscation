# 先行技術と今回の差分

確認日2026-10-23。未読部分、法的な特許性、一般整数上の議論を有限機械整数上の保護効果へ読み替えない。

|文献・区分|実際に確認した範囲|提案・今回との関係・限界|
|---|---|---|
|Shay B. Cohen, Karl Stratos, Michael Collins, Dean P. Foster, Lyle Ungar, *Spectral Learning of Latent-Variable PCFGs*, ACL2012,223–231。[一次PDF](https://aclanthology.org/P12-1024.pdf)。査読会議論文|要旨、導入、§5のTheorem1、§6の可逆行列条件とTheorem2|潜在変数文法のテンソル表現と観測可能表現。可逆行列で混ぜるだけの案には直接近い。数値実験は今回未読・未再現。今回の非線形変換は異なるspan同士の連結を含み、同じセル内の線形混合ではない。この差だけで新規性を確定しない|
|Guillaume Rabusseau, Borja Balle, Shay Cohen, *Low-Rank Approximation of Weighted Tree Automata*, AISTATS2016,PMLR51,839–847。[出版社](https://proceedings.mlr.press/v51/rabusseau16.html)。査読会議論文|出版社の要旨・書誌、検索で取得した著者補足のTheorem2証明冒頭。本文全体未読|Hankel行列のSVDによるWTA縮小。要旨は実データのperplexity改善を述べるが数値は今回取得していない。WTAの基底変換は既知であり、線形案を新発明と呼べない|
|Marcello M. Bonsangue, Jan Rutten, Joost Winter, *Defining Context-Free Power Series Coalgebraically*, CMCS2012,LNCS7399,20–39, DOI[10.1007/978-3-642-32784-1_2](https://link.springer.com/chapter/10.1007/978-3-642-32784-1_2)。査読会議論文。[会議PDF](https://coalg.org/cmcs12/papers/00010020.pdf)|要旨、導入、§4のproper algebraic systemの定義・一意解と対応の説明|形式級数、文法、代数方程式の関係は既知。今回の意味保存の土台はここに属する。論文の主題は難読化の保護評価ではなく、今回の解除時間を裏付ける資料ではない|
|Paul Marion Hriljac, *Systems and methods of source software code obfuscation*, [WO2012040383A1](https://patents.google.com/patent/WO2012040383A1/en),公開2012-03-29、優先日表示2010-09-24。公開公報|書誌、説明0038–0049。以前のhidden-filtration調査で0048–0057ほかも確認|可逆な非線形変数変換、逆変換、変換の合成が近接。今回のspan畳み込み・propernessを保つ生成・二項化・三次係数による解除の組を個別に記載していることは未確認。しかし一般的な非線形座標変換を新規な核として主張できない。権利の有効性・侵害・進歩性は判断していない|

探索語：`"weighted context-free" "polynomial" "automorphism"`、`"algebraic systems" "noncommutative" "change of variables" grammar`、`"obfuscation" "formal power series"`、`"grammar obfuscation" patent`、`noncommutative algebraic power series proper algebraic systems context free Schutzenberger pdf`。一致する論文が出なかった検索を、新規性の証拠には数えない。

**技術的に言える差**：線形な同一spanの混合から、全分割点を通る非線形な級数変換へ移した。小さいbitwise関数の全数学習とは別に、長さ可変のparserで実装した。しかし生成規則は既知の多項式置換に近く、公開された三次成分だけで解除できる。主特許候補には採用しない。

**残す知見**：単一の二次shearでは、係数を任意の32bit値にしても、非可換な三次係数の合同式が簡潔な等価文法への回復を許す。具体的な証明と再現実験を残すが、この否定結果自体の学術的な世界初も未確認である。
