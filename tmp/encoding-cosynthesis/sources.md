# 先行研究との照合

確認日2026-10-12。検索で未発見を未発表の証明としない。

## データ表現の正しさは既知

Design and Evaluation of Slicing Obfuscations、CDMTCS-311。本文§3.2–3.3、§8.2–8.4を確認。抽象化関数・変換関数と可換関係、領域ごとの符号化、境界変換の結合が既に説明されている。本候補のD(E(x))=xや更新可換条件を新規性として数えない。この記録では刊行年を推測せず、レポート番号で同定する。
https://www.cs.auckland.ac.nz/research/groups/CDMTCS/researchreports/311stephen.pdf

## 敵対的な変換選択も既知

Generating Adversarial Computer Programs using Optimized Obfuscations、ICLR2021。本文§3–4を確認。位置と変換を同時に最適化する定式化・一次最適化がある。実験対象は学習モデルへのsource token変換で、今回のWasm状態遷移の同時合成と同一ではない。ただし「解析器の失敗を目的に変換を選ぶ」だけでは独自性の根拠が弱い。本文のprint挿入に関するsemantics記述を、外部出力も保存する本研究の意味保存定義に転用しない。
https://arxiv.org/pdf/2103.11882

## 等価式の複雑化も既知

Scrambler: Mixed Boolean Arithmetic Obfuscation Tool Using E-graph and Equality Expansion、arXiv:2603.03624v1、2026-03-04。HTML本文§3–5、Table1を確認。eggと等価書き換えで式を展開し、サイズや時間等の条件で抽出する。掲載実験の主な指標は構造上の複雑さ。これを解析耐性の実証とは読み替えない。本候補は途中の復元成功を制約へ戻す点を検討するが、その差が新しい一般的手法だと確定したわけではない。著者コード・査読採録状況は未確認。
https://arxiv.org/html/2603.03624v1

## 学習妨害の資料：本文確認の追補

Executable but Unlearnable: Designing Code that Resists LLM-Based Learning。以前のOpenReview閲覧はブラウザ確認画面へリダイレクトし、本文未確認だった。2026-10-12の再確認でも同じ画面になったが、著者Reza M. Pariziが公開した別の本文を閲覧できた。旧時点の未確認という記録と、今回の確認範囲を区別する。
https://openreview.net/attachment?id=VxJW8QE9zK&name=pdf

確認した一次資料：

