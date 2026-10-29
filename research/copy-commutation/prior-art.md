# copy成立条件の先行研究照合

2026-10-19。今回の結果は候補を除外・限定するための補題と実験であり、新しい保護方式の確立ではない。検索で見つからなかったことを新規性の根拠にはしない。

| 文献 | 区分・確認範囲 | 今回との関係・未確認事項 |
|---|---|---|
| Stephen Drape, *Generalising the Array Split Obfuscation*, Information Sciences 177(1), 202–219, 2007, [DOI 10.1016/j.ins.2006.03.012](https://doi.org/10.1016/j.ins.2006.03.012) | 査読誌。書誌は[著者ページ](https://www.cs.ox.ac.uk/people/stephen.drape/publications.html)で確認。[著者draft](https://www.cs.ox.ac.uk/stephen.drape/papers/draft-gensplit.pdf)のAbstract、§1–§3.3、§3.4冒頭を読んだ。最終版全体の精読ではない。 | 抽象データ型全体の表現と操作をdata refinementとして扱い、正当性の可換関係を使う。配列分割のリスト・行列への一般化。今回の「操作と両立する表現」という問題設定自体の先行性が強い。今回確認した範囲から、同一copy全族の分類が既発表とも未発表とも断定しない。実測の保護性能を本調査で再現していない。 |
| Jikai Wang, Ningyu He, Tianming Liu, Junhai Wang, Haoyu Wang, *NotDec: WebAssembly Decompilation With Inter-Procedural Type Recovery*, ICSE 2026, [DOI 10.1145/3744916.3787762](https://doi.org/10.1145/3744916.3787762), [著者版](https://arxiv.org/html/2608.03286v1) | 査読会議と2026年8月公開の著者preprintを区別。今回はAbstract・導入・背景を確認。既存調査は本リポジトリのliterature-reviewを参照。 | メモリアクセスからポインタ・構造体等を回復するため、表現変換の将来の比較対象。構造体アクセス回復85.33%は著者報告であり、こちらの独立測定ではない。今回NotDecは実行していない。copyの正しさから型回復耐性を主張しない。 |
| WebAssembly Community Group, *WebAssembly Core Specification 3.0*, 2026-10-13版, [memory.copyの実行規則](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy) | 言語仕様。memory.copy節の境界検査と両方向のコピー規則を読んだ。 | 重なり・ゼロ長・trapをモデル化する一次資料。難読化論文や性能評価ではない。 |
| James Bartusek, Yuval Ishai, Aayush Jain, Fermi Ma, Amit Sahai, Mark Zhandry, *Affine Determinant Programs: A Framework for Obfuscation and Witness Encryption*, ITCS 2020, LIPIcs 151, 82:1–82:39, [DOI 10.4230/LIPIcs.ITCS.2020.82](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ITCS.2020.82) | 査読会議。出版社の書誌とAbstractを読んだ。本文全体の確認ではない。 | 別方向の着想「行列式を計算表現にする」を先に調べた際の近い先行例。行列式の利用だけを新規原理として数えない。今回のcopy補題の先行定理と同一視しない。候補構成の暗号学的安全性を既成事実にしない。 |

今回の主要な差は、表現一般の提案ではなく、**操作を変えないという制限が表現をどこまで狭めるか**を式で確定し、任意byte copyと整列pair copyの境界を実Wasmで検査した点にある。これは研究上の設計判断には使えるが、既存のdata refinementを超える新規な難読化効果を示していない。補題の証明も初等的であり、既知の可換写像・自然性の議論の特殊化である可能性を排除できない。

検索語には `obfuscation memory.copy encoding`、`centralizer copy coordinate transformations`、`Generalising the Array Split Obfuscation` を使用。検索結果の不在は網羅調査の完了を意味しない。

関連特許の検索手掛かりとして [CN114021083B](https://patents.google.com/patent/CN114021083B/en) の行列式プログラム生成に関する記載と、[EP2831797B1](https://patents.google.com/patent/EP2831797B1/en) のデータ変換に関する検索索引を確認した。今回これらの全請求項を照合したとは記録しない。copyの成立条件をそのまま出願構成としない。特許の有効性・権利範囲・実施自由についての結論は出していない。

読めなかった資料：Carterの[著者PDF](https://www.cs.vu.nl/~herbertb/papers/carter_dimva14.pdf)は今回のopenが403だった。検索索引以上の内容を推測して補わない。Lambda Obfuscation等の検索手掛かりも今回の検証済み比較対象には数えていない。
