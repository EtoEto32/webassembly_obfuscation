# 近接研究と新規性の反証

調査日2026-10-22。以下は本文の指定箇所を実際に確認した。特許公報全体の網羅調査や法律上の新規性判断ではない。

| 文献 | 年・発表先・扱い | 確認箇所と技術的な関係 |
|---|---|---|
| Aaron Mishkin, Arda Sahiner, Mert Pilanci, *Fast Convex Optimization for Two-Layer ReLU Networks: Equivalent Model Classes and Cone Decompositions* | 2022, ICML / PMLR 162、査読済み。[本文](https://proceedings.mlr.press/v162/mishkin22a/mishkin22a.pdf) | §2.1のactivation cone、Appendix AのTheorem 2.1証明（PDF p.16）。同一patternの係数和が予測を保存するmergeを明示。今回の同符号混合・集約に最も直接に近い。 |
| Yifei Wang, Jonathan Lacotte, Mert Pilanci, *The Hidden Convex Optimization Landscape of Regularized Two-Layer ReLU Networks: an Exact Characterization of Optimal Solutions* | ICLR 2022、査読済み。[会議版へのリンク](https://openreview.net/pdf?id=Z7Lk2cQEG8a)、[実際に閲覧できた著者公開版](https://arxiv.org/pdf/2006.05900) | 公開版の表紙にICLR 2022掲載と記載。§3.1はsplitting/merging、§4.1は同一cone内の係数の整列による予測保存。全最適解の特徴付けが提案であり、Wasm難読化の論文ではない。OpenReview直読はchallengeで止まり、別の公開arXiv版で確認した。 |
| Yifan Yan, Xudong Pan, Mi Zhang, Min Yang, *Rethinking White-Box Watermarks on Deep Learning Models under Neural Structural Obfuscation* | 2023, USENIX Security、査読済み。[本文](https://www.usenix.org/system/files/usenixsecurity23-yan.pdf) | 表紙・§6.2を確認。NeuronClique/NeuronSplitは同一incoming weightsを持つchannelを作り、outgoing weightsの和で寄与を制御する。今回の非比例な係数という差だけで全研究に対する新規性は得られない。実験全体の数値は本追補では再評価しない。 |

Mishkinらは有限データ行列X上でactivation patternを定義し、そのpatternを持つ重みのconeを扱う。今回の有限格子Dも、その全点を行として並べれば有限データ行列にできる。従って「全実数ではなく有限入力で一致する」「非比例でも同じpatternとなる」という特徴だけで既存の枠組みから離れたとはいえない。これは先行研究の数式と今回の構成を対応させた、本研究側の推論である。

残る実装上の限定差は、整数unimodular混合で逆を整数に保ち、signed overflowを検査し、WasmのSIMD定数へ吸収する手順。ただし、この組合せに独立した非自明性や保護効果があることは示せていない。最も大きなReject理由は、既知のactivation cone内の変換を限定領域へ適用した実装と評価されることである。

評価の目的も区別する。Mishkinらは学習の凸最適化とMNIST/CIFAR-10等の実験、Wangらは最適解の理論的特徴付けが中心であり、本実験の難読化回復費用とは異なる。こちらの実験は3合成関数のみで、学習済みモデルへの有用性・元論文の学習性能・ウォーターマーク除去性能を検証していない。

## 未読・未確定

*WAMO: Toward Secure Browser Inference via Web Model Obfuscation in WebAssembly*（WWW 2026、[DOI](https://doi.org/10.1145/3774904.3792297)）の本文取得はできていない。検索情報や第三者要約をアルゴリズム比較の根拠にせず、WAMOと異なることを確認済みとしない。

*Hidden Symmetries of ReLU Networks*のOpenReview本文もchallengeで取得できず、詳細比較には使わない。特許US20240078308A1は探索の手がかりに留まり、請求項の充足・非充足を判断していない。

今回の結論は「同一のWasm変換が過去に存在したことを証明した」ではなく、「最初に新しさの核と想定した数学的関係には近い既存技術があり、残る実装差の効果も未確立」である。
