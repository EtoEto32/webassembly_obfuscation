# 中間状態・制御骨格・入出力合成に関する追加照合

2026-10-18。下記は確認した一次資料の範囲を記録する。著者の評価結果と、このリポジトリでの実行結果を混同しない。検索で同じ方式が見つからないことを新規性の証拠にはしない。

## Chisel

**Control-Flow Deobfuscation Using Trace-Informed Compositional Program Synthesis**。Benjamin Mariano, Ziteng Wang, Shankara Pailoor, Christian Collberg, Işıl Dillig。2024、PACMPL 8 (OOPSLA2)、Article 349、31頁、査読論文。[著者PDF](https://ziteng.wang/publications/oopsla24-chisel.pdf)、[DOI](https://doi.org/10.1145/3689789)。初回の文献表にあったBenjamin Marianoの欠落を訂正した。

表紙・要旨、§3.2、§4のトレースに基づく分割、§6の評価、§7の限界を確認した。元の実行が変換後のトレースからの削減で表せる制御フロー拡張を対象に、制御骨格と各基本ブロックを合成する。著者は6種の変換を組み合わせた546例の86%で、変数名を除き元に近いコードを得たと報告する。テストは一般の形式的同値性証明ではなく、トレースの網羅にも依存する。Chisel本体は未実行。

本研究への含意：中間状態を消すことでこの解析モデルの外へ出る可能性はあっても、別の代数的解析や入出力学習に強くなるとは限らない。今回の合成案についてChiselへの耐性を測ったとは主張しない。

## ASPIRE D2.01

**Early White-Box Cryptography and Data Obfuscation Report**。ASPIRE consortium、編集Mariano Ceccato。寄稿者Brecht Wyseur, Patrick Hachemane, Mariano Ceccato, Roberto Tiella, Jerome D’Annoville。2014、公開技術報告D2.01、v1.01、査読会議論文とは区別する。初版提出2014-10-31、v1.01改訂2014-12-10。[プロジェクト公開PDF](https://www.aspire-fp7.eu/sites/default/files/D2.01-ASPIRE-Early-White-Box-Cryptography-and-Data-Obfuscation-Report-v1.01.pdf)。

表紙・寄稿者・改訂履歴、§11.1.1–2、§11.1.5の微分攻撃を確認。多変数多項式の合成・分解を白箱保護に用いる方向を扱い、分解の非一意性と解除手法も議論する。該当節の著者はWyseurとHachemane。性能表の独立再現はしていない。体上の多変数分解と今回の `Z/(2^32)` 上の単変数反復は異なるため、攻撃の成立範囲を無条件に移さない。

本研究への含意：関数を合成して内部の分割を隠す一般発想は先行する。生成元の分解が一意に決まらなくても、別の短い分解があれば実用的な回復は成立し得る。[今回の係数攻撃](checkpoint-composition/README.md)の優先性・独立した学術的新規性は主張しない。

## XSmir

**Augmenting Search-based Program Synthesis with Local Inference Rules to Improve Black-box Deobfuscation**。Vidal Attias, Nicolas Bellec, Grégoire Menguy, Sébastien Bardin, Jean-Yves Marion。2025、ACM CCS、査読会議論文、15頁。[著者機関PDF](https://binsec.github.io/assets/publications/papers/2025-ccs.pdf)、[DOI](https://doi.org/10.1145/3719027.3765134)。

要旨・導入、実装、評価と限界の該当部分を確認した。探索へ定数・アフィン・多項式関係の推論規則を組み合わせるSmirを、Xyntia上にXSmirとして実装する。要旨では、難読化された実コード由来の式で76%、未難読化で84%を合成したと著者が報告し、比較先は63%と55%。この割合を今回のWasmの復元成功率と直接比較しない。文法制約と標本による誤一致の問題が残る。論文は[再現artifact](https://zenodo.org/records/17036259)を案内するが、本リポジトリでは取得・実行していない。

本研究への含意：限定した自作文法での探索失敗を、一般の合成困難性と扱えない。今回の5点補間は固定された低次数多項式に対する狭い解除であり、XSmirを再現したものではない。

## 未取得資料と選定判断

WAMO: Toward Secure Browser Inference via Web Model Obfuscation in WebAssembly（WWW 2026、DOI 10.1145/3774904.3792297）は追加の反証候補。ただし全文を取得できておらず、第三者の要約にあるアルゴリズムや評価値を確認済みの結果として転記しない。先行性の照合が終わったとは扱わない。

今回の2回合成は、汎用変換器を作る前の実Wasm検査で係数からも公開I/Oからも解除できた。中間状態が見えなくなるという性質を、保護効果の代替にしてはならない。WasmのGCや型・スタックの特性を用いる案も、公開APIからの復元と、小さい意味表現への正規化を先に検査する必要がある。独立した新規性と有効性の両立は引き続き未達である。
