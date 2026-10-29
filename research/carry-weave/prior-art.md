# carry-save、MBA、圧縮木の先行性

2026-10-19に英語資料を検索し、以下の一次資料の該当箇所を読んだ。既知技法をWasmへ実装すること、名称を付けること、組合せ順序を変えることだけを新規性としない。

|文献|著者・年・発表先|読んだ範囲、提案・評価、限界|
|---|---|---|
|[Software Carry-Save: A Case Study for Instruction-Level Parallelism](https://perso.citi-lab.fr/fdedinec/recherche/publis/2003-PACT.pdf)、DOI [10.1007/978-3-540-45145-7_18](https://doi.org/10.1007/978-3-540-45145-7_18)|David Defour, Florent de Dinechin、2003、PaCT、LNCS2763:207–214。査読会議|概要、§2の表現、§3の評価説明を確認。余裕bitを設けた多倍長表現でcarry伝播を減らし、並列性を露出する。著者はGMP等との比較を報告。今回のword-level 3:2圧縮と同じ実装ではないが、software carry-saveの発想は既出。Wasm難読化の評価ではない。|
|[Data-Flow Transformations to Maximize the Use of Carry-Save Representation in Arithmetic Circuits](https://www.epfl.ch/labs/lap/wp-content/uploads/2018/05/VermaOct08_DataFlowTransformationsToMaximiseTheUseOfCarrySaveReresentationInArithmeticCircuits_TCAD.pdf)、DOI [10.1109/TCAD.2008.2003280](https://doi.org/10.1109/TCAD.2008.2003280)|Ajay K. Verma, Philip Brisk, Paolo Ienne、2008、IEEE TCAD27(10):1761–1774。査読誌|概要、§II、§III冒頭の圧縮器定義と配置議論を読んだ。算術と論理が混ざったdataflowを再構成して圧縮木の利用を増やす。著者はcritical path最大46%短縮、複数例で面積10–20%削減を報告。信号到着時刻により大きな圧縮木が不利になる点も述べる。本試作の実行器で再現した数値ではない。|
|[Automatic Datapath Optimization using E-Graphs](https://arxiv.org/pdf/2204.11478)、[大学の書誌](https://spiral.imperial.ac.uk/entities/publication/1d080ac7-567e-4371-9c1f-33fafa7e070e)、DOI [10.1109/ARITH54963.2022.00016](https://doi.org/10.1109/ARITH54963.2022.00016)|Samuel Coward, George A. Constantinides, Theo Drane、2022、ARITH。読んだ本文はarXiv v2、会議採択は大学repositoryで確認|概要、§II–IIIのSUM node、bitwidth、書換え・抽出の選択箇所を確認。等価なRTLをe-graphへ保持し、costに従って抽出する。最大71%の回路面積削減を著者が報告。carry-saveの露出と圧縮は既存最適化として扱われる。回路の面積効果をWasm保護へ転用しない。|
|[Simplifying MBA obfuscation with CoBRA](https://blog.trailofbits.com/2026/04/03/simplifying-mba-obfuscation-with-cobra/)|Kyle Elliott、2026-04-03、Trail of Bitsの技術記事。査読論文ではない|線形・半線形MBAの処理、mask、dataset評価、制限を読んだ。著者報告は73,066式中72,960簡約、106未対応。carry-sensitiveな残差やworklist予算の限界を明記。今回CoBRA自体を実行したわけではなく、この成功率を本試作への攻撃結果としない。|
|[US8161463B2 — System and method of interlocking to protect software—mediated program and device behaviors](https://patents.google.com/patent/US8161463B2/en)|Harold Joseph Johnson, Yuan Xiang Gu, Yongxin Zhou。掲載優先日2007-02-23、A1公開2008-08-28、B2公開2012-04-17。特許公報|MBAの説明、請求項1–2・8–12を確認。請求項1に、bitwise式の係数付き総和と元式の恒等式に基づく置換が記載される。式の分割・再合成という広い主張には直接の近接性がある。公報全体の実施可能性、現在の権利状態、侵害や特許性の判断は行っていない。|

検索例：`obfuscation carry-save`、`carry save compiler instruction scheduling software arithmetic`、`mixed boolean arithmetic mask patent partition`。検索で完全一致が見つからないことは新規性の根拠にしない。2026年の新しい資料も査読論文と区別して扱う。

## 差分候補と反証

今回の差分は、加算項を補集合maskへ分割し、片を異なるSIMD laneと圧縮段へ配置して、元の項の局所的なペアをなくす具体的な生成規則。しかし、分割とCSAはいずれも既知の恒等式で、配置はランダム選択に留まる。費用を増やす独立した計画原理はまだ得られていない。

実験では分割なしCSAより解析本体時間が増えた。これは測定された差であり、ゼロと扱わない。一方、出力全体の和を追うと探索なしに圧縮器と分割を順に戻せた。さらに、既存の圧縮木最適化とMBAの範囲を越える技術的な差を裏付けられていない。この二点を分けて記録し、主特許候補には採用しない。

最大のReject理由は「既知の恒等式を合成した合成例であり、追加費用がコード増大と直線的な式処理から来るだけで、既存手法に対する独立した保護上の利点が示されていない」。現在の実験はこの懸念を解消していない。
