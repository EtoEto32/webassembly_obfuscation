# 追加の別原理探索と早期反証

2026-10-24。未実装の案を実験済み候補や新発明として数えない。

|検討した方向|一次資料・確認範囲|判断|
|---|---|---|
|import memoryの非alias条件を読み込み時に検査する|[Wasm Logic ECOOP2019](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2019.9) abstract、[US9152417B2](https://patents.google.com/patent/US9152417B2/en)概要|分離・動的alias検査からの固有差分をまだ特定できない。Wasmへの適用だけで新案にしない|
|alias分割の全列挙を必要な構造だけへ減らす|[Generalized Symbolic Execution, NASA](https://ntrs.nasa.gov/citations/20030017985) abstract、Korat公式tutorial|非同型heap入力・体系的alias探索が先行。独自の探索原理を特定できず保留|
|期待するABI型のwrapperを追加して標準validatorへ検査を委ねる|[O'Jacare.net](https://arxiv.org/abs/0705.1458) abstract、[C++WJ](https://arxiv.org/abs/cs/9907019) abstract|生成wrapperと既存言語の型検査を利用する発想に先行性。現在のWasm固有差分は弱い|
|resource型の名を消して構造検査をcacheし、実体同一性だけ後で照合する|[Wasmtime ResourcesBuilder公式source](https://docs.wasmtime.dev/api/src/wasmtime_environ/component/types_builder/resources.rs.html)全文と設計comment|resourceの共有・generativity・snapshot復元・内部外部IDの区別を既に扱う。単なる置換とcacheを新規要素にしない|
|秘密データの消去・linear memory再利用を省力化する|[WebKit 170343](https://www2.webkit.org/show_bug.cgi?id=170343)検索結果のみ|本文を十分読めておらず採否を確定しない。既知のzeroing省略との差を示せる具体方式は未形成|

これら検索の不一致や空振りは新規性の証明ではない。Gの実験では既存wasm-mergeが統合操作を代替した。Fの公開履歴への拡張は[別記録](fuel-observer/README.md)に置き、別原理3案への水増しを避ける。
