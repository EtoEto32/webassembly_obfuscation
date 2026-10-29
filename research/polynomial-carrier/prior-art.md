# 共同多項式更新：先行技術と差分

調査日2026-10-18。読んだ箇所と推論を分離する。この記録は技術構成の比較であり、特許の有効性、権利範囲、実施自由を判定していない。

## 最も近い構成

**ASPIRE D2.01, Early White-Box Cryptography and Data Obfuscation Report**, 2014, v1.01。Editor: Mariano Ceccato。Contributors: Brecht Wyseur, Patrick Hachemane, Mariano Ceccato, Roberto Tiella, Jerome D’Annoville。EU研究プロジェクトの公開技術報告であり、査読論文として数えない。[公式PDF](https://www.aspire-fp7.eu/sites/default/files/D2.01-ASPIRE-Early-White-Box-Cryptography-and-Data-Obfuscation-Report-v1.01.pdf)。

表紙・版情報と§11.1.2–11.1.4を確認した。§11.1.2は可逆写像を更新の前後に置く多項式構成を扱い、§11.1.4は単項式の事前計算と時間・メモリの関係、SIMD等の実装要因も議論する。Table 13の性能は推定、Table 14は生成したC/GCC O2の実測であり混同しない。対象は有限体上のwhite-box暗号系で、今回のmod 2^32整数スキャナとは異なる。報告中の一般問題の困難性を、今回の構造を持つ式へ移して主張しない。全節・参照文献を精読したとはしない。

こちらの技術的判断：`A F(A^-1 z,u)` の展開と単項式共有を主発明にするのは弱い。Wasmのi32x4命令へ対応させる実装差があるだけでは、独立した保護機構の新規性を支持しない。先行技術の中心構成と一致する点を隠して「初めて」と書かない。

## 関連公報

**US7966499B2**, *System and method for obscuring bit-wise and two's complement integer computations in software*。発明者Arun Narayanan Kandanchatha、Yongxin Zhou。B2公開2011-06-21、対応A1公開2005-07-28。[公報本文](https://patents.google.com/patent/US7966499B2/en)。書誌、本文の有限環変換の説明、請求項1–22を確認した。審査経過・全図面は確認していない。

請求項1は変数へのbias/scalingと剰余逆元を利用した同値式への置換、17–18は線形変換と有限環実装、21–22はscalingとmodulusの条件を含む。今回の4変数を横断する行列混合・SIMD配置をそのまま記載するものと断言しないが、整数の折返しと同値式の置換一般を新規性にできない。公報中の解析困難性の説明を実測済みの事実として採用しない。

## 構成ごとの比較

| 今回の要素 | 近い先行要素 | 今回確認できた差 |
|---|---|---|
| 可逆な状態変換で更新の前後を対応付ける | ASPIREの多項式写像構成 | 有限体の暗号系から有限環の一般整数更新へ対象が違う |
| 32bit折返しを符号化演算に使う | 上記公報の有限環・等価式 | Wasmの厳密な整数意味に合わせた入力制限と検証 |
| 多項式展開と単項式共有 | ASPIREの展開系・実装上の単項式計算 | 4出力係数を固定128bit SIMDに配置 |
| 公開出力から逆像・既知因子をたどる | 線形方程式、既知因子の除算 | 今回の限定スキャナへの具体的な解析実装。新数学手法とはしない |
| 結果 | 主実験で融合実行はdecodeより一部高速 | 解析費用はdecodeとほぼ同じ。差分の保護効果は未支持 |

WASMixer等との関係は研究全体の[文献調査](../literature-review.md)に残す。この候補では「Wasmを使った」という形式上の差より近い、座標変換・多項式展開の先行技術を優先した。近い実装の完全再実装や、網羅的な公報調査は未完了。この調査範囲で特許の新規性・進歩性を確定しない。
