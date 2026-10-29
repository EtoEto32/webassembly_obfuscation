# Iの設計見直し2: 命令ではなく事前表現で環境差を補償

2026-10-24、実装前固定。XNNPACK型lookupの既存profile dispatchが既に正しいので、修復site削減を実アプリの新効果とは主張できなかった。そこで固定lookup骨格に対して、環境ごとの事前テーブルを合成する仮説を検査する。新しい第4原理とは数えない。

## 仮説と既知部分

byte tableの各16-byte列について、lookupのXORとswizzleをGF(2)の係数行列A_Rとして抽出する。各profile RでA_R E_R=Iを満たすE_Rを求め、同じlookup骨格へE_R Tを渡す。初期化時の公開profile probeによってE_Rを選び、処理loop中の分岐やsecret indexによるlinear-memory table loadを避ける。Gaussian elimination、profile probe、SIMD lookup、XOR差分encodingは全て既知である。これらを新発明と呼ばない。

具体的な差分候補は、標準が許す複数の意味の全てで成立する事前表現を自動生成し、表現と命令の部分strict化を一緒に検証する点。XNNPACK、Swizzle Inventor ASPLOS2019、US7739319B2、一般的な合成が近く、進歩性は未確立。

## 評価を固定

- n=16の既存lookup骨格、strict mask 0、全、先頭1箇所、交互の4形。2profileとnativeで実Wasmを生成する。
- 係数抽出は全16 high indexと16基底tableを列挙する。A_R E_R=Iを直接照合し、別byte演算モデルで全256 indexを照合する。特異行列は受理しない。新しい一般線形代数の定理とはしない。
- table初期化後の変更は禁止。元table[0,256)、encoded[512,768)、input[1024,66560)、output[131072,196608)、4pagesを固定。Nは16の倍数、0..65536。境界違反は書込み前にtrap。
- 表参照が入力indexによらないことはWasm-level address traceで検証する。JIT/native/cache/timingを含むconstant-timeの保証とは区別する。
- 対照は直接scalar lookup、全strict vector lookup、XNNPACK型のprofile1差分表。既存の表と同じものが出た場合は既存方式の再発見として記録する。
- 時間はtable初期化とbatch処理を分け、16/256/4096/65536byte、同一process内順序shuffle、5fresh process、warmup後15標本。中央値とばらつき、byte数、RSS、生成時間を記録。profile0強制実装はAArch64実機の代用と呼ばない。

性能差なし・既存encodingと完全一致・既知合成以上の差なしなら主特許候補には昇格しない。公開、push、外部コードへの変更は行わない。
