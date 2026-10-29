# 先行研究と差分の範囲

2026-10-22。今回の対象は、実行中の状態から混合係数を計算しても、所定の有限回で元の計算結果を得られる変換である。残差反復、状態依存の前処理、一般の収束原理そのものを新規と主張しない。

| 資料 | 種別・確認範囲 | 今回の候補に対する含意 |
|---|---|---|
| Alexander J. T. Gurney, *Asynchronous iterations in ultrametric spaces*, arXiv:1701.07434, 2017, [原文](https://arxiv.org/pdf/1701.07434), DOI 10.48550/arXiv.1701.07434 | プレプリント。Abstract、Introduction、§2.1のDefinition 4・Theorem 1、§2.2冒頭を確認。PDF本文の日付は2021-08-07、arXiv登録は2017-01-25。査読済み発表先は未確認 | 正解を含む入れ子の直積集合へ更新が進む既知の収束条件を説明する。今回の重み付き付値による根への下降も、この枠組みで表せる。一般収束定理の独立した新規性を主張する根拠にならない |
| Firedrake, *Preconditioning infrastructure: Nonlinear preconditioning*, [公式文書](https://www.firedrakeproject.org/preconditioning.html#nonlinear-preconditioning), 2026-10-22閲覧 | 技術文書。当該節を確認 | Richardson型の残差更新と、前回状態に依存する非線形前処理を説明する。「状態依存係数を使った反復」という広い発想は差分として不十分 |
| Adrián Ranea, Joachim Vandersmissen, Bart Preneel, *Implicit White-Box Implementations: White-Boxing ARX Ciphers*, CRYPTO 2022, LNCS 13507, pp.33–63, DOI 10.1007/978-3-031-15802-5_2, [原文](https://crypto.iacr.org/2022/papers/530630_1_En_2_Chapter_OnlinePDF.pdf) | 査読済み会議論文。今回の確認はAbstract・Introduction・貢献の説明。全証明を今回読んだとはしない | 関係式による暗黙的実装とself-equivalenceの既存研究。計算を関係式へ移す一般論は新規ではない。今回の試作は暗号鍵のwhite-box安全性を主張しない |

GurneyのTheorem 1はさらに先行文献[23]へ証明を参照している。今回その原典の全文を確認していないため、Gurney自身がnested-box条件を初めて提案したとは記述しない。今回の条件と既存定理との対応は本研究側の分析である。

## 残る具体的な差分候補

[以前の定数行列分類](../../experiments/sha256-fixedpoint/mixer-classification.md)は、元の依存順序を固定した全ての厳密三角・合同保存写像に対し、全初期状態から収束する定数行列の必要十分条件を扱う。今回は、同じ偶奇条件を全状態で満たす任意の全域関数M(v)について、十分性を根との距離だけから示した。係数内のrotlが二状態間の合同関係を壊しても保証が成り立つ。

したがって差分を検討できる場所は、**元の依存順序から許容される係数関数と有限回の実行を生成する具体的な手順**に限られる。定数分類を任意の状態依存行列の必要十分分類へ拡張したとは言わない。Wasmの固定語長演算・rotlを使うが、Wasmだけに成立する原理でもない。

既存の一般理論の直接的な応用と評価される可能性があり、独立した新規性は未確立である。さらに今回の係数生成族では専用の係数射影が全18解析条件を回復した。構成の自由度を増やしたことと、保護上の技術的効果を増やしたことは別に評価する。

関連検索ではultrametric/paracontraction、p-adic/state-dependent iteration、state-dependent preconditioner/fixed point、finite-ring residual obfuscation、nested boxesを調べた。検索一致の不存在を新規性の証拠とはしない。特許請求項・ファミリーを網羅した調査や法的な特許性判断は今回の成果に含まれない。
