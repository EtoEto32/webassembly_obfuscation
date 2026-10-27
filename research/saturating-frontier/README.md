# 飽和min-plus領域の分解消去

研究仮説のプロトタイプと反証実験。現段階で有効な新しい難読化方式とは認定していない。[設計・先行研究との差分候補](design.md)。

## 今回得た結果

`results/invention-20261018/saturating-frontier-v2` の4カーネル×未変換/展開方式を、`saturating-frontier-optimized-v1` でraw/O2/O3へ展開した。24バイナリ、199,512入力条件で返り値不一致・trapなし。境界値、一様32bit入力、飽和しにくい小入力を使用。一般の全入力同値性をテストによって証明したものではない。

|カーネル|元のmin/飽和加算数|平坦な係数式の演算数|公開wasmから再構成した演算数|
|---|---:|---:|---:|
|two-choices|3|7|3|
|four-choices|7|63|7|
|shared-input|5|11|5|
|cost-offset|7|9|7|

方式既知の攻撃は変換済みバイナリだけを読み、SIMD laneを係数集合へ持ち上げ、2項因子、共通単項式、座標別部分集合の分解を試す。4例すべてで元と同じ演算数の式を復元した。元の構文との完全一致を必要としない。根拠は `saturating-frontier-attack-v4/attack.json`。因数分解部分は各約0.24–0.72 msという単回計測で、WABT抽出時間は別記。時間の統計的優越を主張しない。

再構成式の再展開は抽出集合と一致し、独立したNode評価でも16,384入力条件で実wasmと一致。正規化した集合の一致は同値性の十分条件だが、全ての関数同値を認識する判定ではない。攻撃はraw生成プロファイルに対応し、最適化後一般のSIMDを解析するものではない。

初期攻撃v1は、accumulator/paddingの65535を不要項として除去できず、分解を見落とした。v2で修正し、v3で単位元との不要な加算を除去。v4で部分集合の因数分解を追加した。古い攻撃の弱さを保護効果に数えない。

性能は各20,000回warmup、20,000呼出し×9反復を保存。ただしJSのspread呼出し・入力配列参照込み、順序固定の予備測定であり、観測された小さい時間差を速度向上と解釈しない。線形memoryは使用しない。JITを含むプロセスメモリは未測定。変換時間とbytesは各manifest、入力と時間標本はchecks.jsonにある。

## 原因と判断

元のmin/addを係数集合に展開しても、生成された集合には小さいMinkowski和の構造が残る。既知の一般的な因数分解困難性は、この生成分布の困難性を保証しない。本構成の基本形は実用的な保護候補として不採用。飽和上限を変える、項数だけを増やす、laneを入れ替える改良でこの理由が解消したとは扱わない。

実装できた技術差は、剰余環のMBAではなく飽和した冪等半環の展開を使うこと。だが「分配展開とSIMD化の応用にすぎない」という新規性への反論を解消しておらず、保護効果も確認できなかった。今回の結果を成功した発明として論文へ書かない。研究全体のgoalはactive。

## 再現

WindowsでPython 3.9、Node 24.15.0、WABT 1.0.42、Binaryen 133を使用。repo直下`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を既定とする。別の配置は`WASM_TOOLS_ROOT`で指定できる。標準ライブラリのみで動作する。

repo rootから未使用の出力先で実行する。既存の実験ディレクトリは上書きしない。

```powershell
python research/saturating-frontier/compile.py build results/frontier-new-construction
python research/saturating-frontier/optimize.py results/frontier-new-construction results/frontier-new-optimized
& 'C:/Program Files/nodejs/node.exe' research/saturating-frontier/check.cjs results/frontier-new-optimized
python research/saturating-frontier/attack.py results/frontier-new-construction results/frontier-new-attack
& 'C:/Program Files/nodejs/node.exe' research/saturating-frontier/check-attack.cjs results/frontier-new-construction results/frontier-new-attack
```

単独の実バイナリ変換：`python research/saturating-frontier/compile.py transform INPUT.wasm OUTPUT.wasm`。

対応範囲：唯一の`run`関数がi32引数を`i16x8.splat`し、`i16x8.min_u`・`i16x8.add_sat_u`・定数で構成した純粋式のlane 0をi32で返すmodule。効果、任意のmemory、call、元のloop、一般のSIMD lane入力には未対応。非対応入力をそのまま成功扱いにせず拒否する。入力i32の下位16bitを使う元の挙動を保つ。
