# Pの先行技術・反証調査

調査日2026-10-26。読了範囲を限定して記載する。検索不発を世界初の根拠にはしない。今回の目的は修士研究の差分であり、特許性の鑑定は行っていない。

| 資料 | 種別・確認範囲 | Pとの関係 |
|---|---|---|
| WebAssembly Community Group, Core Specification, Appendix Validation Algorithm。[仕様](https://webassembly.github.io/spec/core/appendix/algorithm.html) | 標準仕様。operand/control stack、unreachableのアルゴリズム説明を参照 | single-pass型検証そのものは既知。single-passでも多値の展開量が定数とは限らない |
| wasmparser 0.227.1 / 0.262.0, Bytecode Alliance。[0.262.0 source](https://github.com/bytecodealliance/wasm-tools/blob/v1.262.0/crates/wasmparser/src/validator/operators.rs) | 実装。block/loop/if/end/call、pop、push、br_table周辺を実読。全crate読了ではない | 読んだ箇所は各型要素をpop/push。Pとの差はsignature sliceをoperand stackの表現に保つ点 |
| V8 contributors, function-body-decoder-impl.h。[source](https://github.com/v8/v8/blob/main/src/wasm/function-body-decoder-impl.h) | 実装。ValidateParameters/PopSomeArgs/PushValueTypesを実読。2026-10-26 snapshot保存 | 読んだ箇所は値ごとに検査・push。compiler IR生成と共有されるので、Pの置換がそのまま可能とは未確認 |
| WABT contributors, type-checker.cc。[source](https://github.com/WebAssembly/wabt/blob/main/src/type-checker.cc) | 実装。PeekType/PushTypes/PopAndCheckSignature/PopAndCheckCallを実読 | 配列と型列ごとの検査を使用。Pと完全に同じ圧縮スタックは読んだ範囲にはない |
| Alex Crichton, “Fix an exponential algorithm validating components”, 2026-10-06, [PR #2755](https://github.com/bytecodealliance/wasm-tools/pull/2755) | 実装修正。commit説明とcomponent.rs変更を実読 | outer alias時のfree-variable走査にeffective type sizeを課金・上限制御。operand stack表現とは異なるが、短い型参照から大きな検証仕事が生じる問題は既知 |
| Alex Crichton, “Limit types in rec groups in components”, 2026-10-01, [PR #2726](https://github.com/bytecodealliance/wasm-tools/pull/2726) | 実装修正。説明・変更を実読 | rec groupを1型として数えず含有型数を上限へ計上。資源量の正確な課金という問題自体は新規でない |
| Nick Fitzgerald, “Multi-Value All The Wasm!”, 2019-11-21, [Bytecode Alliance](https://bytecodealliance.org/articles/multi-value-all-the-wasm) | 技術記事、査読論文ではない。multi-value用途・validation導入の説明を参照 | 型列を番号で参照してmulti-valueを扱う仕組みと用途は既存。Pはmulti-valueを発明したわけではない |
| Xavier Leroy, “Java Bytecode Verification: Algorithms and Formalizations”, 2003, JAR 30, 235–269, [DOI](https://doi.org/10.1023/A:1025055424017) | 査読誌。出版metadata、[著者版](https://xavierleroy.org/publi/bytecode-verification-JAR.pdf)のAbstract・§1・§3とキーワード周辺を読んだ。全文読了ではない | 型のabstract interpretation、検証費用と安全性の研究は長い蓄積がある。Wasm版の型スタックを実装しただけでは新規性にならない |
| Andreas Gal, Christian Probst, Michael Franz, “Integrated Java Bytecode Verification”, 2005, ENTCS 131, 27–38。[著者機関記録](https://orbit.dtu.dk/en/publications/integrated-java-bytecode-verification/) | 機関記録ではpeer-review。今回はAbstract・metadataのみ | SSAのdefinition/use照合へ統合し、値の移送ごとの検査を省く既存研究。Pのsame-language圧縮列との詳細な差は本文比較未完了 |
| Zhaofeng Yu et al., “Exploring and Exploiting the Resource Isolation Attack Surface of WebAssembly Containers”, USENIX Security 2025。[論文](https://www.usenix.org/system/files/usenixsecurity25-yu-zhaofeng.pdf) | 査読会議。Abstract、fuel/mitigation/compilation関連の検索箇所のみ | host資源を含むWasm resource isolationの研究。検証時間を含む資源保護という広い目的を新発見とはしない |

公開ソース6件のsnapshot・URL・SHA-256を`results/signature-stack/prior-snapshots-v2/manifest.json`に保存した。main URLは将来変わるので実読箇所の再確認にはsnapshotを使う。#2755/#2726はwebページ取得が失敗した後、公開patchを取得して確認した。初回ネットワーク失敗もv1に残した。

## 積極的に疑った点

- hash-consing、rope/区間列、memoization自体は新しくない。仕様上既に存在するsignatureを使うだけで独立の研究貢献が成立するとはしない。
- 同一signatureの反復を減らすだけなら1件のcertificateを持つcached-flatで足りないか → 実装・測定したところ、多くの効果がこれで説明できた。
- 同じ型のrun-length encodingで十分ではないか → i32/i64/f32/f64が混在する列を使用。ただし混在させたこと自体は新規性の証明ではない。
- 長いsignatureを別chunkへ分割すれば省略が外れるのではないか → `fragmented-v1`で確認。一般的な検証仕事上限の解決ではない。
- 最新版で既に解決済みではないか → 0.262.0を固定して比較。wide人工例では差が残ったが、strong flat対照との差は小さい。

検索語は`WebAssembly validator compressed operand stack multi value signature validation`、`bytecode verification compressed type stack persistent stack signatures`、`WebAssembly validation hash-consing`等。これらで完全同一方式を確認できなかったことは、「同一研究が存在しない」という証明にならない。

**判定**：読んだ主要実装との狭い実装差はある。新しい基本原理・修士主テーマとして十分な独自性は未確立。一般的な型列再利用を超える問題設定・保証・適用実績が必要。
