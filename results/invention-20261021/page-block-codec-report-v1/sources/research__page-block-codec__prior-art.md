# 先行構成との照合

調査日2026-10-21。検索一致の有無だけでは新規性を判定しない。今回の技術的判断は、既知の高アドレス優先処理が具体的な意味保存の代替になることと、方式を知る回復が安いことに基づく。

## 実際に読めた一次資料

1. **WASMixer: Binary Obfuscation for WebAssembly**、Shangtong Cao, Ningyu He, Yao Guo, Haoyu Wang。今回読んだ版は[arXiv PDF](https://arxiv.org/pdf/2308.03123)の§3.3、§4.1.1、Algorithm 1。既存の査読版とは版を混同しない。base/offset/幅/符号を受けるload/store helperで、読込み後・書込み前にXORを行う。今回の差は複数語を混合するblock表現とtrap境界のloweringであり、load/storeの置換や随時復号自体には差がない。この論文の実装を今回実行したわけではない。

2. **partially out of bounds store writes to memory**、Dan Gohman (sunfishcode)、2017-03-02。[WebAssembly/spec issue #438](https://github.com/WebAssembly/spec/issues/438)。ページ末尾のstore16が先頭byteだけ変更してからtrapする反例と、trap後にそのbyteを読む例を本文で確認。査読論文ではなく公開された仕様実装の議論。

3. **Wasm: Emit byte stores for unaligned store from high-to-low to properly handle partial-OOB**、Lars T. Hansenほか。[Mozilla Bug 1343981](https://bugzilla.mozilla.org/show_bug.cgi?id=1343981)。descriptionとreview comment 5に、高アドレスからbyte/wordを書いて範囲外なら変更前に止める処理が明記される。Firefox63での修正記録がある。patch attachmentの直接取得と日時APIは取得失敗なので全文patch精読とはしない。今回のblock-highはこの順序規則を独立block表現へ適用した自作対照で、Firefox実装をベンチマークしたものではない。

4. **WebAssembly Core Specification 3.0**、[2026-10-20版の実行規則](https://webassembly.github.io/spec/core/exec/instructions.html#memory-instructions)のscalar load/store・SIMD load/store。自然数での有効アドレス・全幅の範囲検査・非整列許容を確認。[memory64提案](https://github.com/WebAssembly/memory64/blob/main/proposals/memory64/Overview.md)も確認。memory64やSIMDの導入自体を本研究の発明とはしない。

## 関連資料を新たに具体化した範囲

5. **WeBMO: WebAssembly Memory Bitwise Operation Obfuscation**、Jeongpil Park, Eun-Sun Cho、COMPSAC2024、1436–1439、DOI [10.1109/COMPSAC61105.2024.00189](https://doi.org/10.1109/COMPSAC61105.2024.00189)。[公式program](https://ieeecompsac.computer.org/2024/program/)のSRS枠に題名variantと著者を確認。本稿全文は未取得。本文を推測して「本方式にはない」と主張しない。会議収録は確認したがこの枠の査読手順は未確認。

6. **Simplification of Executable Code Obfuscated by Bitwise Memory Operations**、Jeongpil Park, Seoksu Lee, Eun-Sun Cho、KSC2023、2023-12-20。[著者研究室のpublication一覧](https://sites.google.com/cs-cnu.org/plas/publications/2020-current)と[news](https://sites.google.com/cs-cnu.org/plas/older)で題名・著者・発表日を確認。本論文の本文と査読手順は未確認。WeBMO本文の代用品にはしない。

7. **Simplification method of executable code obfuscated with Bitwise Memory Operation**、[KR103005503B1](https://patents.google.com/patent/KR103005503B1/en)、関連公開[KR20250115746A](https://patents.google.com/patent/KR20250115746A/en)。掲載発明者は조은선、박정필、出願日2024-01-24、A公開2025-07-31、B公開2026-08-13。直接openはCache missだが、同Bページの検索抽出に請求項1–9の韓国語と英訳が返り、その範囲を読んだ。mi-asm Z3 IRのConcat/Extract/mem32をpattern照合し、ExprCompose/ExprSlice/ExprMemへ移す簡約が記載される。本実験はv128 helperの実行による同定で、同一手順とは扱わない。発明の優先権、現在の権利状態、有効性、侵害・実施自由についての判断は行っていない。明細書全文・審査経過の精読でもない。

## 採否

最大のReject理由は、符号化・read-modify-writeのまとめ上げ・Wasmの既知の失敗前検査規則の実装で説明でき、独自の生成原理と追加保護効果が弱いことである。「解析できるから難読化でない」という理由ではない。性能上の改良は保持するが、今回の順序/符号化/アドレス拡張をそれぞれ独立発明とは数えない。

残る未検証事項はWeBMO本文との具体的差、一般のアクセスを持つ実アプリでの適用率、復号を独立helperとして取り出せない構成の費用である。単にhelperをinline化することは既知の変換であり、それだけを次の新候補にしない。
