# 新規性監査：構造化境界での状態再符号化

確認日：2026-10-11。対象：このリポジトリの `619ce7be0fb3ceeb631f170d7614bb26f8639b08` にある試作。

## 判定

**現状の試作を「既存研究にない新しいWasm難読化アルゴリズム」として採用しない。**
多変数アフィン符号化、領域ごとの符号化、境界の復号・再符号化の合成には、直接対応する先行研究がある。
Wasmの多値ブロックへの実装という差はあるが、それによる新たな解析困難性は立証できていない。
追加した限定的な反証実験でも、領域ごとの符号化によって入出力式の推定に必要な問い合わせ数は増えなかった。

これは「同一のWAT実装が既に公開されている」という断定でも、あらゆる将来の評価研究を否定する判断でもない。
現在主張できるのは、**既存データ符号化をWasmへ適用した試作と、限定された算術サンプルでの解析容易性の確認**である。
本監査は新しく作った整数計算用リポジトリを対象とする。従来の公開データセット・ハッシュ計算・対策検討の論文の新規性は別に判断する。

## 中核的な重複

| 試作の要素 | 一次資料の該当箇所 | 判定と残る差 |
|---|---|---|
| `E(v)=Av+b` で複数変数を同時に混ぜる | Fukushimaほか、2006、§4.1、式(1)、誌面503頁／PDF6頁 [S1] | 行列とベクトルによる多変数符号化は既存。試作は2変数・32bit剰余環に限定する |
| プログラム領域ごとに別の符号化を割り当てる | Majumdarほか、2007、§5.3、PDF9頁 [S2] | 領域別の表現という発想に直接の先行例がある |
| 境界で復号と次領域の符号化を合成する | 同§5.3 [S2] | 同節は隣接する変換の式をまとめることも説明している。今回の中核と強く重複 |
| 変換後も意味を保存し、途中の復号式を簡約する | Drapeほか、2007、§2.2–2.3、式(3)–(9)、付録A [S3] | データ表現と処理の関係を用いる枠組みは既存。Wasm/i32の意味に合わせる実装差は残る |
| 符号化したまま演算する | Tigress EncodeData、冒頭例とpoly1 [S4] | 中間値を平文へ戻さないこと自体を新規性にできない |
| multi-valueの分岐結果・ループ引数に値の組を渡す | Wasm multi-value提案、Motivation／Validation [S5] | 標準の値受渡し機構。後方辺のphiを表す用途も既に説明されている |
| 領域別符号化で式の再構成を難しくする | 今回の追加実験 [E1] | 対象サンプル・手法では問い合わせ数の増加なし。一般的な解析耐性は未評価 |

S1は一般の整数行列を扱い、計算範囲の制約を§7.2で議論している。S2の§4.3にもオーバーフローと割り切れる除算への注意がある。
したがって「先行論文とビット単位まで同じ変換」とは言わない。今回、奇数行列式を選んで `Z/(2^32)` 上で逆行列を求めた点は実装上の違いである。
ただし、剰余環上の可逆性という通常の代数条件を採用しただけでは、新しい難読化原理や優位性を示したことにならない。

S3の付録はSSAを連立式の整理の参考にしているが、phi関数は直接使わないと述べる。
「S3に今回と同じSSA合流処理が実装済み」とは主張しない。Wasmの値受渡しの根拠はS5である。

## 式の対応：今回の解析

先行研究の変換関数を `cf_r=E_r`、復元関数を `af_r=D_r` と読み替える。
逐次記法で境界の `af_r; cf_s` は、関数合成では `E_s ○ D_r` となる。
元の処理 `F` を含めた試作の規則は次の通りであり、既存の表現変更を領域間に適用した形である。

```text
T_(r,s) = E_s ○ F ○ D_r
D_s ○ T_(r,s) ○ E_r = F
```

`F(v)=Mv+c` なら、今回の変換は

```text
T_(r,s)(z) = A_s M A_r^-1 z + (A_s c + b_s - A_s M A_r^-1 b_r)
```

