# 先行技術との照合

確認日2026-10-19。検索不検出を新規性の証明にはしない。技術的な比較であり、権利範囲・存続・特許取得可能性の法的判断を完了したものではない。

|資料|書誌・確認範囲|今回との関係・限界|
|---|---|---|
|[An FSM Re-Engineering Approach to Sequential Circuit Synthesis by State Splitting](https://user.eng.umd.edu/~gangqu/promotion/paper3.pdf)|Lin Yuan, Gang Qu, Tiziano Villa, Alberto Sangiovanni-Vincentelli。IEEE TCAD 27(6), 1159–1164, 2008、DOI 10.1109/TCAD.2008.923245。査読誌の著者版。Abstract、§I、§IVとFigure 6を確認。[大学の記録](https://drum.lib.umd.edu/items/3cb0bf41-b8f9-46b9-8eeb-6f34092aaec8)でも2008を確認|同値な状態を増やし、incoming edgeの行先と符号を変更することは既知。目的は回路の電力・面積であり難読化ではない。著者版はMCNC91で平均5.5%電力低下、1.3%面積増・1.3%delay増などを報告。今回この数値を再現していない。今回の均一複製・置換による構成を、それだけで独立の発明と認定する根拠は弱い。|
|[An n log n Algorithm for Minimizing States in a Finite Automaton](https://www.cs.cmu.edu/~cdm/resources/Hopcroft1971.pdf)|John Hopcroft、Stanford technical report STAN-CS-71-190、1971。読んだ版は技術報告。Abstract、Introduction、formal algorithm、correctness、runtime節を確認|状態表から同値類を求める古典的解析。O(kn log n)のkはalphabetに依存。今回の単純分割改良はこの高速実装の再現ではない。大きな表を与えたときの全状態解析の測定だけでは最良攻撃費用にならない。|
|[Learning Regular Sets from Queries and Counterexamples](https://swt.informatik.uni-freiburg.de/teaching/WS2019-20/AutomataTheory/Learning%20Automata%20%28Caveat%20not%20related%20to%20Machine%20Learning/at_download/file)|Dana Angluin、Information and Computation 75(2), 87–106, 1987、DOI 10.1016/0890-5401(87)90052-6。査読誌版PDFを大学掲載先で確認。Abstract、§2.1–2.2/Figure 1、§4.1を確認|membershipとequivalence queryによる学習。今回は観測表の構成を使うが、等価性oracleを有限テストへ置換した。一般の完全回復保証は適用しない。物理状態数だけを拡大しても公開出力の区別が変わらない点を評価する先行基盤。|
|[IP protection through gate-level netlist security enhancement](https://www.jinyier.me/papers/Integration16.pdf)|Travis Meade, Shaojie Zhang, Yier Jin、Integration 58, 563–570, 2017、DOI 10.1016/j.vlsi.2016.10.014。査読誌版。Abstract、§2概要、§5.1–5.5を確認|REFSMによる回復とREHOPによる状態拡大を扱う。鍵入力、penalty/black-hole mode、scan chainを含むhardwareモデルで、全入力の言語を保存する今回とは異なる。小例の約6千万test vectorという報告をWasmの保護効果へ転用しない。論文自身もtableの自由度とサイズの問題を議論。|
|[US11657127B2](https://patents.google.com/patent/US11657127B2/en)|Md Moshiur Rahman / Abdulrahman Alaql / Swarup Bhunia。B2公開2023-05-23。公開公報。前回の[照合記録](../overlap-automata/prior-art.md)に加え、今回はAbstractと独立請求項1を再確認|gate-level netlist、key、control/pseudo-state elements、追加FSMとmux、誤key時の機能破壊を含む。今回にはkey/lockingがなく言語を保存するが、「状態を増やす」一般論を新規とはできない。この違いだけで取得可能・非侵害とは判断しない。|

探索語は `automata obfuscation state splitting`、`state replication software obfuscation patent`、`learning regular sets queries counterexamples` など。US7430670B2は検索候補に上がったが本文openが失敗したため請求項を読了したとは扱わない。関連特許を網羅できたとも主張しない。

## このターンで先に退けた方向

可逆回路の局所混合は[Canettiの2025年講演](https://simons.berkeley.edu/talks/ran-canetti-boston-university-2025-06-23)の抄録にも存在した。さらにTQC2014の[Circuit Obfuscation Using Braids](https://drops.dagstuhl.de/storage/00lipics/lipics-vol027-tqc2014/LIPIcs.TQC.2014.141/LIPIcs.TQC.2014.141.pdf)と関係するため、「可逆回路化して局所変形する」一般案は新発明として進めなかった。ここでは2025講演の抄録確認であり、その論文の証明全体を検証した記録ではない。

採用の最大の障害は、状態分割・表駆動・商回復という既知の構成に対して、新しい具体規則の追加効果を示していないこと。今回の費用測定は有用な反証だが、このまま特許請求の主構成を確定しない。
