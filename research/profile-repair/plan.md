# I: 共通実行profileを保つ部分決定化 — 実装前計画

2026-10-24。Hの通知・Fの予算会計と異なり、仕様上の共通環境parameterと部分変換の整合を対象にする。特許新規性は未確立。一般のCEGIS、program repair、property-driven fence insertionを新規とはしない。

## 仮説

Wasm3のrelaxed swizzleは共通R_swizzle∈{0,1}を使う。二つの同じswizzleのXORは両profileで0でも、片方だけstrict swizzleに変えるとR=1で0以外となり得る。従って各命令を独立の非決定変数にする解析は相関を失い、変更集合に関する単調性も一般にはない。

保護する戻り値（権限判断を表す純粋関数）について、元コードを全strict化した基準値と、部分strict化した全環境profileの値が全入力で一致する集合を求める。これは任意の既存実行の値保存ではなく、元コードの決定profileへ観測を揃える明示的な変換である。未変更時に不安定な判断の意味は変わり得る。対象subsetでは基準profileも元の合法動作である。

## アルゴリズム案

各relaxed命令に変更Boolean h_iを置く。候補集合の費用を最小化し、SMTで全入力と共通Rに対し基準値との相違を探す。反例x*,R*を得た場合、hを記号のまま残した **F(h,x*,R*)=F(all,x*,0)** という制約を追加する。単なる「この集合のどれかを変更せよ」ではなく、変更同士の等価・排他も表せる制約を用いる。全入力queryがUNSATなら終了、unknown/上限は成功扱いにしない。

## 最初の範囲

実.wasmをvalidationして読む。2個のi32引数から1個のi32を返す単一run、純粋な直線コード、i32演算/local、i8x16.splat→relaxed_swizzle→lane0抽出に限定。全laneを同じ値で埋める制限によりswizzleの正確なscalarモデルを作る。memory、host import、float、loop、thread、他のrelaxed命令は拒否。最大16site。既存のWAT構文readerを再利用し、対象subset検査を別途行う。

## 固定する比較・成功条件

全site変換、構文依存slice、独立siteモデル、共通profileモデルを比較。最初に2siteの非単調反例を実Wasmで確認する。小例では全2^n変更集合を独立検査し最小費用と比較。各変換binaryをvalidation、NodeとWasmtimeで境界・乱数入力照合。両profileを明示したstrictな模型binaryも別に生成して照合し、同じCPU上の2engineが全hardware選択を網羅したとは言わない。

命令数削減と時間改善を区別する。正しさの後にfresh process性能比較を行い、通常O3が取消し関係を既に除く場合も数える。手書き正しい部分変換と通常optimizerを強い比較相手にする。新規性が単に既存一般合成をWasmへ適用しただけなら特許主案に採用しない。

## 読了した根拠

- [Wasm3 numerics](https://webassembly.github.io/spec/core/exec/numerics.html#op-ivrelaxed-swizzle): R_swizzleの定義・lane規則。2026-10-23版を2026-10-24確認。
- [Relaxed SIMD proposal](https://github.com/WebAssembly/relaxed-simd/blob/main/proposals/relaxed-simd/Overview.md): Consistencyとswizzle節。概要の非決定性一般論と個々の現行operator規則を混同しない。
- [Wasmtime Config](https://docs.wasmtime.dev/api/wasmtime/struct.Config.html#method.relaxed_simd_deterministic): 全relaxedを決定化する既存option。表示51.0.0-dev、実験に使うlocal50.0.1とは区別。
- Joshi/Kroening, [Property-Driven Fence Insertion Using Reorder Bounded Model Checking](https://www.kroening.com/papers/fm2015-robmc.pdf), FM2015, pp291–307, DOI10.1007/978-3-319-19249-9_19: abstract・導入・minimum hitting set周辺を確認。一般の反例駆動で必要な抑制箇所を選ぶ原理は先行。
