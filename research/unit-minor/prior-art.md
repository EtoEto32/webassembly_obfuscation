# 近い先行技術と今回の差分

2026-10-22。以下の実読範囲を超えて内容を推測しない。単なる検索不発は新規性の根拠にしない。

| 資料 | 書誌・実読範囲 | 今回への意味 |
|---|---|---|
| James Bartusek, Yuval Ishai, Aayush Jain, Fermi Ma, Amit Sahai, Mark Zhandry, *Affine Determinant Programs: A Framework for Obfuscation and Witness Encryption* | 査読会議ITCS 2020、LIPIcs 151:82、[DOI 10.4230/LIPIcs.ITCS.2020.82](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ITCS.2020.82)。[出版社PDF](https://drops.dagstuhl.de/storage/00lipics/lipics-vol151-itcs2020/LIPIcs.ITCS.2020.82/LIPIcs.ITCS.2020.82.pdf)の要旨・技術概要、§8.1.1–8.1.3、§9.3の該当箇所を確認。全証明・著者実装の再現は未実施。 | 入力依存行列式による全計算の表現、局所置換、左右の混合は既存。有限体・Boolean入力・候補iOの設計を、我々のi32算術式の安全性へ転用しない。 |
| Li Yao, Yilei Chen, Yu Yu, *Cryptanalysis of Candidate Obfuscators for Affine Determinant Programs* | 査読会議EUROCRYPT 2022、pp.645–669、[DOI 10.1007/978-3-031-06944-4_22](https://doi.org/10.1007/978-3-031-06944-4_22)。[IACR会議PDF](https://iacr.org/archive/eurocrypt2022/132760166/132760166.pdf)の要旨・§1.1・§5のmod 4展開・§6を確認。ePrint 2021/1684は別のpreprint表示であり、発表年を混同しない。 | ADPの特定の局所ランダム化への攻撃と修正案がある。修正案自体も安全性確立とはしていない。我々の記号行列式回復は、その論文の攻撃を再現したものではない。 |
| Harold Johnson, Yuan Xiang Gu, Michael Wiener, *Securing accessible systems using cross-linking*, EP2831791B1 | [公開文献](https://patents.google.com/patent/EP2831791B1/en)。header、説明C4.1、C7 Proposition 7と周辺、Dの該当段落を確認。A1公開2015-02-04、B1公開2020-10-21。優先日2012-03-30を公開日と数えない。全請求項・family・図中数式を網羅した調査ではない。 | Z/(2^n)上の入力依存行列、多項式係数の行・列加算による生成が明記される。入力依存shearを新発明と数えない。今回の非単元出力fを含むbordered matrixとは構成範囲が違うが、その差だけで新規性や進歩性を認定しない。 |
| Stephen Drape, Irina Voiculescu, *Creating Transformations for Matrix Obfuscation* | SAS 2009、[DOI 10.1007/978-3-642-03237-0_19](https://doi.org/10.1007/978-3-642-03237-0_19)、[著者機関PDF](https://www.cs.ox.ac.uk/files/2891/SAS.pdf)。この区間では[過去の本文読解記録](../../tmp/determinant-representation-audit/README.md)を再確認。 | 数値を行列式で表す原理は既存。過去に棄却した固定基底のscalar codecとは今回の全式変換を区別するが、行列式そのものの新規性は主張しない。 |

アクセス記録：ePrint 2020/889と2021/1684は403、Princeton版は401だった。ADPは出版社PDF、攻撃論文は検索で得た同じIACR会議URLから本文を読めた。CN114021083Bは今回本文取得に失敗し、検索手掛かりのままとする。読めなかった資料の内容や権利範囲を補完しない。

追加検索には `"obfuscation" "unimodular" matrices`、`"obfuscation" "polynomial matrices" determinant`、`"determinant" "obfuscation" "row" "polynomial"` を使い、上の直接的な多項式行列生成の先行記載を見つけた。

残る実装上の差は、純粋なi32式からunit-minorを持つ行列を作り、生成時に混合を展開し、全pivotのうち最後だけ非単元を許す評価器へ落とすこと。ただし、block determinant、rank保存、単元によるGaussian消去は標準的な代数である。独立した新しい難読化原理は未確立。最大のReject理由は、既知の行列式表現と多項式行列変換をword ring向けに組み合わせた実装であり、保護上の差が小例の解析費用増に留まること。
