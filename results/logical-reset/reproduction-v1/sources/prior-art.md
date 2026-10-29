# Jの近接先行技術と読了範囲

調査日2026-10-24。以下は読めた資料の対応付けであり、網羅的な特許調査ではない。著者の評価値を当リポジトリの追試値に混ぜない。

|資料|種別・書誌|今回の確認範囲|Jに対する意味|
|---|---|---|---|
|[Proposal: first-class Instance::reset() for pooled reuse of untrusted guests](https://github.com/bytecodealliance/wasmtime/issues/14313)|公開issue、stevendore、2026-09-10。査読なし|Feature/Benefit/Implementation/Alternatives、およびmaintainerの2026-09-10コメント|最も近い要求仕様。再利用時にdrop状態まで戻す問題設定は既知。性能にはpoolingとの比較が必要という指摘もある|
|[PoolingAllocationConfig](https://docs.wasmtime.dev/api/wasmtime/struct.PoolingAllocationConfig.html)|Wasmtime公式実装資料、表示51.0.0-dev|Advantages/Disadvantages、resident設定|ランタイム内の再利用・初期像復元・縮小に既存の強い対照がある。JのNode fresh対照からこの方式への優位は推論できない|
|[Wizer](https://github.com/bytecodealliance/wizer)|公開実装、Bytecode Alliance|READMEのAbout/How it works/Caveats。今回本体未実行|初期化結果をmoduleへ保存する先行例。初期像を持つこと自体は新規ではない|
|[Reusable Enclaves for Confidential Serverless Computing](https://www.usenix.org/conference/usenixsecurity23/presentation/zhao-shixuan)|Shixuan Zhao, Pinshen Xu, Guoxing Chen, Mengya Zhang, Yinqian Zhang, Zhiqiang Lin、USENIX Security 2023、査読済み|[本文](https://www.usenix.org/system/files/usenixsecurity23-zhao-shixuan.pdf)のabstract、§3.2–3.3、§4.1–4.2、§4.3冒頭、§5.2/§6.3の関係箇所。全文読了・再現は未実施|保護されたsnapshotを使うenclave再利用。cross-request resetと復元metadata保護は既存概念で、実装層がJと異なる|
|[Live migration of compiled Wasm modules across the Compute Continuum](https://research.unipd.it/retrieve/3f09ee34-9cc7-4356-b4a9-ffc7694ad4a2/JSA%202025%20-%20Tinto.pdf)|E. Tinto, L. Marchiori, T. Vardanega、Journal of Systems Architecture 168 (2025) 103532、[DOI](https://doi.org/10.1016/j.sysarc.2025.103532)、査読済み|abstract、§3.2–3.6、評価・discussionの取得箇所、参考文献42。[公開repo](https://github.com/TintoEdoardo/wasm-tools/tree/develop)を同定。cratesページは取得失敗し関連実装本体未読|Wasm bytecodeへcheckpoint/restoreを挿入する原理は既知。エンジン非改造の変換だけではJの新規性にならない|
|[US10936724B2: Configurable compute instance secure resets](https://patents.google.com/patent/US10936724B2)|Diwakar Gupta, Marcin Piotr Kowalski, Johannes Stephanus Jansen Van Rensburg。表示優先日2017-09-27、B2公開2021-03-02、Amazon Technologies Inc|書誌、description冒頭、請求項1–20|VMのvolume復元と識別情報維持を含むreset。reset一般を広く請求する根拠にならない。Wasm特有の連動変換の同一記載は読んだ請求項からは確認できない|

特許の独立請求項1・10・18は、container利用後のVM、volumeの交換または復元、同一device/network addressの維持を含む。従属項2・14はvolatile memory snapshotを加える。Jはvolume・network addressを扱わず、これらとの形式的差はある。ただし記載の全体・関連family・他の引用文献を調査し尽くしておらず、非侵害や権利化可能性を結論しない。

Wasm仕様の[現行文書](https://webassembly.github.io/spec/core/bikeshed/)と[bulk memory proposal](https://github.com/WebAssembly/bulk-memory-operations/blob/master/proposals/bulk-memory-operations/Overview.md)を、grow、drop、active segment初期化の意味確認に使った。Jは標準仕様が定める挙動を利用しており、これらの意味自体を発明要素にしない。

追加検索は `WebAssembly reset instance data.drop virtualization`、`WebAssembly reset logical memory.grow`、`WebAssembly snapshot binary transformation elem.drop`、`patent WebAssembly reset instance virtual memory size data segments`、`WebAssembly reset binary instrumentation memory`、`WebAssembly reset logical size` 等。直接一致する構成は今回同定していないが、検索の不発は不存在の証拠ではない。二次的なチュートリアルは新規性の肯定根拠に使わない。

未読の探索先としてGenWasym（arXiv:2608.18327、プレプリント）、Wemby（ISSTA 2025）、Wasm移行の周辺実装が残る。abstract・検索snippetだけでJとの全構成差を認定しない。
