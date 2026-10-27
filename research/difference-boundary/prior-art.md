# 先行技術と確認範囲

2026-10-19。既知の部品と、今回の未確立な差分候補を分ける。検索で完全一致を見つけられなかったことを新規性や特許性の証明にしない。以下は技術的照合であり、権利範囲・有効性・実施可否の結論ではない。

|資料・書誌|実際に読んだ範囲|今回との関係・限界|
|---|---|---|
|Guy E. Blelloch, *Prefix Sums and Their Applications*, CMU-CS-90-190, 1990年11月、技術報告。[機関書誌](https://www.cs.cmu.edu/afs/cs.cmu.edu/project/scandal/public/papers/CMU-CS-90-190.html)、[著者の章版PDF](https://www.cs.cmu.edu/~guyb/papers/Ble93.pdf)|機関の書誌・要旨、章版§1.1のassociative scan定義と用途。章版とTRを別の新研究として数えない。著者publication一覧の章年は1991、他資料では1993となるため、本台帳では確認できたTR書誌を採用。|累積XORは一般的なscan。逐次依存があるように見えても、それだけで解析費用を大きくできるとはいえない。今回のcopy境界式をこの資料が直接提案したとは主張しない。|
|WebAssembly CG, *WebAssembly 3.0 Instructions*, 2026-10-13表示のlive仕様。[memory.copy](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy)|memory.copyの実行規則、bounds検査、0長、重複時の方向を確認。査読論文ではない。|範囲検査は0長returnより前。重複コピーをDへそのまま利用できる根拠。今回の変換は標準命令の意味に依存し、独自runtimeやTEEは不要。|
|Weili Wang, Honghan Ji, Peixuan He, Yao Zhang, Ye Wu, Yinqian Zhang, *WAVEN: WebAssembly Memory Virtualization for Enclaves*, NDSS 2025、査読会議。DOI 10.14722/ndss.2025.230746。[本文](https://www.ndss-symposium.org/wp-content/uploads/2025-746-paper.pdf)|表題・要旨、§V-A/Bのaddress変換・bulk runtime処理、§VI-FのSTREAM比較とTable IVを確認。|Wasmのmemory仮想化とbulk命令の費用は先行済み。ページ単位にmemmoveを分割する方式であり、隣接値のXOR差分と2境界修復とは異なる。これは難読化評価ではなく、著者実装も今回再実行していない。|
|Harold Johnson, Yuan Xiang Gu, Michael Wiener, *Securing accessible systems using dynamic data mangling*, EP2831797B1、2018-05-02公開。[公報](https://patents.google.com/patent/EP2831797B1/en)|書誌、M-registerの説明、請求項1–15を確認。|入力から得る値と置換多項式によって格納位置を変える、符号化して格納する等。今回の候補は位置のランダム化ではなく、固定した隣接関係の値の差分とbulk更新。一般のデータ符号化の初提案とはしない。|
|Harold Joseph Johnson, Yuan Xiang Gu, Yongxin Zhou, *System and method of interlocking to protect software-mediated program and device behaviours*, US9910971B2、2018-03-06公開。[公報](https://patents.google.com/patent/US9910971B2/en)|書誌、説明中のlinear encoding・変数分割と復号の批判、請求項1–3を確認。36項全体・familyの全請求項を読了したとはしない。|符号化領域での計算を続ける着想は既知。請求項1はbit群を複数linear functionとselectorで変換する具体的構成。今回の一定の隣接XORを同一構成だと断定しない。一方、単に復号を省くことを新規性の根拠にできない。|

追加反証検索：`delta encoded memmove`、`differential encoding copy boundary array`、`obfuscation differential memory`、`difference array range copy`、`XOR linked list splice`。差分配列の区間更新は既知。XOR listのbulk移動と境界リンク修正を説明する[実装READMEの検索抽出](https://docs.rs/crate/xorlist-rs/latest)も得たが、直接ページ取得は失敗し、ソース未読・未実行である。これを今回の規則と一致した確定先行技術とは数えない。名称の類似だけの差分圧縮文献・差分プライバシー文献は比較対象から外す。

## 特許候補としての構成分解

|構成要素|状態|
|---|---|
|隣接値の差分とprefixによる復号|既知の一般原理。発明の核にしない。|
|Wasmで値を符号化したまま処理|既存の符号化計算の用途。移植だけでは差を主張しない。|
|重複copyに対し、コピー前の2区間XORとcopy後の2点修復を使う|今回の具体的な差分候補。完全一致の先行技術は本調査で同定できていないが、差分の定義から直接導ける。独立した新規性・進歩性は未確認。|
|補正区間の共通部分を一度だけ読む|実測で高速化を検査。一般的な共通部分の計算共有でもあり、独立した難読化の貢献とはまだ言えない。|
|Wasm bounds・0長・重複を保存|正当性に必要な実装条件。規格の適用自体を発明とはしない。|

最大のReject理由は、更新の高速化があっても同じ差分表現の復元に追加の障壁を作らないこと。境界修復の有用性と特許に値する独立性は別判定とする。WASMixer等の基本調査は[既存台帳](../literature-review.md)にあり、今回はそれらの著者ツールを実行していない。
