# 近接研究・公開特許との構成比較

確認日2026-10-18。検索語は `nondeterministic automata obfuscation state merging`、`automata obfuscation overlap states` など。一次本文で確認した範囲を記す。全文網羅、新規性・進歩性・他者権利との関係の法的判断を完了したという記録ではない。

|資料|書誌・読んだ版|今回確認した部分と関係|
|---|---|---|
|[Minimal Nondeterministic Finite Automata and Atoms of Regular Languages](https://arxiv.org/pdf/1301.5585)|Janusz Brzozowski / Hellis Tamm、2013、arXiv:1301.5585 v1。読んだ版はプレプリント|Abstract、§1–2、§4の反例、§5。複数quotientをNFA状態で共有する構成・非一意な最小NFA・coverの合法性検査が既知。重なりそのものは差分にならない。§5はKameda–Weinerの修正版概要なので、1970年原論文を直接精読したとは扱わない。|
|[Efficient Reduction of Nondeterministic Automata with Application to Language Inclusion Testing](https://homepages.inf.ed.ac.uk/rmayr/1711.09946.pdf)|Lorenzo Clemente / Richard Mayr、2019、Logical Methods in Computer Science 15(1), 12:1–12:73、[DOI](https://doi.org/10.23638/LMCS-15(1:12)2019)。査読誌版|Abstract、§1、§7.1末尾–7.2、§8冒頭。trim・商・pruning・saturation、NFA向けsimulationの区別、決定的な包含先では多項式検査が可能な点を確認。論文のHeavy-kは本実装より強い。論文の大規模評価を今回の生成族への攻撃結果に転用しない。|
|[Nondeterministic automata: Equivalence, bisimulations, and uniform relations](https://arxiv.org/abs/1102.5449)|Miroslav Ćirić / Jelena Ignjatović / Milan Bašić / Ivana Jančić、arXiv 2011。誌面メタデータはInformation Sciences 261 (2014) 185–218、DOI 10.1016/j.ins.2013.07.029|抄録確認。bisimulationによる比較・商は既知。本文の全アルゴリズムや評価を検証したとはしない。|
|[US11657127B2 — Hardware intellectual property protection through provably secure state-space obfuscation](https://patents.google.com/patent/US11657127B2/en)|掲載発明者 Md Moshiur Rahman / Abdulrahman Alaql / Swarup Bhunia。B2公開2023-05-23、A1公開2021-06-24。査読論文ではなく公報|掲載概要、明細書のFSM重畳部分、請求項1–17を確認。gate-level netlist、鍵入力、追加FSM、dummy FSM、誤鍵時の機能破壊を含む。今回の鍵を使わない言語保存NFA結合とは構成が異なるが、「補助状態機械を重ねる」一般論を発明とはできない。請求項18末尾と全図面の精読は未完了。|

公報の掲載statusから存続・権利範囲を確定しない。上表の違いは技術的照合であり、非侵害・特許取得可能性の結論ではない。

## 発明候補の構成対応

|構成要素|既知との対応|今回の差として検査した点|現時点の判断|
|---|---|---|---|
|DFAと全語を受理する補助NFAの積|標準の積・言語保存の性質|奇数cycleの等bit判定を補助NFA化|容易な恒真性の別実装。新規効果を示さない|
|状態同一視と、元DFAによる誤受理検査|NFA商・候補の合法性検査、決定的包含先|元プログラムを生成時oracleとして使う|実装できるが、それだけで新規とはしない|
|元状態の対応集合R(r)の重なりを最大化|複数quotientを同じNFA状態で表すことは既知|最小状態数の代わりに重なりを目的にした探索|無作為結合に対する保護費用の増分効果を支持しない|
|i64 localで到達集合を更新|標準的なbitsetによるNFA実行|実Wasmでの意味保存と費用測定|Wasmに移植したことは発明の核にしない|

検索不検出を先行技術不存在の証拠にしない。請求項案として権利化可能な構成を確定していない。実装・比較・反例を保存し、この限定案は主方式から外す。
