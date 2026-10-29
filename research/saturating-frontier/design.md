# 飽和min-plus領域の分解消去：発明仮説

2026-10-18。別原理の候補。既知の代数恒等式そのもの、SIMD命令の利用、熱帯因数分解の困難性を発明・安全性として主張しない。

## 規則

S={0,...,65535}、a⊕b=min(a,b)、a⊗b=min(65535,a+b) とする。0は⊗の単位元、65535は⊕の単位元かつ⊗の吸収元。両演算は結合的で、⊗は⊕に分配する。Wasm `i16x8.min_u` と `i16x8.add_sat_u` は各laneでこの演算を正確に実行する。

対応する純粋なWasm領域を、非負の係数ベクトルと定数の有限集合に変換する。葉xiは単位ベクトル、定数は零ベクトルとその定数、minは集合和、飽和加算はMinkowski和に対応する。同じ係数では最小定数だけ残す。係数と定数がともに他の項以上の項は全非負入力で劣るため除去する。次数・項数の上限を超える場合は変換しない。

```
expand(xi) = {(ei, 0)}
expand(c) = {(0, c)}
expand(min(F,G)) = prune(expand(F) union expand(G))
expand(sat_add(F,G)) = prune({(a+b, sat(c+d)) : (a,c) in expand(F), (b,d) in expand(G)})
emit one SIMD lane per affine term; pack up to eight terms per vector
evaluate sat(c + sum(ai*xi)) using saturating additions
take lane-wise minima across packs, then a horizontal minimum
```

乗算を通常の16bit乗算に置換してはならない。繰返し飽和加算又は飽和doublingを使う。入力splatsの切詰めにより各xiは元と同じ0..65535。全i32入力を受理し、暗黙の小入力制限は追加しない。

元のmin/addの階層を係数集合から復元する情報は保存しない。同じ正規化集合を持つソースは同じ出力バイナリになる。ただしこれは元の構文の不可逆性にすぎず、同じ意味を持つ小さい計算の復元が困難とは限らない。

## 差分候補と攻撃

LOKIの依存superoperatorや従来のMBAと同じ剰余環の式難化ではなく、順序と飽和を持つ冪等半環の領域を対象とする。算術結果の公開復号器・状態番号・秘密キーは設けない。反面、対象領域が限定され、展開数が指数的に増え得る。

公開された係数集合を読み、共通項抽出、Minkowski和分解、探索による再因数分解で同等以下の演算数の式を回復する攻撃を主比較とする。未変換・展開scalar・展開SIMD・通常のO2/O3を比較する。係数が読めた時点で解析失敗とは数えず、係数抽出と簡潔な再構成を別々に報告する。

**最大のReject理由**：単なる分配展開とベクトル化であり、新しい保護原理になっていないこと。特に生成される積構造が簡単に因数分解できれば採用できない。検索で同名の方式が見つからないことは新規性の根拠にしない。

## 先行資料の確認範囲

- [WebAssembly SIMD proposal](https://github.com/WebAssembly/simd/blob/main/proposals/simd/SIMD.md)、[仕様](https://webassembly.github.io/simd/core/bikeshed/index.html)：unsigned saturationとmin命令の定義を確認。命令自体は既存。現状のアルゴリズムは他の飽和SIMDにも移植でき、Wasm専用ではない。
- Ki Hang Kim, Fred W. Roush, [Factorization of polynomials in one variable over the tropical semiring](https://arxiv.org/abs/math/0501167), 2005、確認版はarXiv v2（プレプリント）、DOI 10.48550/arXiv.math/0501167：arXivの書誌・要旨を確認。一般の因数分解に関するNP完全性は、本案の有限飽和領域・生成分布・関数同値による再構成の困難性を証明しない。本文精査と査読発表先確認は未完。今回の実装に対する評価結果を報告した資料ではない。
- Bo Lin, Ngoc Mai Tran, [Linear and Rational Factorization of Tropical Polynomials](https://arxiv.org/abs/1707.03332), 初稿2017・確認版2019 v3（プレプリント）、DOI 10.48550/arXiv.1707.03332：arXivの書誌・要旨を確認。豊富な特別クラスに効率的な因数分解法を与えると報告。形式多項式の分解と、関数として同じ最小値の分解の相違を次に精査する。本文・査読発表先・計算量の詳細は未確認。
- [LOKI](https://synthesis.to/papers/usenix22-loki.pdf)と[SaMBA](https://eprints.cs.univie.ac.at/8730/1/2026_samba.pdf)は従来の式難化との差分確認先。今回の領域では両者の実装を比較実行していない。

この構成を単に「熱帯因数分解はNP困難だから安全」として採用することは禁止する。