という別のアフィン写像になる。この式は本監査での導出であり、先行論文からの引用ではない。
今回の生成器では分岐は `flag & 1`、ループ回数は `n & 15` だけで決まり、`x,y` は制御に影響しない。
そのため制御引数を固定した関数全体もアフィン写像となる。多値構文を使ってもこの性質は変わらない。

## 追加実験 E1：入出力式の再構成

実装：`tests/affine-recovery.cjs`。生データ：`artifacts/affine-recovery.json`。
元の生成器、プログラム定義、manifestの意味情報、符号化行列、mapping.jsonは推定器に与えない。
推定器はファイル名で対象42本を選択し、Wasmの公開関数 `run(x,y,flag,n)` の出力だけを利用する。
実験後に別処理で42本のSHA-256を既存manifestと照合し、すべて一致することを確認した。

### 方法

制御条件ごとに `f(x,y)=M[x,y]^T+b (mod 2^32)` を仮定する。
`f(0,0)` で `b`、`f(1,0)-b` と `f(0,1)-b` で `M` の各列が得られる。
必要な学習用問い合わせは3回。これは基礎的なアフィン補間であり、新しい解析アルゴリズムという主張はしない。
近年の黒箱解析にもアフィン・多項式の推定が使われる [S8] が、この実験はSMIRの再現ではない。

- 対象：3プログラム × (baseline 1条件 + global 3シード + per_region 3シード) × 最適化なし／O2 = 42本。
- 制御条件：`flag=0,1` × `n=0..15` = 各32条件、合計1,344条件。
- 推定に使わない入力：各条件につき境界値46組と固定シード疑似乱数1,024組、計1,070組。
- 境界値には `0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff` を含む。学習3入力は除外。
- 非アフィンの積・平方を別途試し、検証入力 `(2,3)` で不一致として棄却することを確認。
- Node.js 24.15.0。V8版とスクリプト・入力WasmのSHA-256はJSONに記録。

### 実測結果

| 方式 | Wasm本数（O2込み） | 制御条件数 | 学習用問い合わせ／条件 | 検証した出力ペア数 | 不一致 |
|---|---:|---:|---:|---:|---:|
| baseline | 6 | 192 | 3 | 205,440 | 0 |
| global | 18 | 576 | 3 | 616,320 | 0 |
| per_region | 18 | 576 | 3 | 616,320 | 0 |
| 合計 | 42 | 1,344 | 3 | 1,438,080 | 0 |

学習用問い合わせ総数は4,032。推定した係数も、同じプログラム・制御条件の全変種で基準版と一致した。
143万件という値はバイナリ・制御条件をまたぐ出力比較の総数であり、143万種類の独立したプログラムや入力ではない。

**言えること：** このサンプル群では領域別符号化が、この方法の学習用問い合わせ数を増加させていない。
**言えないこと：** 元のソース、内部の符号化鍵、内部変数、CFGを復元した／一般Wasmを3回で解析できる／全解析手法に無効／実行時間も同じ、とは言えない。
推定したのは公開入出力の関係で、計算全体がアフィンであるという強い前提がある。
有限個の入力による照合自体は全入力での同値性の証明でもない。この結果だけで元の難読化方式一般の無効性を結論付けない。

再実行（リポジトリ直下）：

```powershell
node tests/affine-recovery.cjs artifacts artifacts/affine-recovery.json
```

## Wasm研究との位置関係

WASMixer [S6] のデータ・制御・命令変換と、Cryptic Bytes [S7] の複数レベルの変換・評価も確認した。
この2論文だけと異なっていても新規性は成立しない。一般の難読化研究S1–S4に中核的な先行例があるためである。
また、WASMixer自身も構造的な変化と特定解析に対する耐性を分けて評価する。今回のO2後のサイズ差は耐性の代用指標にしない。

Wasmのmulti-value利用と領域別符号化を完全に同一の形で組み合わせた既発表実装は、今回確認した範囲では特定できなかった。
これは「存在しない」の証明ではない。仮に初の実装でも、既存手法の移植を超える制約解決や検証結果がない限り、
それだけを新アルゴリズムの根拠にはしない、というのが本監査の判断である。

