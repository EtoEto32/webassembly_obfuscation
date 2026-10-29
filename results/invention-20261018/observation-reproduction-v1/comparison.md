# 実測比較（自動生成）

全75条件はcomparison.csvとsummary.json。以下はO3。時間はWasm内batchの1反復あたりで、ホスト呼出し時間ではない。中央値[Q1,Q3]、15反復。倍率はblockごとのplainとの比の中央値。

|カーネル|方式|bytes|ns/反復 [Q1,Q3]|時間倍率|復元演算数|
|---|---|---:|---|---:|---:|
|product|plain|220|1.236 [1.213,1.327]|1.000|0|
|product|output-only|211|0.997 [0.994,1.018]|0.822|1|
|product|random|239|1.452 [1.419,1.494]|1.170|1|
|product|frontier|239|1.481 [1.465,1.504]|1.190|2|
|product|mba|218|1.410 [1.401,1.557]|1.160|0|
|score-square|plain|226|1.222 [1.213,1.248]|1.000|0|
|score-square|output-only|257|1.481 [1.471,1.485]|1.207|0|
|score-square|random|214|1.549 [1.532,1.567]|1.264|0|
|score-square|frontier|257|1.487 [1.459,1.489]|1.208|0|
|score-square|mba|222|1.418 [1.394,1.421]|1.151|0|
|interpolation|plain|238|1.193 [1.187,1.208]|1.000|0|
|interpolation|output-only|238|1.203 [1.202,1.216]|1.012|0|
|interpolation|random|247|1.338 [1.326,1.348]|1.116|0|
|interpolation|frontier|244|1.219 [1.218,1.233]|1.023|1|
|interpolation|mba|235|1.611 [1.592,1.626]|1.342|0|
|cubic-product|plain|211|0.943 [0.928,0.983]|1.000|0|
|cubic-product|output-only|211|0.979 [0.959,0.998]|1.019|0|
|cubic-product|random|228|1.191 [1.177,1.219]|1.267|0|
|cubic-product|frontier|230|1.057 [1.031,1.068]|1.117|2|
|cubic-product|mba|213|1.284 [1.271,1.303]|1.373|0|
|determinant-control|plain|190|0.840 [0.837,0.870]|1.000|対象なし|
|determinant-control|output-only|190|0.851 [0.839,0.857]|0.998|対象なし|
|determinant-control|random|190|0.841 [0.838,0.856]|1.002|対象なし|
|determinant-control|frontier|190|0.844 [0.839,0.856]|1.001|対象なし|
|determinant-control|mba|190|0.840 [0.839,0.859]|0.999|対象なし|

メモリ: 全条件のWasm線形メモリは65,536 bytes。Node全体のpeak working setは起動・コンパイラを含む。モジュール固有の使用量とはみなさない。
Node peak範囲 41,580–42,380 KiB。

変換時間は別の60試行（4方式×5カーネル×3反復）。全生値はtransform-resources-sequential/results.json。生成メモリはPython親のみ、WABT子プロセスのpeakは未測定。

|方式|変換時間中央値の範囲 ms|Python peak範囲 MiB|
|---|---:|---:|
|output-only|68.20–81.66|17.69–17.85|
|random|70.16–81.03|17.69–17.89|
|frontier|68.10–119.68|17.67–17.88|
|mba|33.95–36.22|17.65–17.84|
