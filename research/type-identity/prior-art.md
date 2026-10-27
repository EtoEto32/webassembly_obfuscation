# 型同値状態の先行研究照合

2026-10-19。調査・確認した範囲を明記する。今回の方式は主発明として不採用。文献未発見を新規性の根拠にしない。

| 資料 | 書誌・区分・読んだ範囲 | 提案・評価・今回への含意 |
|---|---|---|
| *GC v1 Extensions*, WebAssembly Community Group | [公式proposal](https://github.com/WebAssembly/gc/blob/main/proposals/gc/MVP.md)。標準化資料、査読論文ではない。Types、Type Definitions、Equivalenceとその注記を確認。対応する[Core 3.0型規則](https://webassembly.github.io/spec/core/valid/types.html)も参照。 | group内位置とrollingによる同値性は既知。事前のbottom-up canonicalizationで効率的に比較できることまで明記される。「再帰型だから同値判定が難しい」という説明はこの資料に反する。性能の独立再現をしたのではなく、今回の実験で既存Binaryen readerを攻撃に利用した。 |
| Andy Wingo, *nominal types in webassembly* | [著者ブログ](https://wingolog.org/archives/2026/03/10/nominal-types-in-webassembly)、2026-03-10。技術解説。記事全文を確認。 | 同じ形のstructでもgroup内の別位置では区別され、別module/groupに同じ構造を作れば同値になり得ることを説明。今回の核となる型identityの利用にはこの直接的先行性がある。後半の「nominal typing proposal」という呼び方は例外tagを使った冗談を含む説明であり、別の新標準が成立した根拠にはしていない。 |
| Christophe Foket, Bjorn De Sutter, Bart Coppens, Koen De Bosschere, *A Novel Obfuscation: Class Hierarchy Flattening* | FPS 2012会議、2013年刊行、LNCS 7743, pp.194–210、[DOI 10.1007/978-3-642-37119-6_13](https://doi.org/10.1007/978-3-642-37119-6_13)。査読論文。[機関書誌](https://biblio.ugent.be/publication/3228461)、[著者PDF](https://users.elis.ugent.be/~brdsutte/research/publications/2012FPSfoket.pdf)の要旨・§1–2・§4.2を確認。全節の精読ではない。 | Javaの型階層を平坦化して設計情報を隠す。DaCapoでQMOOD指標・points-to集合・費用を評価。多くの例の定常実行overheadは10%未満と著者報告。人の実際の解除時間を直接測った値ではなく、今回も独立再現していない。こちらは既存クラス階層を除去するのでなく、新たな型を制御状態のタグとして導入する点が違う。ただし「型情報を変えて難読化」という上位概念は既知。 |
| *Class coalescence for obfuscation of object-oriented software* | [US7150003B2](https://patents.google.com/patent/US7150003B2/en)、2006-12-12公開。発明者：Gleb Naumovich, Ezgi Yalcin, Nasir D. Memon, Hong Heather Yu, Mikhail Sosonkin。検索索引で書誌と明細書の説明を確認。本文openはGoogle Patents/Justiaともエラー。**全請求項は読めていない**。 | クラスをまとめて抽象構造を隠す関連技術。今回の複製groupとは機構が異なるが、型・クラス構造の変更一般を新発明とはできない。特許の有効性、権利範囲、実施自由の判断はしていない。請求項ごとの構成対比を完了したとは記録しない。 |

検索語：`WebAssembly obfuscation garbage collection recursive types ref cast`、`obfuscation recursive type WebAssembly`、`obfuscation class hierarchy transformation types`、`WebAssembly recursive groups canonicalization identity`、`obfuscation type-based dispatch`。2026-10-19時点の検索である。検索結果がないことは関連先行技術が存在しない証拠ではない。

## 候補の具体差と反証

差分候補は「同じshapeの状態tokenを、別の同値rec groupからの型で検査する」「使われない兄弟型を含むgroup全体で型identityを決める」という構成だった。初期値・整数式・memory.copyを混ぜる以前の案とは機構が異なる。しかし同値groupを作る規則は仕様どおりで、既存の型正規化だけで複製を統合できた。正規化後には有限個の型ラベルが残るだけで、追加の適応的解析負担は小さい。

「型グループに依存するのでバイナリ編集時に一部の型だけ変えると壊れる」という事実と、「元のアルゴリズムを理解しにくい」という効果は別である。今回前者を負の対照で確認したが、後者の追加優位性は示していない。単純な型ラベル化を越える技術差も未確立なので、主請求項候補として採用しない。

既存[GC参照共有回路](../alias-circuit/README.md)はオブジェクト同一性と破壊的field更新を使う。今回はfieldも更新もなく、型同値性を使う点が違う。それでも両方に共通する失敗原因は、公開された仕様から小さな意味ラベルへ落とせることである。型を増やすだけの追加実験を新原理として数えない。