## 採用判断と次の条件

1. 新アルゴリズムの提案としての採用は見送る。新規性未確定という保留だけで研究の主軸に据えない。
2. 試作は既存符号化の比較用教材・実験基盤として残す。今回の42本は既存採掘データセットの評価件数へ混ぜない。
3. 評価研究として続けるなら、まず「既存の評価では答えていない問い」を文献に基づき定義する。
   適用箇所の選択、Wasm特有の制約、解析手法別の失敗原因とコストなどの候補にも、それぞれ追加の先行研究確認が要る。
4. 同一条件の既存方式・簡約器との比較、非アフィンを含む通常計算、実用規模、最適化後の挙動を評価するまで、有効性やCSECでの採否は保証しない。
5. 「変換数を増やす」「シードを増やす」「multi-valueを使う」「入力を多数照合した」だけを新規性としない。

## 一次資料

- **S1** Fukushima, Kiyomoto, Tanaka. *An Obfuscation Scheme Using Affine Transformation and Its Implementation*. IPSJ Digital Courier 2, 498–512, 2006. [本文](https://www.jstage.jst.go.jp/article/ipsjdc/2/0/2_0_498/_pdf)／[書誌](https://doi.org/10.2197/ipsjdc.2.498)。確認：§4.1–4.2、§7.2。
- **S2** Majumdar, Drape, Thomborson. *Slicing Obfuscations: Design, Correctness, and Evaluation*. DRM 2007. [著者公開本文](https://www.cs.auckland.ac.nz/~cthombor/Pubs/drm0127-majumdar.pdf)。確認：§4.3、§5.3–5.4、参考文献。最も直接的な領域別符号化の根拠。
- **S3** Drape, Thomborson, Majumdar. *Specifying Imperative Data Obfuscations*. ISC 2007. [著者公開本文](https://www.cs.ox.ac.uk/stephen.drape/papers/imp-specify.pdf)。確認：§2.2–2.3、§3.1、§5、付録A。
- **S4** [Tigress EncodeData公式文書](https://tigress.wtf/encodeData.html)。確認：導入例、奇数係数、符号化したままの演算。ツールそのものとの実測比較は未実施。
- **S5** [WebAssembly multi-value公式提案](https://github.com/WebAssembly/multi-value/blob/master/proposals/multi-value/Overview.md)。確認：Motivation、Examples、Validation。既存のloop引数とphiの対応。
- **S6** Caoほか. *WASMixer: Binary Obfuscation for WebAssembly*. [arXiv v1](https://arxiv.org/html/2308.03123v1)。確認：方式説明、§5.4の解析耐性の比較。刊行版の全文差分・全実装は未監査。
- **S7** Harnes, Morrison. *Cryptic Bytes: WebAssembly Obfuscation for Evading Cryptojacking Detection*. [arXiv v1](https://arxiv.org/html/2403.15197v1)。確認：変換種別、§5の評価。今回の方式と同一の実装がないという証明には使わない。
- **S8** Attiasほか. *Augmenting Search-based Program Synthesis with Local Inference Rules to Improve Black-box Deobfuscation*. CCS 2025. [著者公開本文](https://binsec.github.io/assets/publications/papers/2025-ccs.pdf)。確認：§5.2の補間とアフィン推論。今回の簡単な補間実験と同一条件の性能比較はしていない。
- **S9** Drape. *Intellectual Property Protection Using Obfuscation*. Oxford CS-RR-10-02, 2010. [本文](https://www.cs.ox.ac.uk/files/2936/RR-10-02.pdf)。補助資料として表現変更の枠組みを確認。
- **S10** Fukushimaほか. *Analysis of Program Obfuscation Schemes with Variable Encoding Technique*. IEICE E91-A(1), 316–329, 2008. [出版社ページ](https://globals.ieice.org/en_transactions/fundamentals/10.1093/ietfec/e91-a.1.316/_p)。書誌・要旨を確認。本文照合済みの扱いにはしない。

検索の範囲・未確認資料は `novelty-search-log.md` を参照。
