# 先行資料と確認範囲

確認日2026-10-21。暗号的な解析不能性を目的としない。ここでの候補は公開Wasmのプログラム変換であり、rANS圧縮そのものを発明と主張しない。

| 資料 | 書誌・読んだ範囲 | 今回への含意 |
|---|---|---|
| Jarek Duda, *Asymmetric numeral systems: entropy coding combining speed of Huffman coding with compression rate of arithmetic coding* | 2013、v2は2014-01-06、[arXiv:1311.2540v2](https://arxiv.org/abs/1311.2540v2)、DOI 10.48550/arXiv.1311.2540。プレプリント。書誌・要旨のみ確認、全文未読 | 単一自然数の符号状態と表駆動化は既知。著者の速度値・暗号化への議論を本候補の効果へ転用しない |
| Fabian Giesen, *rANS notes* | 2014-02-02、[作者の解説](https://fgiesen.wordpress.com/2014/02/02/rans-notes/)、非査読。Streaming rANSのC/D式、正規化の説明、proofs part1冒頭を確認 | Dの商・剰余式を直接比較対象にした。有限精度の復号が補給streamを必要とすることを無視しない。本案は意図的にその補給を除く制約を課す |
| Fabian Giesen, `ryg_rans/rans64.h` | 冒頭著作年2014、[公開実装](https://raw.githubusercontent.com/rygorous/ryg_rans/master/rans64.h)。Rans64EncPut、DecGet、DecAdvanceを確認、mainはcommit未固定 | 実装でも剰余によるsymbol判定と商による更新が分かれ、必要時に32bitを補給する。本研究はこのコードを移植・再実行したものではない |
| Schloegelほか、LOKI | USENIX Security 2022。[過去に本文§4.5等を確認した記録](../../tmp/semantic-fusion-audit/README.md) | 演算境界を消す一括合成の一般方向は既出。今回新たにLOKI全文・コードを再監査したとはしない |

追加検索：`"obfuscation" "rANS"`、`"obfuscation" "asymmetric numeral systems"`、`"virtual machine" "arithmetic coding" obfuscation`。直接一致を見つけられなかったことを新規性の証明にしない。検索で現れただけの暗号化・マルウェア検出等の資料は、本候補の先行構成を読んだ証拠に使わない。

変数と制御を一つの表現へ混ぜる一般方向には[既存の関係式・公開公報調査](../patent/joint-relations.md)もある。本候補の具体差は、復号器の数値更新そのものに意味計算を担当させ、独立した意味更新を消そうとする制約である。その制約で意味保存が成立するかが未解決で、技術効果や特許性はまだ認定しない。
