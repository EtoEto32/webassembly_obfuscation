# 継続捕捉による演算移送：新規性の事前判定

2026-10-12。非可逆残差案とは別の原理を探すための限定調査。
判定：以下の具体案は既存のCPS・効果ハンドラの利用に留まり、不採用。
難読化強度や容易な逆変換を棄却理由には用いない。

## 検討した規則と還元

純粋でトラップしない整数演算opと、その結果を使う評価文脈Cについて、
C[op(a,b)]を、a,bをタグのpayloadとしてsuspendし、ハンドラ側でopを
計算して捕捉された継続kへ結果を返す処理に移す。

    k = lambda r. C[r]
    handler(op_tag, a, b, k) = resume(k, op(a,b))

順序を保ち、各継続を1回だけ再開すれば元と同じC[op(a,b)]になる。
変わるのは演算の配置、制御の受渡し、環境の保持方法。
しかし上のkは通常のCPS継続そのもので、Wasmでスタックを捕捉しても
新しい意味保存関係は生じない。suspend/resumeを呼出しに戻せば元の配置を
復元できるが、復元可能性ではなく規則の先行例が不採用の理由である。
メモリ副作用、外部呼出し、トラップ、例外を含む再順序化の正しさは主張しない。

## 一次資料で確認した範囲

1. Kenny Zhuo Ming Lu, *Control Flow Obfuscation for FJ using Continuation
   Passing*, arXiv:2012.06340v2、2021-02-26。
   https://arxiv.org/pdf/2012.06340
   要旨、導入、Figure 3周辺、whileとtry-catchの変換説明を確認。
   逐次実行・分岐・反復を継続の組合せに移す難読化を明示している。
   すべての証明・著者実装は未検証。表紙の会議名・DOIにプレースホルダがあるため、
   正式会議論文の書誌情報としては扱わない。

2. WasmFX, *Typed continuations — Explainer*。
   https://wasmfx.dev/specs/explainer/
   primer、型、cont.new/resume/suspend/cont.bind、継続寿命、直接switchの
   提案部分を確認。文脈を捕捉して型付きpayloadとともにハンドラへ渡し、
   1回だけ再開する機構が既に記述されている。
   この文書の設計説明を、現行標準や手元のNodeの対応状況とは同一視しない。
   環境対応を調査・導入する前に新規性の判定で止めた。

3. Philips, De Koster, De Meuter, De Roover,
   *Dependence-Driven Delimited CPS Transformation for JavaScript*。
   https://soft.vub.ac.be/tearless/papers/vub-soft-tr-16-10.pdf
   要旨、PDGの説明、変換例の説明と§3.5の実装方針を確認。
   制御・データ依存から継続に含める文を選ぶ方法がある。
   したがって「全関数でなく必要な依存部分だけを捕捉する」という変更だけも
   新しい原理と主張できない。全変換の正しさを検証したわけではない。

## 結果と限界

今回の規則に独立した新しい意味保存の仕組みはなく、Level 3相当と判断。
継続を使うすべての将来の変換が既知だという結論ではない。
新しいWasm、Z3検証、性能・攻撃実験は作成していない。
非可逆残差案の既存Wasm試作・検証結果は変更していない。
研究全体では新規アルゴリズムの発見は未達成。
