# 近接資料と未確立な差分

2026-10-22。今回は次の一次資料の指定部分を確認した。全文・請求項・引用文献を網羅した特許調査ではない。

| 資料 | 区分・読取範囲 | 関係 |
|---|---|---|
| Harold Johnson, Yuan Xiang Gu, Michael Wiener, Yongxin Zhou, *Securing accessible systems using variable dependent coding*, [US9906360B2](https://patents.google.com/patent/US9906360B2/en), B2公開2018-02-27、関連A1公開2015-03-05 | 特許公報。書誌、C15–C18のdynamic permutation transformations・block data protectionと関連説明を確認。請求項全体の今回の精査はしていない | 実行時の変数から符号化を変え、構造体の複数変数を関係付ける一般構成が先行する。「データ依存で配置が変わる」だけでは強い差にならない |
| *Securing accessible systems using dynamic data mangling*, [EP2831797B1](https://patents.google.com/patent/EP2831797B1/en) | 特許公報。Mass Data Encodingの説明を確認。今回、発明者全員・公開日・全請求項は未精査 | storeごとの再符号化と実行中の位置変更が説明され、US7350085を参照する。同原典の直接取得は失敗し、原典全文を読んだとはしない |
| Bertrand Anckaert, Mariusz Jakubowski, Ramarathnam Venkatesan, Nick Saw, *Practical Data Location Obfuscation*, MSR-TR-2009-3, January 2009, [機関ページ](https://www.microsoft.com/en-us/research/publication/practical-data-location-obfuscation/) | 技術報告。今回確認したのは機関ページの書誌・要旨。本文の性能数値は引用しない | 実行中のデータ位置を隠す研究自体が既存。今回の差分移送の性能比較はこの実装との比較ではない |
| WebAssembly Community Group, *WebAssembly 128-bit packed SIMD Extension*, [公式提案](https://github.com/WebAssembly/simd/blob/main/proposals/simd/SIMD.md) | 仕様資料。v128のlane意味、Swizzling using variable indicesを確認。現行Core 3.0全文の精査とは区別 | i8x16.swizzleは0..15の添字を選択し、範囲外laneを0にする。命令の採用自体を独自の発明とは数えない |

具体的な検討対象は、回転に不変な統計量から配置を再構成し、変更語の統計量の差分だけで更新する規則である。今回読んだ箇所からこの式と完全に一致する記載を確認したわけではないが、それは新規性の証明ではない。不変量から可逆な作用を選ぶこと、加法的統計量を差分更新することはいずれも初等的であり、既存の動的符号化の直接的な特殊例と評価される可能性がある。

反証検索にはdata-dependent memory layout、self-keyed rotation、invariant permutation data obfuscation、data rotation checksum obfuscation等を使った。暗号やデータ匿名化の検索hitを、プログラム変換の同一先行例として混同しない。コード・公報を公開したり、出願・課金操作を行ったりしていない。

以前のpage-block-codecは値を混ぜる固定codecの全体復号を中心に扱う。本案は値そのものを変更せず、内容により論理位置を動かし差分で更新する点で異なる。ただし、両者とも公開アクセス処理から通常の表現へ戻せた。既存候補との差があることと、既存技術全体に対する新規性があることは別である。
