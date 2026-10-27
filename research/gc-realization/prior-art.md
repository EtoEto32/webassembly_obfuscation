# Sの先行性検査

2026-10-27。論文・実装を混同しない。新規性の否定も未確認の同一実装を根拠に断定しないが、既知の原理を新発明とは数えない。

|一次資料|確認した内容|Sとの関係と未確認事項|
|---|---|---|
|Boyapati, Khurshid, Marinov, **Korat: Automated Testing Based on Java Predicates**, ISSTA 2002, pp.123–133, DOI 10.1145/566172.566191（査読済み）|著者公開PDFのabstract、有限化・探索・fieldアクセスによる枝刈り、instrumentationと特別constructorに関する節を読んだ|構造を持つ有限入力・aliasを含むobject graph生成という広い目的は既存。Sは与えられたWasm graphのconstructor実現性を対象とするが、Koratを無変更で実行した比較ではない|
|Haack, Poll, **Type-based Object Immutability with Flexible Initialization**, 2009著者公開稿|abstract、序論、§1.4等。初期化phaseとimmutable/non-null条件の衝突、constructor外の領域による初期化を説明|初期化順序・二段階初期化・循環構造という発想は古い。Wasm immutable fieldには後書き用phaseがない点を区別する。会議版との逐語同一性や実装性能を今回確認していない|
|Fähndrich, Xia, **Establishing Object Invariants with Delayed Types**, OOPSLA 2007|検索で得られたabstract・序論抜粋まで。全文精読・再現は未実施|nonnull不変条件と初期化、既知のbackpatchingを調べる追加候補。全文未読部分でSと一致・不一致を断定しない|
|Binaryen **version_133 scripts/fuzz_opt.py**, class `Two`（実装）|保存snapshotの1932行付近から、二つ目を`--fuzz-import`で生成し、link/merge/optimizationを比較する処理を確認|別案の「複数moduleを結び、別々に最適化するmetamorphic test」は既に実装されている。新しいフレームワークと称する案をこの段階で採用しない|
|Rで確認したBinaryen Inhabitator、wasm-smith 0.262、Weaver（実装/プレプリント）|[Rの一次資料対比](../gc-witness/prior-art.md)と[追加比較](../gc-witness/smith-results.md)|型に合った値・module shape・再帰arrayの空値生成はSの新規部分ではない。Sでは既知型構築をそのまま部品として使う|

参照: [Korat著者PDF](https://users.ece.utexas.edu/~khurshid/testera/korat.pdf)、[著者の出版一覧](https://korat.sourceforge.net/publications.html)、[Haack/Poll著者PDF](https://www.cs.ru.nl/~erikpoll/papers/javimu09.pdf)、[Delayed Types PDF所在](https://citeseerx.ist.psu.edu/document?doi=30b0f52b292f2d9c00862577e6f6a9aa1d804a98&repid=rep1&type=pdf)、[Binaryen固定版](https://github.com/WebAssembly/binaryen/blob/version_133/scripts/fuzz_opt.py)。

## 差分として残る範囲

Sは「元のWasm型を変えず、指定IDの区別・alias・mutable cycleを、通常命令で実現できるか」を明示的に判定し、実行できる証拠を出力する。この問題設定・限定条件・再現物は今回の成果である。ただし、既存の位相順序とseedを使う初期化で同じ結果が得られた。一般的なグラフ構築の新原理という主張は支持されない。

近接研究に対象機能が未記載であるだけでは、新規性の証明にならない。既存生成器へ短い補助関数を足しただけで同じ効果が出る可能性、型付きheap合成・constructor-based test generation・symbolic heap生成で既に扱われている可能性が残る。実際のテスト到達や欠陥検出で追加価値を示す必要がある。

## 仕様とコーパス

[Wasm Core仕様](https://www.w3.org/TR/wasm-core/)のconstructor・field mutabilityが基礎となる。保存した `spec-aggregate.rst` はprose生成用テンプレートを含み、展開済み全規則を読めたものとして扱わない。GC仕様の巨大ページ取得はサイズ上限で失敗した。判定の正当性は限定モデルと3engineの実行で照合し、仕様全体の形式証明とは区別した。

[mkustermann/wasm_gc_benchmarks](https://github.com/mkustermann/wasm_gc_benchmarks)のREADME・tree metadataを確認し、固定commitの12binaryを静的検査した。出自の同じ6設定の最適化前後であり、一般Web全体の代表標本ではない。型中にnonnull mutable fieldがあるという観測は、実行時に循環・aliasが生じる証拠ではない。

資料snapshotは `results/gc-realization/priors-v2`。v1はDNS失敗、v2で5資料の取得に成功した。R時点の検索401はこのturnでは回復し、継続不能の理由にしていない。
