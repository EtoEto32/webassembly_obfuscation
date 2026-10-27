# 時間変更・SIMD混載の先行性

調査日2026-10-19。以下は実際に読めた一次資料本文または著者の資料に基づく。特許公報は論文の査読区分とは別に扱う。本表は技術比較で、網羅的な特許性・権利範囲の結論ではない。

|文献|著者・年・発表先|読んだ範囲、提案と評価、限界|
|---|---|---|
|[Retiming Synchronous Circuitry](https://cseweb.ucsd.edu/classes/fa23/cse248-a/papers/retiming/Leiserson.pdf)、DOI [10.1007/BF01759032](https://doi.org/10.1007/BF01759032)|Charles E. Leiserson, James B. Saxe、1991、Algorithmica 6:5–35。査読誌|概要、導入、グラフモデル、retiming定義を読んだ。頂点の時刻変更に伴い辺のregister数を調整し、機能を保つ。最小周期・状態数に関する多項式アルゴリズムを提示。Wasm難読化の解析費用を測った論文ではない。時間対応の変更自体の先行性が強い。|
|[A Simple, Verified Validator for Software Pipelining (verification pearl)](https://xavierleroy.org/publi/validation-softpipe.pdf)、[著者書誌](https://xavierleroy.org/bibrefs/Tristan-Leroy-softpipe.html)|Jean-Baptiste Tristan, Xavier Leroy、2010、POPL、pp.83–92。査読会議|概要、§2–5、§7–8の関連箇所を読んだ。元と変換後のloopを記号評価で照合するvalidator。著者の試験では検証時間がpipelinerの5%未満で誤警報なしと報告。入力には変換前も必要で、単一バイナリの解除器ではない。記述時点でCoqによる全体の形式化は未完了。本実装がその証明を継承するわけではない。|
|[Exploiting Superword Level Parallelism with Multimedia Instruction Sets](https://groups.csail.mit.edu/cag/slp/)|Samuel Larsen, Saman Amarasinghe、2000、PLDI。査読会議|著者プロジェクトの概要・書誌を確認。独立したscalar処理をまとめるSLPの先行資料。本論文全体は今回精読しておらず、個別性能値や細部を推測して記載しない。|
|[All You Need Is Superword-Level Parallelism: Systematic Control-Flow Vectorization with SLP](https://commit.csail.mit.edu/papers/2022/pldi22-vegen.pdf)、DOI [10.1145/3519939.3523701](https://doi.org/10.1145/3519939.3523701)|Yishen Chen, Charith Mendis, Saman Amarasinghe、2022、PLDI、pp.301–315。査読会議|概要・導入と§5の選択箇所を読んだ。Predicated SSAによりblockやloop境界を越えてSLPを適用する。TSVCではLLVM vectorizer比の幾何平均1.04倍、17件で1.5倍超の高速化、18件で20%超の低速化を報告。依存によるvector化不能などの限界も記載。Wasm保護・適応的解除の評価ではない。|
|[Tamper-resistant code obfuscation with control flow breaking — US12670238B2](https://patents.justia.com/patent/12670238)|Antonio Nappa, Grant Stewart Goodes, Javier Lopez Gomez。掲載出願人Zimperium, Inc.。掲載出願日2025-12-02、登録公報日2026-06-30。特許公報|Justia上の公報本文転載で概要、SIMD/maskingを述べる説明、請求項1–5と関連する媒体・system請求項を確認。複数計算資源への命令割当、資源間jump、VMのinstruction vector等を含む。独立した性能実験の裏付けは今回確認していない。SIMD・maskを難読化に使う広い発想は既出。|

## 具体的な差分の評価

今回の実装は、単一Wasm関数内のdataflowを段ごとにずらし、fill/drainをlane maskで維持する。上記特許の資源間jumpとVM配備という構成をそのまま実装してはいない。一方、その相違だけで独立した新規性があるとはいえず、既知のsoftware pipeliningをWasm SIMDへ割り当てたという評価が最も大きな反証になる。

|主張候補|反証・実験上の限界|判断|
|---|---|---|
|異なる論理時刻を同時に処理する|retiming/software pipeliningの基本操作に含まれる|単独の新規性としない|
|複数のscalar更新をSIMDへまとめる|SLPと境界を越えるvector化が既知|Wasmへの実装だけでは不足|
|maskとlane置換で段順を隠す|mask値から回復でき、さらに依存鎖だけでも36/36回復|追加機構の費用対効果が未確認|
|O3に残る難読化|bitselectは残るが、適応的解析で逐次形を生成できた|残存を解析耐性としない|
|対象profileに対する正当な変換器|有限試験とモデルで支持。広いprofileや実プログラムは未評価|実装成果として保持|

検索は`obfuscation retiming software`、`obfuscation software pipelining`、`obfuscation temporal SIMD`、`SIMD obfuscation vectorization superword level parallelism`、`obfuscation vectorization patent`等を使用した。未読の検索要約に現れた関連文献は、内容を推測して新規性の根拠に加えない。今回は[既存の文献台帳](../literature-review.md)を更新する補足調査であり、WASMixer/Wobfuscator等の全評価を再実施したものではない。

査読で最も大きなReject理由は「既知の最適化の用途変更に留まり、狭い合成例で追加の解析費用を示せていない」。今回の適応的回復はこの懸念を強めた。ただし回復成功それ自体を、あらゆる難読化が無意味だという結論には使わない。
