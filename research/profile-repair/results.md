# 実測と判定

2026-10-24、Windows、Node24.15.0/V8 13.6、Wasmtime50.0.1、WABT1.0.42、Binaryen133、Z3 4.13.3。CPU等は各raw JSON。初期25例は自作fixture。後述の生成例・第三者資料の調査・縮小転記を区別する。

## 正当性と対照

- [主試験](../../results/profile-repair/probe-v1/results.json): 25例、836境界・seed乱数入力、5方式と明示的2profile binaryによる313,500値照合、不一致0。各選択の最終symbolic queryはUNSAT。共通profile方式は99site中14、独立site方式は92をstrict化。6site以下の21例では全184変更集合を照合し最小費用が一致した。
- [境界](../../results/profile-repair/boundary-v1/results.json): 2site例の全4変更集合・2明示profileとnative、36呼出し。片方のみstrict化はR=1で255又は1を返し、元と両方strictは0。nativeもR=1相当を観測。primitiveは全256×256入力、3binaryの196,608照合。valid Wasmの7非対応形、5不正weightを拒否、0siteを受理。0site/空weight処理をこの試験前に修正した。主v1の正入力は影響を受けない。
- [通常最適化](../../results/profile-repair/optimize-v1/results.json): 125binaryをO3・validation、104,500値照合、不一致0。合成器の狭いreaderはv128 local等を含む100形に未対応と報告し、成功に数えなかった。
- [独立symbolic evaluator](../../results/profile-repair/symbolic-v1/results.json): 前項の形を扱う別byte-lane評価器で、4保護方式×25例×raw/O3=200式がUNSAT、約6.2秒。全2^64入力と2profileの式に対する検査であり、parser/engine/solverを形式検証したものではない。
- [Wasmtime](../../results/profile-repair/cross-engine-v1/results.json): native/defaultと既存DET optionの各313,500、合計627,000値照合、不一致0。同CPUの設定差であり2種類のhardwareを用いた試験ではない。

上記は同じfixtureを複数方法で確認している。独立したアプリ数に合算しない。shared memory、trap、host副作用を持つprogramを評価したとはしない。

## 性能

[最初のJS境界測定](../../results/profile-repair/performance-v1/results.json)は5方式×5process。同一byteの方式間でも約10%差があり、参考値へ降格した。[修正計画](performance-plan.md)に従い、Wasm内共通loop、--no-liftoff、同process内shuffle、7fresh process、15標本×200000呼出し、2warmupで再測定した。[主性能](../../results/profile-repair/internal-performance-v1/results.json)。

|例|全strict ns/内部call|共通profile選択|手簡約|対応processの選択/全strict比の中央値|
|---|---:|---:|---:|---:|
|different_indices_pair|1.501|1.417|0.207|0.943|
|pair_and|1.468|1.429|0.202|0.975|
|pair_equal_guard|1.637|1.508|0.208|0.930|
|cancel_plus_other|1.875|1.792|0.202|0.957|
|xor_4|2.472|2.207|0.205|0.893|
|xor_8|3.970|4.053|0.203|1.022|
|xor_15|5.300|5.356|0.206|1.004|
|xor_16|5.287|4.877|0.206|0.920|

全25例の比は約0.893–1.022。同binary別instanceの較正比は約0.995–1.004。変更site削減に比例する速度改善ではない。手簡約25例は別symbolic検査でcanonical値との一致を確認し、多くで大幅に速かった。定数関数へ簡約できる例が多いので、一般サービスの性能改善率には使えない。メモリはprocess RSS/heap/maxRSSをrawへ記録し、関数別の追加割当量や新しいmemory節約とは主張しない。

合成の単発時間は約1.9–41ms、O3後binaryは共通profile選択38–213byte、全strict38–200byte。strictへ置くとopcode encodingが短くなるため、変更数を減らしてもbinaryは小さくならない。実時間最小化に校正した重みは未導入。

## 判断

支持されるのは共通profileを落とす近似に比べた変更数の削減と、部分変換の非単調性を扱う選択の正当性である。標準CEGISと異なる一般合成原理、実アプリでの優位、大きな性能改善、特許性は未確認。既存の全面DET設定は強い実用対照であり、単純な全strict+式簡約が勝つ点を結果に残す。

