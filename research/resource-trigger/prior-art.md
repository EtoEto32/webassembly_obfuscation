# 先行技術との対比と読了範囲

調査日2026-10-19。確認できた公開一次資料を記載する。検索で同一名称が出ないことを新規性の証明にはしない。今回は「計算を別の呼出し機構へ移す」という既知の方向から、所有resourceの明示的破棄へ移す具体規則を試した段階である。

| 資料 | 著者・年・種別 | 読んだ範囲と重要点 | 今回との関係・限界 |
|---|---|---|---|
| [Component Model Explainer](https://github.com/WebAssembly/component-model/blob/main/design/mvp/Explainer.md)、[Canonical ABI](https://raw.githubusercontent.com/WebAssembly/component-model/main/design/mvp/CanonicalABI.md) | WebAssembly Community Group、取得2026-10-19、設計文書 | resource型、rep、new/drop、destructor結線の説明・疑似コード。ownのdropでrepをdtorへ渡す | 本方式の実行意味そのものは既定の機能。公開結線は解析にも利用できる。査読論文でも難読化提案でもない |
| [Wobfuscator: Obfuscating JavaScript Malware via Opportunistic Translation to WebAssembly](https://dlehmann.eu/publications/Wobfuscator-sp2022.pdf) | Alan Romano, Daniel Lehmann, Michael Pradel, Weihang Wang、IEEE S&P 2022、査読会議 | Abstractと方式のtranslation sites、JS ASTからWasmへの移動を確認。論文は43,499 malicious/149,677 benignファイル等で評価 | 実行表現の境界をまたぐ計算移動という反証に重要。今回は合法ソフトウェアの式回復を課題にし、同論文の検出回避の目的・指標は採用しない。resource破棄への移動と同一ではない |
| [Program Obfuscation via ABI Debiasing](https://www.acsac.org/2021/program/final/s130.html) | David Demicco, Rukayat Erinfolami, Aravind Prakash、ACSAC 2021、査読会議、DOI 10.1145/3485832.3488017 | 会議公式Abstractを読了。VTable ordering/function pointer biasを除くcompiler変換、平均binary増加1.42%、DeClassifierへの効果を著者が報告 | ABIが解析の手掛かりになる問題は既知。今回canon結線が手掛かりを与える。NSF掲載本文URLは取得失敗し、本文の詳細や実験の限界は推測しない |
| [Obfuscating C++ Programs via Control Flow Flattening](https://www.inf.u-szeged.hu/~akiss/pub/fulltext/laszlo2007obfuscating.pdf) | Tímea László, Ákos Kiss、SPLST 2007 pp.15–29、会議論文。2009年journal版も存在 | 著者公開PDFの導入・flattening・形式的手順・評価概説を確認。complexity最大約5倍との著者報告 | 言語固有の制御構造へ既知変換を適用する先例。resource型を使うだけでは独立した難読化原理にならない。complexity増加を本研究の解析費用に読み替えない |
| [US20080289045A1](https://patents.google.com/patent/US20080289045A1) *Method and device for encoding software to prevent reverse engineering, tampering or modifying software code, and masking the logical function of software execution* | Thomas Michael Fryer、2008公開、特許公開公報 | descriptionのatoms/dependencies、claims 1–8を確認。atomの重複・順序変更、不変条件、変数のactive/inactive管理 | destructor atomは変数の破棄を意味し、Component Modelのcallbackとは同一と断定できない。「destructor」の語一致だけで先取りとも新規とも判定しない。数値性能評価は確認していない。権利状態や抵触の結論は出さない |
| [Jco transpiling](https://bytecodealliance.github.io/jco/transpiling.html)、[実装](https://github.com/bytecodealliance/jco) | Bytecode Alliance、1.27.0、公開ソフトウェア/公式文書 | componentからJS+core、instantiation、optのCLI。ローカル生成JSのresource表とdestructor呼出しを実読 | opaqueなruntime境界ではなく公開された短いtrampolineへ展開される。こちらの解析器はJSではなく元componentを入力にする。Jcoのbit30表現の反例は本試作の実測として区別する |

追加検索語は `obfuscation destructors algorithm`, `obfuscation resource lifetime`, `obfuscation destructor patent`, `resource.drop obfuscation`, `WebAssembly component resource drop obfuscation algorithm`。CN121859292A、EP2009572A1、ABI論文の本文なども候補に出たが、今回その本文を通読したとは扱わない。未読資料から差分の確定はできない。

技術的に最も近い比較は、同一engine・同一bufferを持つ直接helper呼出し版である。resourceを加えると型→destructor→core関数の結線が一段増えるが、この結線は仕様上明示される。生成順と実行順の分離も、handleからslotへの対応を辿れば解ける。今回の調査では、この具体規則の独立した先行性は確立できていない。既知の計算分割に対し、実測できる利益と請求項に切り出せる技術的差が両立した場合に限って、次の特許候補評価へ進める。
