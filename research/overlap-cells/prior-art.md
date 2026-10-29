# 先行研究と読了範囲

調査日2026-10-19。新規性を反証する目的で符号化表、無効領域、重複表現、共有成分の回復を調べた。既存のWasm調査は[全体文献レビュー](../literature-review.md)にある。以下のアクセス不足を新規性の根拠にしない。

| 資料 | 書誌・確認範囲 | 今回との関係 |
|---|---|---|
| *White-Box Cryptography and an AES Implementation* | S. Chow, P. Eisen, H. Johnson, P. C. van Oorschot。SAC2002、LNCS2595（2003）、[DOI](https://doi.org/10.1007/3-540-36492-7_17)。査読論文。[以前の確認範囲](../isotope-swizzle/prior-art.md)を継承し、今回は全文を再取得していない。 | 入出力全単射を演算表へ合成する核は既知。singleを新手法とは数えない。 |
| *Enhanced Encodings for White-Box Designs* | Alberto Battistello, Laurent Castelnovi, Thomas Chabrier。CARDIS2021。[公式プログラム](https://cardis2021.its.uni-luebeck.de/program.html)と[著者版PDF](https://cardis2021.its.uni-luebeck.de/papers/CARDIS2021_Battistello.pdf)冒頭、§2、§3の符号化・gate構成を確認。査読会議論文としての掲載を確認したが、評価節全体の精読ではない。 | Benaloh由来の表現でgateを計算する提案。今回の隣接pair supportとは異なる。符号化やmaskingを使うこと自体の新規性はない。数値比較は行っていない。 |
| *White Box Implementations Using Non-Commutative Cryptography* | Leandro Marin。Sensors 19(5),1122、2019-03-05、[DOI](https://doi.org/10.3390/s19051122)。査読誌論文。MDPIの直接openは429、PMCはrecaptchaだったが、[出版社本文の検索索引](https://www.mdpi.com/1424-8220/19/5/1122)から要旨・導入・§3.4のoverlapping orbitsと無効値・その構成例の該当段落を実際に取得。全文通読ではない。 | 無効な表要素への任意値の設定や表現領域の重複で解析を誤らせる発想が明記される。群作用・heading spaceを使う方式で、今回の同じ実データを共有する隣接pairとは一致しない。しかし「無効entryに偽値を入れる」だけを新規点にできない。著者の安全性主張を本研究の事実にはしない。 |
| *Maximum Entropy Functions: Approximate Gács-Körner for Distributed Compression* | Salman Salamatian, Asaf Cohen, Muriel Médard。[arXiv1604.03877v2](https://arxiv.org/html/1604.03877)、2016-04-14。本調査ではプレプリントとして扱い、要旨・§I・§II-Bを実読。発表先は未照合。 | 正のjoint supportの二部グラフとその連結成分による共通情報の分解を明記。今回の回復の数学的原理は既知。本論文はWasm難読化の評価ではなく、今回の攻撃実装の初出を立証するものでもない。 |
| *White-Box Cryptography Interleaved Lookup Tables* | Jan Hoogerbrugge, Wilhemus Michiels（公報表記）。[US20160350560A1](https://patents.google.com/patent/US20160350560A1/en)、公開2016-12-01。特許公報。書誌、構成の説明、請求項1–20を取得。B2版の請求項を今回読んだとはしない。 | 共通indexの二次元表を三次元表へ書き換え、配置のinterleaveによって高速化する構成。今回の整合するpair入力、192無効entry、新しいpair置換の伝播とは技術的に異なる。「表をまとめる」だけでは差にならない。法的な権利範囲や実施自由の結論は出していない。 |
| *NotDec: WebAssembly Decompilation With Inter-Procedural Type Recovery* | Jikai Wang, Ningyu He, Tianming Liu, Junhai Wang, Haoyu Wang。[arXiv2608.03286](https://arxiv.org/abs/2608.03286)、2026-08-04。今回取得したのは要旨・書誌と[公式実装README](https://github.com/NotDec/NotDec)。この確認範囲ではプレプリントと区別して扱う。 | 型付きIRや手続き間の型回復を対象とする。今回NotDecを実行した比較はない。本専用回復器での成功を、NotDecの結果や型回復一般の結果として扱わない。 |

未読・照合待ち：*WeBMO: WebAssembly Memory Bitwise Operation Obfuscation*（Park, Cho、COMPSAC2024、DOI10.1109/COMPSAC61105.2024.00189）は二次資料の書誌・要旨のみ。US20090158051A1は検索抄録を取得したが全文openが失敗。US20170033921A1も検索抄録のみ。US6668325B1のarray変換は検索結果での照合候補。これらの未読本文を想像して差分を埋めない。

検索語には `overlapping encodings lookup tables obfuscation`、`software obfuscation invalid table entries overlapping orbits`、`white box implementations non commutative cryptography invalid elements`、`WebAssembly memory bitwise obfuscation`、`common information bipartite connected components`、`patent software obfuscation lookup tables bijective encodings`を使用した。該当しない検索結果もあり、網羅的な特許調査を終えたとは扱わない。

実装上の差分候補は「実データの重複を維持する局所pair更新、到達不能表領域の全域置換化、更新ごとのpair置換変更」の具体的構成だった。しかし既知の符号化表と無効領域処理に近く、適応解析ではsupportの共有成分を伝播するだけで分解できた。追加の置換変更にも優位性が見えず、現時点で主発明に採用する根拠は弱い。これは法的な特許性の否定を確定する結論ではない。
