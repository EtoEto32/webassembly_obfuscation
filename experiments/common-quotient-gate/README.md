# 固定したワード単位の商による段階実行：成立条件の検証

後続検証：[異なる入力・出力表現を許した追加検証](HETEROGENEOUS.md)。本記録の同一商という仮定を外した場合を別実験として扱う。

## 1. 状態：Inconclusive

2026-10-12。新規Wasm難読化方式は採用しておらず、研究全体の目標の状態はactive（継続中）である。今回は、複数ラウンドにわたる制約実行を構成する一案を、数学的な根拠に基づいて棄却した。制約実行全般や難読化が不可能であるとは主張しない。

## 2. 達成事項

固定した部分情報だけで加算とSHA-256のΣ/σ演算を更新する案について、任意のワードの分割に対する必要条件を導出した。Pythonで幅1～3の全4,157分割を列挙した。32ビットでは、非自明な加算商の全31種類について4演算を調べ、計124個の反例を保存した。新しい変換器ではなく、成立しない設計を除外するための証拠である。

## 3. 未達事項

独立した新しい原理、汎用変換器、採用方式のSHA全体、攻撃上の優位性、性能・サイズ・最適化後の残存性を満たしていない。元の依頼§13の完了条件は依然未達。過去のplain/MBAの正確性は新方式の完成証拠に数えない。

## 4. 候補と成立条件

検討した候補は、各語を固定した商 `q: Z/(2^32) -> C` のラベルで部分的に表し、演算を商上で更新してから細かい段階へ進む構成。同じqを各オペランドと結果に使い、全入力について

```text
q(x+y) = A(q(x),q(y))
q(Sigma(x)) = S(q(x))
```

を満たすA,Sが必要である。ラベルの名前、ビット順、線形基底には制限を設けず、qは任意の写像とする。ただし、追加情報、入力に依存する分割、演算ごとに異なるq、複数ワードを共同で表す状態は含めない。定数qと単射qでは、部分的な精度による段階実行にはならない。

**加算だけでもqの同値類は下位kビットに限られる。** `x~y iff q(x)=q(y)` と定義する。加算の適合性から、任意のcでx+c~y+c。Nを0の同値類とすると、0を含み、加算で閉じる。有限群なので負元でも閉じ、Nは加法部分群。さらにx~yとx-y∈Nは同値。巡回群Z/(2^w)の部分群は `N=2^k Z/(2^w)` (k=0,…,w) だけなので、同値類はmod 2^kに一致する。q自体のラベルは自由だが分割は変わらない。任意の全単射で語を符号化してからqを取っても、合成した写像に同じ条件が必要となる。

**SHAのΣ/σとは非自明な商を共有できない。** 次の各演算についてrを最大の回転量とする。

| 演算 | 右回転量 | 論理右シフト量 | r |
|---|---|---|---:|
| Sigma0 | 2,13,22 | なし | 22 |
| Sigma1 | 6,11,25 | なし | 25 |
| sigma0 | 7,18 | 3 | 18 |
| sigma1 | 17,19 | 10 | 19 |

任意の1≤k≤31について、j=max(k,r)、x=0、y=2^jとする。xとyの下位kビットは同じ。一方、回転rによる出力ビットj-rはk未満で、他の回転やシフトのビットとは重ならず、XORで消えない。このため出力の下位kビットは異なる。よってA,Sを同時に定義できない。証明は32ビット整数の純粋演算に対するもの。メモリ、トラップ、Wasmの実行全体についての証明ではない。

## 5. 先行研究との比較

検索日2026-10-12。検索語：`software obfuscation constraint system implicit equations iterative fixed point computation obfuscation`、`obfuscation program constraint logic programming transformation imperative`、`Klimov Shamir T functions triangular functions bit slice rotation invertible mappings pdf`、`implicit white box ARX equations rotations linear encodings solving 2022`、`New Applications of T-functions filetype:pdf`、`Non-Archimedean analysis, T-functions, and cryptography arxiv`。

一次資料の確認範囲：

