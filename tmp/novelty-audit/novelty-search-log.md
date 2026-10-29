# 新規性調査の検索記録

実施日：2026-10-11。対象は `wasm-structured-encoding` の「構造化境界での状態再符号化」。
否定的な判定の根拠は検索件数や用語の不一致ではなく、`novelty-audit.md` のS1・S2などにある具体的な変換規則である。

## 調査方法

1. 提案を、アフィン符号化／多変数混合／領域別配置／境界変換合成／Wasm多値転送／解析耐性に分解。
2. Web検索で各要素を検索し、論文本文・著者公開版・公式仕様へ移動して関連節を読む。
3. S2の参考文献から一般の変数符号化・データ表現変更を確認。Wasmだけに検索範囲を限定しない。
4. 2006/2007年の直接の先行例と、近年のWasm研究・黒箱解析を区別して照合。
5. 自作42本へ別実装の入出力推定を実行し、新規性と有効性を別々に判定。

本記録は検索エンジンの全順位・全ページを保存した系統的レビューではない。後日、検索結果は変わり得る。
PDFの刊行年は本文表紙や出版社の書誌で確認し、検索エンジンのクロール日時を刊行年と取り違えない。

## 主な検索語と判断

| 検索語 | 結果・扱い |
|---|---|
| `obfuscation "different encodings" "SSA"` | SSAという名称だけの一致では判定できない。S3付録を原文照合 |
| `obfuscation "affine" "basic blocks" encoding` | 一般データ符号化へ範囲を広げる手掛かり |
| `WebAssembly "obfuscation" "affine" encoding` | Wasmに限定すると直接例が見つけにくい。非検出を新規性の根拠にしない |
| `WebAssembly obfuscation multivalue "encoding"` | 公式multi-value仕様を確認。名称だけの差を除外 |
| `obfuscation "variable encoding" "different"` | S2 §5.3の領域別配置を特定し、著者PDFで確認 |
| `obfuscation "affine" "basic blocks"` | 符号化・再符号化の関連資料を探索。特許検索結果は主要根拠に不採用 |
| `obfuscation "encoding" "SSA" Drape` | S3を照合。phiを使わないという制限も確認 |
| `"Analysis of Program Obfuscation Schemes with Variable Encoding Technique" jstage` | S10の出版社要旨を確認 |
| `"WebAssembly" "obfuscation" "affine" -site:reddit.com -site:researchgate.net` | 一次資料を優先する補助検索 |
| `"WebAssembly" obfuscation "encoding" "multi-value" -site:reddit.com` | S5および実装資料への導線 |
| `WebAssembly obfuscation 2025 2026 data encoding research -site:reddit.com` | 下表の近年資料をスクリーニング |
| `Wasm obfuscation region encoding affine multi-value research` | 特徴の組合せによる検索。完全一致がないことは証拠にしない |
| `"obfuscation" "affine transformation" Fukushima Kiyomoto 2005` | S1の2006年論文・本文へ到達。行列による多変数符号化を確認 |

前回の候補作成時の検索は `related-work.md` にも残す。今回の判定には、今回本文照合したS1・S2を優先する。

## 近年資料・アクセス範囲

| 資料 | 確認範囲 | 採否 |
|---|---|---|
| [AndroWasm, 2026, v1](https://arxiv.org/html/2602.18082v1) | 要旨・目次とaffineの本文検索 | AndroidへのWasm導入の研究として周辺資料。領域別方式の重複判定には使わない |
| [The WASM Cloak, 2025, v1](https://arxiv.org/html/2508.21219v1) | 要旨・目次とaffineの本文検索 | JS処理のWasm化を扱う周辺資料。全文比較済みとはしない |
| [Fortress WASMの作者説明](https://github.com/lkeld/fortress-wasm/blob/main/RESEARCH.md) | アーキテクチャ・方式説明の一部と語句検索 | 査読論文・有効性確認済みツールと扱わない。全ソースの監査は未実施 |
| [WAMO, DOI](https://doi.org/10.1145/3774904.3792297) | 索引で発見したが出版社本文の取得に失敗 | 内容未確認。新規性の肯定にも否定にも採用しない |
| [A First Look at Code Obfuscation for WebAssembly, NSF URL](https://par.nsf.gov/servlets/purl/10334207) | 本文取得に失敗 | この監査では本文照合済みとして数えない |
| A Systematic LLM-Based Procedure for the Deobfuscation of WebAssembly | 第三者索引で発見のみ | 一次本文未確認。技術的根拠には採用しない |

## 調査で保証しないこと

- 全世界の論文・特許・商用実装・未公開実装の網羅。
- 各論文の全版・全実装・すべての引用先と被引用先の検査。
- 同一の2×2剰余行列とmulti-value構文を使う実装が他に存在しないこと。
- TigressやWASMixerを実行して同一条件で優位性比較したこと。
- CSECでの採択、特許上の新規性・進歩性の法律判断。

これらは「新規性がある」と主張するには不足する調査範囲である。一方、
**今回の中核を新発明として扱わない**という判断は、既に得られた直接的な先行例で十分に支持される。
