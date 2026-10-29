# 別原理の探索と反証記録

調査日2026-10-24。検索結果がないことは新規性の証明ではない。

|仮説|確認した既存技術/問題|判断|
|---|---|---|
|NaNをbit観測点だけで正規化|Wasm RationaleとMozilla bug1338127の議論に、reinterpret/store/call/return等での遅延canonicalizationがある|新規候補から除外。実装しない|
|CABIの全own handleを先に検査してから一括消費|Canonical ABIのtrapはstoreをlockdownする。失敗後の状態を再利用できるとの前提が誤り|公開外部資源への固有の利益をまだ示せず、実装を優先しない|
|CABI liftで共有subtreeをhash-consする|一般のimmutable graph共有、serialization、lazy lowering、zero-copy CM提案に近い|単なるmemo化/共有を主発明にしない|
|公開イベントごとの累積fuel上界から差分予約|定資源型、Wasm gas evaporation、EVM gas paddingが近い。中間イベントと低予算停止、区間間の未使用creditを対象に絞る|限定プロトタイプで有効性と強い対照を確認する。新規と断定しない|

## 読んだ資料

- [Mozilla bug1338127](https://bugzilla.mozilla.org/show_bug.cgi?id=1338127): Benjamin Bouvierの報告とLuke Wagner等の議論、2017年。技術議論で査読論文ではない。NaN定数と算術のGVNの観測差が主題。遅延正規化について本文の関連commentを読んだ。
- [Wasm Rationale](https://github.com/WebAssembly/design/blob/main/Rationale.md): 設計資料のNaN関連説明を確認。全節読了ではない。
- [Canonical ABI](https://raw.githubusercontent.com/WebAssembly/component-model/main/design/mvp/CanonicalABI.md): Introduction、trap/lockdown規則、storeの説明を確認。mainの2026-10-24取得内容で、全concurrency規則の監査はしていない。
- [Component Model Explainer](https://github.com/WebAssembly/component-model/blob/main/design/mvp/Explainer.md): resource、own/borrow、post-return、Component Invariantsを確認。trap後内部状態が観測不能という規則が所有権案の動機を弱める。
- [CM issue644](https://github.com/WebAssembly/component-model/issues/644): zero-copy object modelの提案。bulk method、region borrow、optimizer recoveryの説明を検索本文で確認。未実装を含む提案で標準ではない。
- [US11477258B2](https://patents.google.com/patent/US11477258B2/en): Serialization of objects using multiple serialization algorithms。検索取得の共有handle/immutable object判定の説明のみ。全請求項は未読で、抵触や新規性の法的判断に使わない。

## fuel案に近い研究

1. Van Chan Ngo, Mario Dehesa-Azuara, Matthew Fredrikson, Jan Hoffmann, **Verifying and Synthesizing Constant-Resource Implementations with Types**, IEEE S&P 2017（査読済み）。[会議PDF](https://www.ieee-security.org/TC/SP2017/papers/408.pdf)。Abstract、§IIIの攻撃モデル、§IVの定資源型規則とpotentialを読んだ。総資源消費を等しくする型検査・合成が先行する。観測を終了時総量に限定する記述があるが、それだけでこちらの特許新規性は確立しない。評価表全体・Agda証明は未検証。
2. Blake Regalia, Ben Adams, **SNIP-50: Evaporation: Privacy for Wasm Execution Gas**, 2023-04-28作成、Draft仕様。[原文](https://github.com/SecretFoundation/SNIPs/blob/master/SNIP-50.md)。仕様・reference implementation・accuracy・callback・hard-coded targetの節を読んだ。check_gasとgas_evaporateで末尾の総量を揃える。Wasm gas privacyそのものは明確に既知。実network上の実験は行わない。
3. [Oasis Sapphire Security / Gas Padding](https://docs.oasis.io/build/sapphire/develop/security/): 開発者向け技術資料。padGas、最悪費用を上回るtarget、外部callとtransaction-sizeの限界を確認。取得時点の説明で日付固定版ではない。
4. Meng Xu, **Constant-Gas Programming for Confidential Smart Contracts**, PLAS 2026採択。[公式採択要旨](https://plas26.github.io/accepted.html)。2026-11-19開催予定であり調査日に発表済みとは書かない。Coga、EVM storage更新のsemantic class、M+ oracle、proof-carrying toolchainの要旨のみ読んだ。本文・code未取得。中間観測とproofを扱う近接研究として要追跡であり、未読の詳細を推測しない。
5. **US20250335260A1, Schema-based resource allocation for request processing**, 2025公開出願。[本文・請求項](https://patents.google.com/patent/US20250335260A1/en)。請求項1–11、schema scale factorとWasm fuelの説明を読んだ。queryのfield/data shapeから割当を拡大する内容。秘密に依存しない累積prefix予約との同一性はこの読了範囲では確認していないが、schema由来予算を広く新規としない。権利状態や全familyは未監査。

残る最も強いReject理由は、累積最悪費用の差分予約が、既存のamortized resource analysisと定量的side-channel対策を特定IRへ適用しただけと評価されることである。自作例の改善率だけではこの反論を解消できない。
