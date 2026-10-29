# 先行研究と主張できる差分

確認日2026-10-27。取得元・hashは[manifest](../../results/boundary-alias/priors-v1/manifest.json)。読んだ範囲を以下に限定する。未実行の他研究の数値は著者報告であり、本研究の再現結果ではない。

|資料|区分・読んだ範囲|関係と限界|
|---|---|---|
|WebAssembly Community Group, [JavaScript Interface §5.8](https://webassembly.github.io/spec/js-api/#garbage-collected-objects), 2026取得|公式仕様。Exported GC Objectの内部操作・cache規則|同じWasm object addressを同じJS wrapperへ対応付ける。公開参照のidentityは観測可能。private fieldの読み出しは不要|
|Binaryen133 [fuzz_shell.js](https://github.com/WebAssembly/binaryen/blob/version_133/scripts/fuzz_shell.js)|公開実装。printed、logRef、callFunc、callExports|GC objectを通常prototypeの表示へ縮約する。今回のidentity列はこの表示に含まれない。ただしBinaryenには他のassertion・ref.eq生成・interpreter比較があり、ツール全体がidentity bugを検出不能とは言わない|
|Oracle, [Java Object Serialization Specification §1.2](https://docs.oracle.com/en/java/javase/25/docs/specs/serialization/serial-arch.html#writing-to-an-object-stream)|公式技術資料。初回参照にhandleを割り当て、後続参照でhandleを使用する部分|共有・循環の保存は既知。WeakMap番号付けそのものの新規性への直接的な反証。Javaで既知だからWasmでの有用な実証が無価値、とは言わない|
|Junjie Wang, Zhiyi Zhang, Shuang Liu, Xiaoning Du, Junjie Chen, **FuzzJIT: Oracle-Enhanced Fuzzing for JavaScript Engine JIT Compiler**, USENIX Security 2023。[会議PDF](https://www.usenix.org/system/files/usenixsecurity23-wang-junjie.pdf)|査読会議。表紙、oracleの§4とTable2周辺、特にdeepEqualsとfalse-positive対策|返却値の深い比較、JIT前後の比較は既存。Table2はproperty値の再帰比較を示すが、実装全体のalias保存能力は今回未検証。Wasm GCに未対応と断言しない|
|Liam Wachter, Julian Gremminger, Christian Wressnegger, Mathias Payer, Flavio Toffalini, **DUMPLING: Fine-grained Differential JavaScript Engine Fuzzing**, NDSS2025, DOI10.14722/ndss.2025.241411。[会議PDF](https://www.ndss-symposium.org/wp-content/uploads/2025-1411-paper.pdf)|査読会議。abstract、§IIIのstate extraction/serialization/matching、§Vの感度・費用・hyperparameter部分|対象JSコードを変えずengine側で内部stateを取得し、addressやtier固有情報を除外するのは既存。「非侵襲oracle」という一般主張は新しくない。本試作は既存公開境界だけを使うため狭い。著者は8新規bugを報告、今回は未再現|

## 技術差と研究新規性を分ける

今回確認した技術差は「opaqueなGC objectの単一値表示に、既存の境界をまたぐ同一性列を加える」こと。fieldを辿るdeep serializationより少ない観測でも、共有関係だけの差を識別できる。標準engineで実行でき、compiler内部のpatchを必要としない。

ただし正規化の核は既知。線形探索対照も全故障対照を識別したので、独自の検出原理を確立したとは扱わない。Java serializationとの先行性だけでWasm向け研究の可能性を完全否定もしない。修士研究の貢献として残る可能性は、**現行Wasmテストoracleの測定された欠落、どの実行・API条件で起きるか、追加観測が実不具合検出に寄与するかの体系的実証**である。

現状は14種類の意図的な差を含む小例と64生成物のみ。自然に発生したmiscompilationの追加検出は0、他研究のoracleを同一条件で実行した比較もない。よって主テーマへの昇格は保留。次の採用条件は、独立選定した既知不具合又は実生成器の故障注入評価、適切なtyped input/multi-value観測、ログへの小修正対照を含む費用比較である。単純な修正が同じ効果でも応用上の新規性を自動的に否定せず、貢献の大きさを別途評価する。
