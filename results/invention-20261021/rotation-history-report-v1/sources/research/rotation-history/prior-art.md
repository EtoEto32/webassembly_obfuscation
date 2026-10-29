# 先行性の照合

2026-10-21。今回の具体化はbit単位の可観測性と入出力実現に近い。一般原理を新発明としない。

| 文献 | 書誌・種別 | 確認した範囲 | 関係と限界 |
|---|---|---|---|
| [Observability of Nonlinear Dynamical Systems over Finite Fields](https://arxiv.org/abs/2404.02336) | Ramachandran Anantharaman, Virendra Sule、2024-04-02、arXiv2404.02336v1。査読掲載先は今回未確認 | [著者HTML](https://arxiv.org/html/2404.02336v1)の要旨、導入、§IIの定義 | 有限体上の非線形自律系を出力を生成する線形系へ移す枠組みと、観測からの初期状態回復を扱う。入力依存回転を含む本案の全入力の定理として流用しない。全証明・独立した実測は未確認 |
| [Discrete-time polynomial systems with inputs and outputs: structure, reachability, observability, and minimal realizations](https://arxiv.org/abs/2609.36423) | Eduardo D. Sontag、2026-09-29公開のpreprint。著者が1976年学位論文の更新版と説明 | 今回は書誌・要旨を再確認。過去の[確認範囲](../output-recurrence/prior-art.md)も参照 | 入出力差分式・観測による状態実現そのものは古い研究対象。無限体上の理論をword環・入力付きbit操作へ無条件に適用しない |
| [Duality of Linear Systems](https://mitter.lids.mit.edu/publications/70add_duality_linear_systems.pdf) | 検索書誌にFabio Fagnani、1994。完全な著者・出版先は未照合 | 著者機関PDFは取得できたがtext抽出は0行。本文未読 | 線形実現の追加照合先に留め、内容を新規性の判定根拠へ加えない |

検索は`linear systems finite fields observability realization input output`、`software obfuscation state elimination output history rotation`等。
同一の語が見つからないことは新規性の根拠にしない。公開特許の網羅調査・請求項対比は今回行っていない。

## リポジトリ内の先行試作との違い

[output-recurrence](../output-recurrence/README.md)は整数剰余環の商状態へ短く戻せた。
今回はその[rotate反例](../output-recurrence/extension.md)を踏まえ、合同類を保存しないbit回転で失われる情報を実際の観測履歴から補う。
固定回転で履歴を生成する具体則と、入力依存回転で任意の有限履歴長が不足する構成を追加した。
単なるbの変更ではないが、出力履歴へ移す一般方針を別の新発明として重複計上しない。

今回の固定回転系はGF(2)上の線形系であり、非線形な新規難読化原理ではない。
64回の公開問い合わせで規則を同定でき、履歴化による追加の保護利得を確認できなかった。
実装上の具体化や成立条件の整理は成果だが、それだけで既存理論から独立した新規性・特許性を認定しない。