## 追加80例: 差が出る系列を限定

[固定した生成計画](generated-plan.md)に従い、seed2026102424で4系列×20を生成した。[主結果](../../results/profile-repair/generated-v1/results.json)は1,003,200値照合、不一致0。[O3](../../results/profile-repair/generated-optimize-v1/results.json)は400binary・334,400照合、不一致0、狭い合成readerの未対応330形。[別byte evaluator](../../results/profile-repair/generated-symbolic-v1/results.json)は640式UNSAT。[分類](../../results/profile-repair/generated-summary-v1/results.json)では全80のcanonical出力が非定数、全1,984変更集合の列挙で最小費用が一致した。

|系列|例数/site数|共通profileの変更数|独立siteの変更数|費用が減った例数|
|---|---:|---:|---:|---:|
|独立data/index|20/80|59|59|0|
|意図的な相関|20/80|33|56|13|
|前siteを使う入れ子|20/80|67|67|0|
|算術・bitwise・select|20/80|38|38|0|

合計197対220、合成時間中央値31.402ms。改善は相関系列だけであり、無作為な実アプリで同様の削減が生じる証拠にはならない。生成例の性能測定はしていない。

## NoWaSet: 対象命令がなかった

[NodeWasmStudy公式artifact](https://github.com/michelledaviest/NodeWasmStudy)のcommit `53118203addbc9d421deb83289c282dfe7f27173`に固定した。[inventory](../../results/profile-repair/nowaset-inventory-v1/results.json)からoriginal dumpだけをGit blob IDで重複除去し、220ファイル・131,210,382byteを取得した。元の公開説明にある217 moduleとの件数差の理由は未確認。全packageやDockerは実行していない。

[静的scan](../../results/profile-repair/nowaset-scan-v1/results.json)では218件が通常validationを通り、対象のRelaxed SIMD命令は0。prefix候補2件はdisassemblyで偽陽性と判定した。[追補](../../results/profile-repair/nowaset-followup-v2/results.json)で1件は非対応custom linking metadataを無視すればcore validationが通り、対象命令0。残る1件は0byteファイルだった。したがって非空219件には対象命令を確認できなかった。これは当該固定datasetの結果であり、現在のWasm全体の普及率ではない。

[28 detector対照](../../results/profile-repair/scan-controls-v1/results.json)は99実site、overlong opcode、custom section内の偽候補、整数immediate内の偽候補を区別した。scan成功、tool非対応、空入力を解析耐性へ加算しない。followup-v1はJSONのWindows既定文字コード読取りで停止し、UTF-8指定のv2で確認した。inventoryのtree欄がcommit応答IDを指していた点も追補へ訂正し、凍結済み結果は書き換えていない。

## XNNPACK: 既存の相関利用が成立

[固定sourceの記録](../../results/profile-repair/xnnpack-v1/source-provenance.json)、[実行結果](../../results/profile-repair/xnnpack-v1/results.json)。hardware probe、u16 lookupの16byte本体、scalar fallbackを縮小WATへ転記した。元C全体のコンパイルではなく、実x86 configはu32を選ぶ。tail、is_x86、init-onceを含む全libraryの検証とはしない。

任意table列とbyte indexの式で元構成は両profileで正しく、共通profileモデルは変更0、独立siteモデルはprobe1箇所のstrict化を選んだ。実Wasmは20変更条件×3profile×276table×16block=264,960呼出し、4,239,360出力byteを照合。元・全strict・probeのみ・最後のkernel siteのみは正しい。kernel先頭15箇所の単独strict化及びkernel全strict/probe未変更には反例がある。全memoryのoutput外変更は0。

既存の正しい構成を変更して壊した対照であり、XNNPACKの脆弱性を示したものではない。profile共有の活用は既に実装されているため、新規性の反証として重く扱う。

## 表現補償への見直し

[構成・請求項案・実測](compensation.md)。固定lookup骨格に対してprofile別の線形表現を生成した。63binaryの生成、別式30UNSAT、Node61,498,752byte、Wasmtime22,111,488byteの照合を確認。全strict版に対する大batchの速度差は既存XNNPACK型処理にもあり、新しい速度改善と主張できない。これ以上同じlookupを拡張して新原理の件数を増やさない。
