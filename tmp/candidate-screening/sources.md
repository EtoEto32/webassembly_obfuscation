# 次候補の調査記録

調査日2026-10-11。一次資料の該当部分を確認した範囲を記録する。全論文・実装を網羅した系統的レビューではない。

| 資料 | 年・確認範囲 | 判断への用途 |
|---|---|---|
| [Drape, Intellectual Property Protection using Obfuscation](https://www.cs.ox.ac.uk/people/stephen.drape/papers/siemens.pdf) | 表紙March 2009、§2.4.1と§6.5の該当記述。本文確認、実装なし | 例外による制御変換の直接の先行例。以前の監査の2010年Oxford報告とは参照版を区別 |
| [Lu, Control Flow Obfuscation for FJ using Continuation Passing](https://arxiv.org/html/2012.06340v2) | arXiv初版2020、v2 2021。§2の例、§4の変換説明を確認。実装未確認 | 元の例外処理をCPSへ変換する研究。意図的にthrowを増やす方式そのものと誤認しない |
| [Foket et al., A Novel Obfuscation: Class Hierarchy Flattening](https://users.elis.ugent.be/~brdsutte/research/publications/2012FPSfoket.pdf) | FPS 2012著者公開版、§1–2の方式と例。実装未確認 | 型階層の変換と型検査の書き換え。Wasm GC状態表現と完全に同一という根拠にはしない |
| [V8 canonical-types.h](https://chromium.googlesource.com/v8/v8/+/cfa8d0b35acb42e79382004e0f1625d5ae1a7493/src/wasm/canonical-types.h) | 固定commitのクラス冒頭コメント・宣言を確認 | 同一再帰グループと対応する型のcanonicalization。実測Nodeと同じcommitと確認したわけではない |
| [Wasm binary types](https://webassembly.github.io/spec/core/binary/types.html) | 表示版WebAssembly 3.0 (2026-10-09)、型・recgroupの符号化 | 直接バイナリの型節構築。新規性の資料ではない |
| [vmquack作者説明](https://www.willsroot.io/2023/08/vmquack-avx512.html) | 2023年、本文のvectorized VM命令の説明。ソースの実行・全監査は未実施 | SIMD/AVX-512使用だけを新しい発想としないための一次実例。査読論文とは扱わない |

主な検索語：

- `WebAssembly obfuscation exception handling tags control flow`
- `WebAssembly obfuscation garbage collection br_on_cast reference types`
- `software obfuscation SIMD lane encoding vectorization`
- `"obfuscation" "class hierarchy" "type" paper`
- `"exception-based" "obfuscation" paper 2009`
- `"WebAssembly" "recursive types" "obfuscation"`
- `"exception" "obfuscation" "Drape" control flow`

未確認・取得失敗：

- `https://x86asm.net/articles/using-xmm-for-general-purpose-simd-with-gpr/index.html`：HTTP/HTTPSとも本文取得失敗。検索の抜粋だけで詳細を確定しない。
- `https://www.diva-portal.org/smash/get/diva2%3A699631/FULLTEXT01.pdf`：タイムアウト。検索抜粋からDrapeの元の資料へ移り、元の資料で根拠を確認した。学位論文全体を読んだ扱いにしない。
- NotDecの型復元に関する論文：索引で発見した段階。一次本文・実装未確認であり、解析性能の根拠にはしない。

型名・SIMD命令・例外を使うことだけで新規性が成立しないという選別と、すべての拡張候補に新規性がないという断定は異なる。後者は行っていない。
