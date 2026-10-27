# 先行性・反証・次の採用ゲート

2026-10-27。一次資料の取得URL/hashは[manifest](../../results/heap-observer/priors-v1/manifest.json)。以下は読んだ範囲に限る。検索で同名手法が見つからなかったことを新規性の証明にしない。

|一次資料|種別・確認範囲|提案への反証または残る差|
|---|---|---|
|WebAssembly GC [MVP specification](https://github.com/WebAssembly/gc/blob/main/proposals/gc/MVP.md)|公式提案。recursive type group、equivalence、struct/array操作|型group複製とcast/getは仕様で可能。別moduleから読む能力そのものを発見したと主張しない|
|Binaryen133 [pass.h](https://github.com/WebAssembly/binaryen/blob/version_133/src/pass.h)|公開実装。WorldModeの仕様コメント|open-worldで逃げた参照の検査を許し、closed-worldで外部の内容検査・構築等を禁止する。観測契約の区別は既存|
|Binaryen [issue8754](https://github.com/WebAssembly/binaryen/issues/8754)、2026-05-21以降|開発者議論、査読論文ではない。public typeのshape保持・外部構築・rec group siblingの議論|型の公開性と外部利用の区別もすでに検討されている。契約の細分化だけを新案にしない。議論の全項目が実装されたとは断定しない|
|Binaryen133 [fuzz_opt.py Two handler](https://github.com/WebAssembly/binaryen/blob/version_133/scripts/fuzz_opt.py)|公開実装。第2module生成、fuzz-import、merge、独立最適化、closed-world分岐を確認|型付き外部contextを作ってmoduleの最適化前後を検査する一般原理は既存。今回のdeterministicな到達heap読出しと、ランダムな第2moduleがどこまで同じ差を観測するか未測定|
|V8 Team, [A new way to bring garbage collected programming languages efficiently to WebAssembly](https://v8.dev/blog/wasm-gc-porting), 2023-11-01|公式技術記事。Developer tools integration節|GC objectの型・field・参照辺をheap snapshotで見る能力は既存。今回との具体差はengine固有debug APIを使わず生成Wasmから読むこと|
|Wachterほか、DUMPLING、NDSS2025|査読会議。前段の[読了範囲](../boundary-alias/prior-art.md)を参照|対象code無改変の状態比較、addressを除くserialize、観測上限の費用調整は既存。Wasm GC境界の比較契約・standard engineへの適用を別途評価する必要がある|
|Oracle Java serialization、WangほかFuzzJIT USENIX2023|公式仕様・査読会議。前段の[読了範囲](../boundary-alias/prior-art.md)|循環・共有の番号付け、深い値比較は既知。BFS/Mapを新アルゴリズムとしない|

## 技術差を仮説へ絞る

残る研究候補は「**Wasm GCの外部観測契約に合う読出しcontextを自動生成し、既存の出力oracleが失う状態差を定量化する**」という評価・検査方法である。型付きgetter、BFS、共有の番号付けの個々の原理は既知。対象programもengineも書き換えず同じhelperで最適化前後を比べる構成には実装上の差があるが、それだけで修士研究の十分な貢献とは判定しない。

最も厳しいReject理由は、Binaryen Two等がすでに同じ違いを十分に検出し、今回が便利な表示器の追加に留まることである。手製のfield値変更だけを大量に検出しても、この反証には答えられない。別の危険は、closed-worldで許された表現変更を誤検知して検出数を膨らませること。今回の32差はその負の対照として扱う。

## 次の検査（まだ実行していない）

1. 版固定のTwo / fuzz-importと、typed/multi callerを併せた強い既存対照を実行する。同じ対象・同じ変種・生成/実行時間予算で比較し、単純な手書きgetterも残す。
2. 追加効果の評価対象を、観測器に都合のよい手製field差だけから、独立選定した公開の修正済みmiscompilationと実生成物の系統的な故障注入へ広げる。自然な不具合と人工変種の件数を分ける。
3. 差がある場合は、型検査失敗・scalar値・内部alias・cycle・array length/element・閉世界契約違反に分けて原因を示す。random contextが見逃す条件を抽出する。
4. 同等の費用で差が出ない場合は新規検査方式として採用しない。測定されたテスト不十分性が残るなら、その体系的実証を修士テーマ候補として再評価する。

型付き呼出しpoolを新方式として足す方向は、[Randoop/Weaverとの照合](../boundary-alias/caller-results.md)により優先しない。型groupの複製自体も[既存type fuzzer](../type-context/README.md)との重複が強い。今回も新しい案の数だけを増やさず、最も近い既存対照への追加効果を次の判定基準にする。