- [著者公開本文](https://www.researchgate.net/publication/408477049_Executable_but_Unlearnable_Designing_Code_That_Resists_LLM-Based_Learning)。著者投稿表示は2026-07-05。HTML抽出の§2–7.1と参考文献[21]を読んだ。PDFファイルの取得・版間差分の検証はしていない。
- [会議公式ページ](https://2026.aiwareconf.org/details/aiware-2026-papers/11/Executable-but-Unlearnable-Designing-Code-That-Resists-LLM-Based-Learning)：AIware 2026、著者名、DOI 10.1145/3805760.3814896を確認。
- [著者リポジトリ](https://github.com/dslmllab/Statistical-Opacity)：READMEと4個のnotebookの存在を確認。notebook本文の監査、実行、結果再現は未実施。

本文の範囲：§2は変換済みコードを含む学習コーパスによる汎化性能を対象とする。§7.1の試作は識別子変更、for→while、恒真・恒偽条件による包囲。本文はper-token perplexityの比較を述べ、全手法の合成は識別子変更単独より小さい効果だったと報告する。独立再現はしていない。

本研究の判断：学習分布への影響と、命令意味・動的値を利用した対象固有の状態の対応の復元は別の測定対象である。この資料だけでは後者の耐性を支持しない。上記3変換をWasmへ移植しても、本目標で要求する独立した構成原理にはならない。さらに本候補のE/D/U同時合成や復元導出の一般化規則は、この資料の確認だけでは完成しない。新方式として採用せず、文献上の比較対象（再利用分類C）とする。学習妨害の全方式が無効という結論ではない。

今回の検索語：`"Executable but Unlearnable" obfuscation`。探索範囲はこの未確認資料の本文と著者リポジトリ所在の確認に限定。新しい変換器・SHA実験・攻撃比較・性能測定・Before/After生成は実施していない。研究目標は未達成のまま継続する。

## 追加検索と残る課題

### 学習と難読化の定理を転用できる範囲

2026-10-12、前項の引用元を追加確認。Boyle, Ishai, Meyer, Robere, Yehuda, **On Low-End Obfuscation and Learning**, ITCS 2023。検索語：`"On Low-End Obfuscation and Learning" pdf`。DOI転送先は取得できなかったが、[刊行版PDF](https://drops.dagstuhl.de/storage/00lipics/lipics-vol251-itcs2023/LIPIcs.ITCS.2023.23/LIPIcs.ITCS.2023.23.pdf)は閲覧できた。確認範囲は導入、§3のTheorem 11の証明、Definition 12、Theorems 13–14と証明、Corollaries 15–16、Theorem 17周辺。全28ページの通読・著者実装の再現ではない。

Theorem 14は、誤り回数の上限Mを持つ効率的学習に加え、対象クラスの等価性問い合わせを多項式時間で実装できることを仮定する。証明では辞書順最初の反例を返すよう問い合わせを揃える。結論は同じ機能のプログラムを共通の表現へ写すcanonical obfuscationであり、復元器に学習させないという結論ではない。

本候補への適用判断：有限の復元文法で候補を排除できたことから、この定理の学習条件や等価性問い合わせの計算量条件は導けない。また、意味的正準化が元の構文由来の情報を消しても、本研究で求める状態の対応の復元時間の増大は別途必要である。したがって本定理を新しい生成原理やSHA-256耐性の証明として採用しない。一方、あらゆる学習利用の生成方式が既知・無効であるとも結論しない。再利用分類C。今回の追加確認による実装・攻撃実験・性能測定はない。

QSynth/LOKIは既存の候補監査記録を参照。CEGISそのものや、プログラム合成そのものを新しい方式として提案しない。

検索語：obfuscation synthesis counterexample guided data encoding representation / adversarial program synthesis obfuscation superoptimization encoding / obfuscation counterexample-guided synthesis / obfuscation synthesizing encodings / data obfuscation synthesis encoding / obfuscation state encoding synthesis software / obfuscation commuting encoding synthesis / obfuscation encoding CEGIS / obfuscation automatic generation e-graph。

現状の判断：単純な自動複雑化案は不採用。具体的な生成規則は未確定。以下の追補により、E/D/Uの同時合成という問題設定自体も新規性の根拠から除く。

## 同時合成そのものとの直接的な重複

2026-10-12。Wang, Wang, Dillig, *Relational Program Synthesis*, OOPSLA 2018、DOI 10.1145/3276525。[著者公開PDF](https://www.cs.utexas.edu/~isil/relational-synthesis.pdf)の導入、Definitions 2.1–2.2、Example 2.3、Algorithm 1と§5冒頭、§5.3冒頭を確認。全文通読・Relish実装の再現はしていない。検索語：`program obfuscation synthesis relational invariants implicit encoding`。ローカルMarkdownを題名・DOI・arXiv番号で検索した範囲には既存の記録がなかった。

複数の未知関数を関係仕様から合成する枠組みで、符号化・復号の同時合成を例示する。関数の各出現へ独立した実装を割り当てる緩和と、同一関数としての整合性を回復する探索を区別する。これをWasm対応済み、または難読化耐性の方式とは扱わない。

本設計への照合（以下は本研究側の推論）：`D(E(x,r))=x` と `I(z) => (D(U(z,u))=T(D(z),u) and I(U(z,u)))` は、複数未知関数の関係仕様である。既存の関係合成を使ってこの条件を満たすだけでは、独立した生成原理にならない。

また、固定した有限個の復元式 `d_j` を全入力で正しい復元器にしない、という条件は、各jについて合法な証人 `(z_j,u_j)` を選び `d_j(O_U(z_j,u_j)) != D(z_j)` を要求する形になる。固定長の純粋な更新文法で、`O_U` が同じUの構文から確実に生成され、合法性が正確に表現できる場合、証人を合成対象の定数として追加した関係制約にできる。独立した観測関数を自由に合成して偽のtraceを作ってはいけない。到達可能性を過大近似したIだけでは証人の実行可能性は保証されない。この対応は定式化上のものであり、Relishがそのまま処理できる、効率的に解ける、将来の個別生成アルゴリズムがすべて既知、という主張ではない。

判断：同時合成と有限復元式の不一致制約だけを新方式として実装し直さない。新しい構成規則の裏付けは得られなかった。分類C。今回のWasmの生成・実行・SMT・最適化・攻撃試験はなし。
