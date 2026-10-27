# 可逆混合・局所更新に関する先行性の確認

調査日2026-10-19。これは今回の候補に絞った追補で、[全体の文献調査](../literature-review.md)を置き換えない。書誌、読んだ範囲、実測との境界を記す。特許性や権利範囲についての法的判断は行っていない。

| 文献 | 種別・書誌と読了範囲 | 今回への含意 |
|---|---|---|
| Reversible Circuit Rewriting with Simulated Annealing | Nabila Abdessaied, Mathias Soeken, Gerhard W. Dueck, Rolf Drechsler. VLSI-SoC 2015, pp.286–291。査読会議論文。[著者PDF](https://msoeken.github.io/papers/2015_vlsisoc.pdf)、[DFKI書誌](https://www.dfki.de/web/forschung/projekte-publikationen/publikation/7888)。要旨、定義、moving ruleとextended moving rule、書換え手順を確認。 | control/targetに基づく交換と回路書換えは先行する。著者は回路の量子コスト削減を報告しているが、今回その結果を再現していない。Wasmの不可逆更新への適用を同論文の新規性欠如と断定するのでなく、一般的な交換・相殺を自分の発明に数えない。 |
| Encrypted Operator Computing: a novel scheme for computation on encrypted data | Claudio Chamon, Jonathan Jakes-Schauer, Eduardo R. Mucciolo, Andrei E. Ruckenstein. arXiv:2203.08876、2022、v2は2022-11-11。[書誌](https://arxiv.org/abs/2203.08876)、[本文](https://arxiv.org/html/2203.08876v2)。プレプリント。要旨、共役構成、§5.1–5.2のgate書換えとBDD表現を確認。 | E F E^-1の形、線形・非線形回路による変換、control/targetの重なりに応じた書換えが非常に近い。安全性は論文の仮定を含む構成で、今回の公開係数のSIMDコードに転用できない。Wasmで動いたという差だけでは独立した発明根拠にならない。 |
| Encrypting data based on linear 3-bit gates and non-linear gates | 発明者Claudio Chamon, Jonathan Jakes-Schauer, Andrei Ruckenstein。Usencryption Inc。WO2023077167A1、優先日2021-11-01、公開2023-05-04。[公報](https://patents.google.com/patent/WO2023077167A1/en)。要旨、関連説明、請求項1と2–10、対応する媒体請求項を確認。 | 請求項1は線形/非線形段、元gateを挟む変換、置換によるdaughter gate、BDDからのmodule chip生成等を列挙する。今回のコードはその二段構成・BDD chipを実装していないが、表現変換で処理を挟む一般着想は重なる。未読のfamily各国請求項・審査経過を含む網羅調査ではない。 |
| Towards General-Purpose Program Obfuscation via Local Mixing | Ran Canetti, Claudio Chamon, Eduardo R. Mucciolo, Andrei E. Ruckenstein。TCC 2024、LNCS15367、pp.37–70。会議は2024、出版社は2024-12の公開と2025のcopyrightを記載。[会議録](https://link.springer.com/book/10.1007/978-3-031-78023-3)、[ePrint 2024/006](https://eprint.iacr.org/2024/006)。査読会議版の存在を確認。今回読めた内容はePrint書誌・要旨のみで、PDF取得は失敗。 | 可逆回路の機能保存局所摂動を使う難読化候補と仮定付きの理論を扱う。読めていない具体的摂動手順や実験結果を推測しない。局所混合そのものを未開拓と主張することへの反証資料。 |
| Qiskit CommutativeCancellation | IBM公式[API資料](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.passes.CommutativeCancellation)。実装資料、2026-10-19参照。 | 交換を利用した自己逆gateの相殺は既存最適化器にもある。量子向けpassを今回のWasmにそのまま実行したわけではない。 |

今回独自に実装・計測した対象は、返り値を伴うprivateなWasmレコード更新で、readだけの干渉をwriteの伝播と区別する計画である。これが既存依存最適化から容易でない差に当たるとの根拠はまだない。最大のReject理由は「既知の回路共役と依存解析の適用で、保護効果を追加で示せていない」ことである。

検索は上記タイトルのほか、`reversible circuit obfuscation conjugation cancellation`、`read write obfuscation reversible cancellation`、`conjugation obfuscation light cone`等で、肯定例だけでなく近似技術を探索した。検索で見つからないことを新規性の証明にしない。EOCの特許・論文は目的が暗号計算でも技術的先行性の比較対象となる。今回の目的を暗号化へ変更する理由にはしない。
