# 先行技術との照合と読了範囲

2026-10-23。一次資料だけを技術判断の根拠にする。検索不一致から新規性を推定しない。

|資料|発表・読んだ範囲|今回との技術的な関係|
|---|---|---|
|James Propp, **Discrete analogue computing with rotor-routers**, 2010, [arXiv:1007.2389v2](https://arxiv.org/abs/1007.2389)、関連掲載DOI [10.1063/1.3489886](https://doi.org/10.1063/1.3489886)|著者プレプリントの要旨、導入、§2.1を[HTML](https://arxiv.org/html/1007.2389v2)で読んだ。出版社本文への接続失敗。HTMLの再生成日を論文年と扱わない|訪問で回転する接続・ネットワーク計算・counterは既知。原論文の数値問題と今回の初期bitから終点を返す入力族は同じ仕様ではない。計算原理自体の新規性はない|
|Bernd Gärtner, Thomas Dueholm Hansen, Pavel Hubáček, Karel Král, Hagar Mosaad, Veronika Slívová, **ARRIVAL: Next Stop in CLS**, ICALP2018, 60:1–60:13, [DOI](https://doi.org/10.4230/LIPIcs.ICALP.2018.60)|査読会議。出版社書誌・要旨、PDF検索抽出のAlgorithm1、Definition1–3|二分岐の交互切替、終点判定、flowとparity証明は先行。今回の有限上限実行を、一般ARRIVALの未解決計算量と同一視しない。論文の全証明は未読|
|Sebastian Haslebacher, **ARRIVAL: Recursive Framework & ℓ₁-Contraction**, ICALP2025,95:1–95:17, [DOI](https://doi.org/10.4230/LIPIcs.ICALP.2025.95)|査読会議。[本文HTML](https://drops.dagstuhl.de/storage/00lipics/lipics-vol334-icalp2025/html/LIPIcs.ICALP.2025.95/LIPIcs.ICALP.2025.95.html)要旨、§1、§2の定義と検索抽出Theorem1まで|構造を使う解析と固定点化も既知。今回の小さいグラフに巨大な解析費用を期待する根拠にできない。全アルゴリズム未実装、性能比較未実施|
|Alexander E. Holroyd, Lionel Levine, Peter Winkler, **Abelian logic gates**, Combinatorics,ProbabilityandComputing28(3):388–422,2019, [DOI](https://doi.org/10.1017/S0963548318000482)|査読掲載書誌は前回確認。[著者版](https://lionellevine.github.io/abelian-logic-gates.pdf)は2018-04-09改訂。今回はpp1–5の導入、Theorem1.1–1.3、Proposition1.4まで読んだ|単純な状態付きgateの合成、rotorのemulationは既知。論文は粒子数を入力とするprocessorで、初期switch状態を入力とする今回の族へ単調性を無条件に転用しない。今回のmuxは選択bitに関してunateではない|
|Sumit Gulwani, Susmit Jha, Ashish Tiwari, Ramarathnam Venkatesan, **Synthesis of Loop-Free Programs**, PLDI2011, [著者機関ページ](https://www.microsoft.com/en-us/research/publication/synthesis-loop-free-programs/)|査読会議。[著者PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/pldi11-loopfree-synthesis.pdf)の検索抽出要旨・§1を読んだ|入出力の関係から構成要素をSMT合成する一般原理は既知。今回の各switch反復は固定Bで展開できる。「全体合成する」ことだけを新規性の核にできない|
|Susmit Jha, Sumit Gulwani, Sanjit A. Seshia, Ashish Tiwari, **Oracle-Guided Component-Based Program Synthesis**, ICSE2010, [DOI](https://doi.org/10.1145/1806799.1806833)|査読会議。[著者機関PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/icse10_synthesis.pdf)検索抽出の要旨・導入|入出力から簡潔な実装を回復する評価側の原理も既知。今回の全8入力/BDD回復は新しい汎用解析手法という主張ではない|

検索語：`rotor obfuscation program`、`switching graphs obfuscation`、`rotor router Boolean circuits`、`rotor-routing program synthesis`、`rotor Boolean functions`。暗号機Enigmaや無関係な企業名の結果は採用しなかった。固有の難読化用生成特許を網羅した調査ではなく、特許性の肯定・否定の法的結論を出していない。

今回との差分候補は、各入力bitを初期switchへ配置した有限終点計算を、元関数全体の真理値表から直接合成し、32 laneをWasmへ下ろす具体的な構成である。しかし有限仕様合成と既知rotor計算を超える非自明な生成規則、広い関数族への構成定理、保護上の費用対効果を確認できなかった。現状で独立した新規発明とは認定しない。

併行してメモリ/トラップ方向も既存のwrite-frontier、trap-carrier、difference-boundaryと照合し、単なる再提案を避けた。WAMO(WWW2026、DOI10.1145/3774904.3792297)は書誌が既に保存済みで、今回も出版社本文を取得できていない。第三者の要旨転載だけで未読の詳細を補ってはいない。