- Vladimir Anashin, *Non-Archimedean analysis, T-functions, and cryptography* (2006), [著者プレプリント](https://arxiv.org/pdf/cs/0612038)。§4.1末尾～§4.2冒頭（PDF pp.13–14）を確認。合同関係と適合写像、T関数と2進合同の関係を説明している。今回の有限巡回群の証明は自前で記述した標準的な代数の適用で、新定理として扱わない。
- Ranea et al., *Implicit White-Box Implementations: White-Boxing ARX Ciphers* (CRYPTO 2022), [著者論文](https://crypto.iacr.org/2022/papers/530630_1_En_2_Chapter_OnlinePDF.pdf)。定義3～4、§3～§3.1の該当部分を確認。入力を固定して出力についてアフィン系を解く構成は既知。本案の固定商という条件を課した方式ではないため、今回の不成立をこの論文への攻撃結果と呼ばない。

Klimov–ShamirのFSE 2005論文は一次サイトの検索抽出で冒頭を確認したが、直接openは403。COSICの解説ページはtimeout。両者の本文を読み終えたことを主張しない。Translingual Obfuscationは検索結果のみで、比較の根拠に使っていない。

| 比較項目 | 判断 |
|---|---|
| 数学的原理 | 固定商の演算適合性は既知の合同の概念 |
| 表現体系 | 非線形なラベルも許したが、加算に適合する分割はmod 2^k |
| 状態変換 | 座標・ラベル変更で条件を回避できない |
| 依存関係 | 全入力・同じ語分割を要求する点が本検証の範囲 |
| 困難性の原因 | 実行方式が成立せず、解析困難性の段階に到達していない |
| 一般化 | 他の固定幅にも加算部分の証明は適用。SHA定数の反例は32ビット |

## 6. 再利用

既存Python 3.12.14をA（そのまま利用可能）として使用。`tmp/fixed-point-source-audit`、`tmp/nonbijective-residual-gate`、`tmp/settling-carry` のREADMEを読み直し、C（失敗原因の参考）として利用した。固定点の存在と収束の区別、暗黙方程式の既知性、依存グラフが残る問題を踏まえた。過去の結果を再実行したとはしない。

## 7. 実装と検証

実験前に `protocol.json` を保存し、標準Pythonのみの `check.py` を実行した。分割の代表をrestricted growth列で列挙し、同じ入力クラスから異なる結果クラスが出ないか、演算表を直接調べた。

| 幅 | 全分割 | 加算に適合 | XORに適合 | ROTR1に適合 | 加算とROTR1に適合 |
|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 2 | 2 | 2 |
| 2 | 15 | 3 | 5 | 7 | 2 |
| 3 | 4,140 | 4 | 16 | 33 | 2 |

共通の2分割は定数と恒等。加算単独ではmod 2^kの全候補が通り、XOR単独ではそれ以外も通ることを対照にした。小さいビット幅での検査はSHA-256全入力での検証ではない。32ビットの実験は、各演算・各kについて同値な入力対で出力が非同値となる証人を探索・検査したもので、124件すべてが得られた。全受理分割、反例、コードとprotocolのSHA-256は `results.json` に保存した。

## 8. 攻撃と比較

実行可能性の段階で棄却したため、攻撃実験・既存方式との公平な比較は未実施。候補の狙いは、解析者にワード全体を示さず制約を段階的に解くことだったが、固定した非自明な部分情報だけでは更新を定義できない。今回の反例は意味保存に関するもので、攻撃成功率ではない。

## 9. コストと最適化

Wasmは生成していない。処理速度、バイナリサイズ、最適化後の残存性の測定値はない。Pythonによる列挙の速さを、この方式の性能として扱わない。

## 10. 改善サイクル

通常の下位ビット順だけでなく、任意のビット順・非線形な分割へ条件を緩める案を検討した。しかし、加算への適合性から分割が再びmod 2^kに限定された。小さいビット幅での全数検査とSHAの反例がこの帰着を支持したため棄却。ワードごと・演算ごとに異なる商や共同状態なら今回の証明の外だが、未定義の代替案を改善成功とは数えない。候補予算20分、実験コマンド60秒以内、追加パラメータ探索0。

## 11. Before/After案と実例

サンプルID COMMON-QUOTIENT-1。変換前は `z = Sigma0(x)`、想定した変換後は次である。

```diff
- z = Sigma0(x)
+ class_z = table_Sigma0[class_x]
```

`class_x=q(x)`。このAfterは**成立しない変換案**で、生成済み難読化コードではない。具体的な反例は `results.json` のwitnessesにある。k=1ならx=0とy=4はともに偶数だが、Sigma0の結果は偶奇が異なり、同じclass_xに一つのclass_zを割り当てられない。ビルド・最適化に進まなかった理由はここにある。

## 12. 保存先・再現手順

本ディレクトリのprotocol、check.py、results.json、READMEが今回の成果。既存結果を上書きしないため、空ディレクトリへコードとprotocolをコピーして実行する。

```powershell
$dest = 'tmp/common-quotient-reproduction-01'
New-Item -ItemType Directory -Path $dest -ErrorAction Stop
Copy-Item experiments/common-quotient-gate/check.py,experiments/common-quotient-gate/protocol.json -Destination $dest
.tools/runtime-analysis-py312/Scripts/python.exe "$dest/check.py"
```

期待値は§7の表とwitness_count=124。今回実行したコマンドは `.tools/runtime-analysis-py312/Scripts/python.exe experiments/common-quotient-gate/check.py`。コピー先での再実行はしていない。

## 13. 限界

固定・ワード単位・全入力・同じ商という仮定を外す方式、補助状態、集合値の近似、オーバーアプロキシメーション、入力確定後のアフィン解法、複数語の関係表現を除外しない。部分情報のラベルだけで各演算を正確に進める案に限った結果である。新規性の核心はまだ得られておらず、これを研究目標の代替成果や完成と扱わない。
