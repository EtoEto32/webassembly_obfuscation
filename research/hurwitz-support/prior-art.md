# 先行技術と確認範囲

2026-10-19調査。今回実行したのはローカルの新しい試作であり、下記の著者実装の追試ではない。完全一致の検索結果が見つからないことを新規性の証明にしない。

|資料|書誌・種別・実際に読んだ範囲|関係・限界|
|---|---|---|
|*Private Function Evaluation with Cards*|Alexander Koch, Stefan Walzer, **2022**, New Generation Computing 40:115–147、査読誌、[DOI 10.1007/s00354-021-00149-9](https://link.springer.com/article/10.1007/s00354-021-00149-9)。要旨、モデル、§7のBarrington構成と証明を確認。|幅5の置換列でBoolean計算を実行する原理は既知。カードの秘密shuffleと監視の物理的仮定があり、公開のWasm表にその秘匿性は移せない。本試作の基礎構成はこの既知原理。原典Barrington (JCSS 38(1):150–164, 1989, DOI 10.1016/0022-0000(89)90037-8)の書誌はこの論文の参考文献で確認し、原典全本文を読んだとはしない。|
|*Centrality of star and monotone factorisations*|Jesse Campion Loth, Amarpreet Rattan, **2025**、Bulletin of the London Mathematical Society、査読誌、[DOI 10.1112/blms.70170](https://londmathsoc.onlinelibrary.wiley.com/doi/full/10.1112/blms.70170)。書誌、要旨、§1.6を確認。|Hurwitz moveの逆向き・積保存を明示する数学研究。今回の基本恒等式は新発見ではない。この論文の主定理を難読化強度の根拠に使わない。|
|*The MMap Strikes Back: Obfuscation and New Multilinear Maps Immune to CLT13 Zeroizing Attacks*|Fermi Ma, Mark Zhandry、**TCC 2018**、査読会議。[会議PDF](https://www.iacr.org/archive/tcc2018/11239235/11239235.pdf)の表題・要旨・§2.4を確認。|隣接する基底行列を相殺するKilian型randomizationが説明される。本試作のbasis対照はその公開置換版。multilinear mapや当該論文の安全性仮定を実装していない。|
|*Obfuscation for protection of streaming media and other data flows*|Lex Aaron Anderson、[US20240045670A1](https://patents.google.com/patent/US20240045670A1/en)、公開**2024-02-08**、出願人表示Arris Enterprises LLC。公開特許資料、査読論文ではない。書誌、§3のrandomized branch encoding、Algorithm 1、公開公報の請求項19–29を確認。|logical operationから幅一定の置換分岐programを作り、層間経路・入出力符号化を変更する。今回のbase/basisと近い。入力依存の支持集合を縮約しながらHurwitz moveを選ぶ規則が同一記述かは確認できない。登録版の請求項・全ファミリーを比較したものではなく、抵触性や特許可能性の判定をしない。|
|*White-box cryptographic system with input dependent encodings*|Wilhelmus Petrus Adrianus Johannus Michiels, Paulus Mathias Hubertus Mechtildis Antonius Gorissen、[US9654280B2](https://patents.google.com/patent/US9654280B2/en)、公開**2017-05-16**、Irdeto BV。先行公開US20120002807A1の表示を確認。特許資料。encodingの説明、nibbleで選択する表の例、請求項1–13を確認。|入力由来のselectionに応じてencoderとcompensatorを選ぶ考えは既知。本試作は鍵付き暗号処理ではなく公開Boolean式で、因子交換を用いるが、「符号化が入力依存」という差だけでは新規といえない。法的な請求項解釈は行っていない。|
|*Graph-Based Algorithms for Boolean Function Manipulation*|Randal E. Bryant、**1986**、IEEE Transactions on Computers C-35(8):677–691、査読誌、DOI10.1109/TC.1986.1676819。[著者公開版](https://www.cs.cmu.edu/~bryant/pubdir/ieeetc86.pdf)の要旨・導入・定義を確認。更新注釈を含む版。|順序付き判断図の正規化は既知の解析。今回の攻撃は有限状態を終端とした同じ原理を使う。BDDが最悪指数的になる事実を、今回生成した例が難しいという証拠にしない。|
|*128-bit packed SIMD Extension*|WebAssembly CG、[公式提案](https://github.com/WebAssembly/simd/blob/main/proposals/simd/SIMD.md)、仕様資料。swizzleの索引・範囲外zeroの節を確認。|置換の合成がswizzleへ落ちる。これはWasmでの効率的実装であり、群計算そのものがWasmで初めて可能になるわけではない。|

## 選別した他方向

Bertrand Anckaert, Mariusz Jakubowski, Ramarathnam Venkatesan, Nick Saw, *Practical Data Location Obfuscation*, MSR-TR-2009-3, January 2009。[著者所属機関ページ](https://www.microsoft.com/en-us/research/publication/practical-data-location-obfuscation/)の要旨・書誌を確認。heap再配置、stackからの移送、pointer scramblingが既知。本文全体・数値表は未確認で、この試作との定量比較には使用しない。

*Analysis of Exception-Based Control Transfers*, CODASPY2017、DOI10.1145/3029806.3029826の[著者PDF](https://www2.cs.arizona.edu/~debray/Publications/codaspy17.pdf)は検索抽出の導入部分のみ確認、直接openはtimeout。例外による制御移送の既知性の手がかりであり、全文読了扱いにしない。Wasmの例外方式をこの資料だけで完全に否定したわけではない。

## 反証検索と差分の扱い

`obfuscation Hurwitz`, `program obfuscation braid`, `branching program input-dependent conjugation`, `permutation branching program obfuscation patent`等で追加探索した。既知の群計算・層間randomization・入力依存符号化との重なりが大きい。今回の支持変数数による選択規則は具体的に実装できたが、それを独立した発明として推せる有効性は実測で確認できなかった。既存特許に記載された強度の主張も、そのまま本研究の事実にしない。
