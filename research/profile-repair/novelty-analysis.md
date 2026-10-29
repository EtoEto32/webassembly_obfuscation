# 先行技術との差と請求項案

2026-10-24。**共通profileの相関を使う部分決定化の実装候補。特許新規性・進歩性は未確立。**

|資料|区分・読了範囲|近さと反証|
|---|---|---|
|[Wasm3 numerics §4.3.6](https://webassembly.github.io/spec/core/exec/numerics.html#relaxed-operations)|標準仕様、2026-10-23版。共通parameterの説明とswizzle規則を確認|最も直接的な先行。共通Rという機構は既存で、当研究の発明ではない。仕様を正確にSMTへ移しただけというReject理由がある|
|[Wasmtime deterministic execution](https://docs.wasmtime.dev/examples-deterministic-wasm-execution.html)|公式実装資料、全relaxed決定化・NaN正規化の説明|全命令を決定化する機能が既にある。特定観測に必要なsiteのみ選ぶ点が候補差分。今回のlocal50.0.1でも既存DET optionを実行した|
|Solar-Lezama, Tancau, Bodik, Saraswat, Seshia, [Combinatorial Sketching for Finite Programs](https://people.csail.mit.edu/asolar/papers/asplos06-final.pdf), ASPLOS2006, pp404–415|査読会議、abstract・Introduction・有限program定義・§5.2 QBF・§5.4 CEGIS|Boolean穴を有限programの仕様と照合して埋める一般原理が先行。Iの一般Boolean制約による非単調な選択もこの枠内に入る。論文のAES実験は追試していない|
|Joshi, Kroening, [Property-Driven Fence Insertion Using Reorder Bounded Model Checking](https://www.kroening.com/papers/fm2015-robmc.pdf), FM2015, pp291–307, DOI10.1007/978-3-319-19249-9_19|査読会議、abstract・導入・§4のhitting-set手法|不必要な全面抑制を避け、propertyに必要な箇所を反例から選ぶ目的が近い。Iは演算結果の共通profileと非単調な変更関係を扱うが、一般合成との差は弱い。性能を相互比較したわけではない|
|Gulwani, Srivastava, Venkatesan, [US8402439B2: Program analysis as constraint solving](https://patents.google.com/patent/US8402439B2/en), 優先2008-06-27、公開2013-03-19|特許。書誌・請求項1–18|invariant template、weakest precondition、制約変換等を請求する。制約solverでprogram性質を得る一般説明は既存。Iはループ不変式のtemplateやbinary-searchによるWP生成を実装していないが、これで新規性や非抵触が確定するわけではない|
|Udupa, Gulwani, [US10831451B2: Synthesized programming-by-example programs](https://patents.google.com/patent/US10831451B2/en), 優先2017-12-01、公開2020-11-10|特許。書誌・請求項1–19・CEGIS説明|例集合を拡張し、性能でrankしたprogramを再合成する構成。Iは既存binaryと共通profileから全入力queryを作るが、反例と費用を使う一般構成を新規とはできない。関連EP3717999/WO2019108466はfamily表示のみで全請求比較未実施|

追加探索は`relaxed SIMD global parameter optimization`、`relaxed SIMD correlation refinement`、`partial deterministic`、`counterexample program synthesis patent`等。厳密な同一名称が見つからないことを証拠にしない。審査履歴、引用の全追跡、全family、日本国での請求項比較、FTOは未実施。Googleの法的status表示から有効性を断定しない。

## 差分の候補

Iが具体化したのは、(1)binaryから共通profile familyを結び付け、(2)部分strict化で壊れる相関を保持したまま、(3)特定観測をDET基準へ揃える最小費用集合を求め、(4)出力binaryを別モデルで再確認する一連の限定手順である。25自作例では、独立siteモデル92箇所に対し14箇所で条件を満たした。

ただし、この4項は既存標準・CEGIS・既知最適化・translation validationの適用として説明できる。「既存手法の原理を超えた」証拠はまだない。性能差も小さく、手簡約には及ばない。主特許候補へ採用する判断は保留する。

## 技術的な請求項たたき台

**I1**: WebAssembly binaryの観測結果を所定の決定的profileへ一致させる変換方法であって、複数の緩和演算に共通する環境parameterを対応付け、各緩和演算を厳密演算に変更するかを示す選択変数を設け、前記共通parameterの全ての許容値と入力値における観測結果が前記決定的profileの観測結果に一致する選択変数の組を費用に基づき選定し、当該組に対応する演算を変更したbinaryを生成する方法。

**I2**: I1において、不一致となる入力及び環境parameterを求め、前記選択変数を記号のまま残した観測一致式を制約へ加え、複数選択変数間の等価関係又は排他関係を保持して再選定する方法。

**I3**: I1又はI2において、変更後binaryを再読し、変換時のsite番号に依存しないlane表現によって、共通環境parameter下の観測一致を再検査し、未対応又は未解決を適合として受理しない方法。

これは技術構成の記録であり出願可能性の保証ではない。最大のReject理由は「既知の共通parameter semanticsに一般の有限program合成を適用しただけ」である。I2の非単調制約もSKETCH等の一般式で表現できる。独立site近似に対する改善だけで進歩性を主張しない。

## 第三者コードと見直し後の追加反証

|資料|区分・読了範囲|今回への含意|
|---|---|---|
|[XNNPACK hardware-config](https://github.com/google/XNNPACK/blob/c754a15b2bed01e80679793cbe75ebc61312430f/src/configs/hardware-config.c)、同commitの[x8-lut config](https://github.com/google/XNNPACK/blob/c754a15b2bed01e80679793cbe75ebc61312430f/src/configs/x8-lut-config.c)と[u16 kernel](https://github.com/google/XNNPACK/blob/c754a15b2bed01e80679793cbe75ebc61312430f/src/x8-lut/gen/x8-lut-wasmpshufb-u16.c)|公開実装、対象probe・dispatch・lookup関数を読了、hash保存。査読論文ではない|共通profileを検出し、それに適合する差分表lookupを選ぶ実装が既にある。縮小転記は変更0で正しかった。Iの共通profile利用そのものを新規にできない|
|Arm astc-encoder [SSE vtable_prepare/lookup](https://raw.githubusercontent.com/ARM-software/astc-encoder/main/Source/astcenc_vecmathlib_sse_4.h)、[NEON版](https://raw.githubusercontent.com/ARM-software/astc-encoder/main/Source/astcenc_vecmathlib_neon_4.h)|公開実装、該当32/64entryの前処理とlookupを2026-10-24に閲覧。main参照でcommit固定しておらず、初公開日は未調査|SSEの差分表とNEONの通常表というarchitecture別の事前表現がある。表現による環境適合も一般には既存|
|Phitchaya Mangpo Phothilimthanaほか9名、[Swizzle Inventor: Data Movement Synthesis for GPU Kernels](https://lenary.co.uk/publications/swizzle_inventor.pdf)、ASPLOS2019、DOI10.1145/3297858.3304059|査読会議。abstract、導入、§4のcanonical reduction表現と目的関数、§5の探索空間を読んだ。評価全体は未精読・未追試|mappingを穴とした合成が先行。今回の有限係数表合成を「SIMD表現の自動発明」と広く請求する根拠はない|
|William W. Macy Jr., Eric L. Debes, Yen-Kuang Chen, Minerva M. Yeung、[US7739319B2: Method and apparatus for parallel table lookup using SIMD instructions](https://patents.google.com/patent/US7739319B2/en)、表示優先2001-10-29、公開2010-06-15|特許、書誌・請求項1–40を読了。family・審査履歴全体は未調査|複数registerに分けた表をshuffleして結果を結合する構成が先行。単なるSIMD lookupは差分ではない。サイトの有効/期限表示から法的判断をしない|
|Conrad Watt, John Renner, Natalie Popescu, Sunjay Cauligi, Deian Stefan、[CT-Wasm: Type-Driven Secure Cryptography for the Web Ecosystem](https://cseweb.ucsd.edu/~dstefan/pubs/watt%3A2019%3Act-wasm.pdf)、PACMPL3(POPL), Article77, 2019、DOI10.1145/3290390|査読論文、今回確認したのはabstract・書誌と導入範囲。機械化証明は未精読・未追試|情報流と時間漏洩対策の型検査が先行。今回のaddress trace検査をそれに相当する形式保証と呼ばない|

Swizzle Inventorの著者一覧はPhothilimthana、Archibald Samuel Elliott、An Wang、Abhinav Jangda、Bastian Hagedorn、Henrik Barthels、Samuel J. Kaufman、Vinod Grover、Emina Torlak、Rastislav Bodik。

80生成例の改善が意図的相関系列に限られたこと、NoWaSet非空219binaryに対象命令がなかったこと、XNNPACK既存構成が正しかったことを踏まえ、I1–I3の特許性を強める実用証拠は得られていない。見直し2の[I4–I5](compensation.md)も、既存の差分表・環境別表現・線形合成の組合せというReject理由が強い。両profileで動くことは示したが、新しい一般原理や既存方式に対する速度優位は示していない。
