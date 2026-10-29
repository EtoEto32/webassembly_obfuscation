# 先行研究と主張できない部分

確認日2026-10-21。各資料の確認範囲を限定して記す。以下の既知構成を組み合わせただけで、新原理・初出・特許性を確定しない。

| 資料 | 書誌と読取範囲 | 提案・評価・今回との関係 |
|---|---|---|
| [Translingual Obfuscation](https://faculty.ist.psu.edu/wu/papers/to-eurosp16.pdf) | Pei Wang, Shuai Wang, Jiang Ming, Yufei Jiang, Dinghao Wu。EuroS&P 2016、査読会議。著者PDFの要旨、§3.1周辺、§7.3/Table 6を確認。発表先は[著者CV](https://faculty.ist.psu.edu/wu/wu-cv.pdf)の書誌でも確認 | BABELはCからPrologへの変換でunification/backtrackingを利用する。Table 6は条件によって大きなslowdownも示し、30%以上を変換したCPU主体例の高い費用を著者自身が論じる。10反復平均、serverは通信時間込み。計算モデルを変える難読化は既出。本案は探索なしのCNF単位伝播だが、この違いだけで独立性は確立しない。著者実装は未実行。 |
| [Inprocessing Rules](https://fmv.jku.at/papers/JarvisaloHeuleBiere-IJCAR12.pdf) | Matti Järvisalo, Marijn Heule, Armin Biere。IJCAR 2012、LNCS7364:355–370、査読会議。[大学の書誌](https://research.jku.at/en/publications/inprocessing-rules/)。要旨、§2の定義、§7のVE/Extended Resolution箇所を確認 | 全resolventによる変数消去と、substitution型との差を記載する。解の再構成や推論規則の正しさが対象で、Wasm難読化性能の論文ではない。本案のresolution規則は既知。前処理で推論能力を落とす危険も新発見とはしない。 |
| [Clause Elimination Procedures for CNF Formulas](https://www.cs.helsinki.fi/matti.jarvisalo/papers/heule-jarvisalo-biere.lpar10.pdf) | Marijn Heule, Matti Järvisalo, Armin Biere。LPAR-17、2010、LNCS6397:357–371、査読会議。要旨、BCP-preservanceの定義、Table 1、対応する反例箇所を確認 | 節除去の論理同値性・伝播保存・合流性を区別する。論理的に同じでも伝播能力は落ち得る。本案の負の対照はこの既知の区別を実装上確認するもので、新定理ではない。全文・全手法の再現はしていない。 |
| [CENSOR: Privacy-preserving Obfuscation for Outsourcing SAT formulas](https://eprint.iacr.org/2022/672) | Tassos Dimitriou, Khazam Alhamdan。ePrint2022/672。読んだ資料はプレプリントの書誌・要旨だけ。本文PDFは403で取得できず、査読版の内容は未確認 | SAT式の外部委託と入力・出力のprivacyを扱う。要旨にあるsecurityやslowdownの主張を、本案の保護効果へ転用しない。公開実行可能なWasm変換とは目標が異なるが、CNFを難読化へ使う一般発想は先行する。詳細な変換との一致・不一致は未判定。 |
| [Graph-Based Algorithms for Boolean Function Manipulation](https://ieee-ceda.org/media/graph-based-algorithms-boolean-function-manipulation) | Randal E. Bryant、1986、IEEE Transactions on Computers C-35(8):677–691。DOI 10.1109/TC.1986.1676819、査読誌。[著者書誌](https://www.cs.cmu.edu/~bryant/pubs.html)とIEEEの要旨・書誌を確認。今回全文は再読していない | 決定変数順序を固定したBoolean graph表現は既知で、最悪のサイズは指数的。本実験のROBDD構築やcanonicalな等価式への変換は発明として数えない。 |
| [WebAssembly Core Specification](https://webassembly.github.io/spec/core/bikeshed/) | 仕様。v128、iand/ior/ixor/ibitselectの定義を確認 | v128のbitwise演算で128個のBoolean評価をまとめることは公開仕様の直接利用。Wasmに実装しただけでは新規性にならない。他ISAにも同じ構成を移植できる。 |

検索語には `software obfuscation unit propagation`、`code obfuscation constraint propagation`、`obfuscation Tseitin`、`obfuscation variable elimination CNF` を用いた。別のSIMD最適化・符号化割当も探索したが、具体的な独立原理を得なかったものは新候補として数えない。

当初の差分候補は、入力・出力を残す射影を、伝播だけで停止する実行器と一緒に生成し、消去する変数を選ぶ手順だった。しかし現在の選択規則は既知のbounded variable eliminationに近く、Wasmの128-bit実装を越える独自性が弱い。公開I/Oからの回復も容易だったため、主発明としては採用しない。単に類似の題名が見つからなかったことを肯定的な新規性証拠にしていない。
