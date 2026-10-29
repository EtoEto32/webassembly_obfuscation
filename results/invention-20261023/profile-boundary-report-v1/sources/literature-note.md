# 調査と候補選別の追補（2026-10-23）

## 確認できた一次資料

- Guan-Yan Yang, Tsung-Han Liu, Farn Wang, Kuo-Hui Yeh, **Class-based Obfuscation with Multi-objective Evolutionary Algorithms on Source Code**, International Journal of Information Security 25, article167, 2026-09-23。査読論文。DOI [10.1007/s10207-026-01297-z](https://link.springer.com/article/10.1007/s10207-026-01297-z)。出版社の要旨、Introduction、手法冒頭、§6を読んだ。クラス操作と多目的探索をPythonに適用し、構造指標と実行費用を評価する。著者自身が構造指標は解析耐性の直接測定ではないこと、15個の小プログラム、テストに限られた正当性、他言語への未検証を述べている。実装や結果表全体を再現・精査したものではない。Wasmへ探索器を移植するだけを独立原理とは数えない。
- Neil D. Jones, **Lecture 4 on Obfuscation by Partial Evaluation of Distorted Interpreters**。[著者講義資料・NII掲載](https://www.nii.ac.jp/userimg/lectures/neiljones/TokyoSlidesObfuscation.pdf)。共著研究者としてRoberto Giacobazzi, Isabella Mastroeniを記載。今回読んだ範囲はpp.1–10の生成・意味保存・部分評価の説明。年・講義の査読状況は資料冒頭から確定せず、査読論文として登録しない。評価器の様式を残す部分評価は既知の方向であり、別の評価器を使うだけでは新規な生成規則の証拠にならない。Wasmの実験結果はこの資料から主張しない。

## 本文未確認の調査項目

**Code obfuscation based on deep integration**, Xiaobing Xiong, Zihan Sha, Hui Shu, Ran Wei, The Computer Journal68(12),1980–1995,2025。DOI [10.1093/comjnl/bxaf089](https://doi.org/10.1093/comjnl/bxaf089)。出版社の号目次で著者・題名を確認したが、論文ページは今回の取得で失敗した。二つのプログラムのIR統合という説明は二次索引の要旨で見た段階で、具体手順・数値・本研究との差を本文から確認できていない。先行性の確認が必要な項目として保持し、読んだ論文の技術的事実には加算しない。

検索では、`obfuscation abstract interpretation compiler data representation`、`Code obfuscation based on deep integration pdf`、`obfuscation tropical/min-plus/max-plus`なども用いた。熱帯/飽和min-plus方向はリポジトリ内の[saturating-frontier](../saturating-frontier/README.md)と重複するため、新しい別原理の案として再計上しなかった。検索で一致が見つからないことを、新規性の証明に使わない。

## 今回の研究判断

新しい候補を完成したとは記録しない。計算形式の変更には既知の枠組みが多く、今回は独立した具体生成規則を選定できなかった。一方、専用解除器が形式未対応を返すだけの状況は、既存案の変種と実Wasmで確認・改善できた。今後は生成器への設定追加だけで有効性を判断せず、複数の異なる元プログラムと、候補の意味を知る解析を用いる。発明の目的は引き続き、既存技術に対して説明可能な具体的差と、有用な実測効果を持つ難読化である。
