# 実測比較（自動生成）

全75条件はcomparison.csvとsummary.json。以下はO3。時間はWasm内batchの1反復あたりで、ホスト呼出し時間ではない。中央値[Q1,Q3]、15反復。倍率はblockごとのplainとの比の中央値。

|カーネル|方式|bytes|ns/反復 [Q1,Q3]|時間倍率|復元演算数|
|---|---|---:|---|---:|---:|
|product|plain|220|1.276 [1.245,1.458]|1.000|0|
|product|output-only|211|1.030 [1.017,1.240]|0.817|1|
|product|random|239|1.484 [1.458,1.723]|1.165|1|
|product|frontier|239|1.546 [1.510,1.709]|1.209|2|
|product|mba|218|1.660 [1.464,2.087]|1.254|0|
|score-square|plain|226|1.218 [1.213,1.240]|1.000|0|
|score-square|output-only|257|1.518 [1.499,1.563]|1.243|0|
|score-square|random|214|1.585 [1.564,1.626]|1.279|0|
|score-square|frontier|257|1.521 [1.493,1.524]|1.231|0|
|score-square|mba|222|1.449 [1.422,1.459]|1.173|0|
|interpolation|plain|238|1.212 [1.208,1.214]|1.000|0|
|interpolation|output-only|238|1.229 [1.216,1.236]|1.015|0|
|interpolation|random|247|1.345 [1.332,1.355]|1.115|0|
|interpolation|frontier|244|1.247 [1.225,1.252]|1.027|1|
|interpolation|mba|235|1.626 [1.605,1.658]|1.341|0|
|cubic-product|plain|211|0.957 [0.937,0.994]|1.000|0|
|cubic-product|output-only|211|0.974 [0.957,0.989]|1.012|0|
|cubic-product|random|228|1.203 [1.183,1.225]|1.267|0|
|cubic-product|frontier|230|1.057 [1.037,1.059]|1.099|2|
|cubic-product|mba|213|1.300 [1.277,1.303]|1.359|0|
|determinant-control|plain|190|0.858 [0.856,0.876]|1.000|対象なし|
|determinant-control|output-only|190|0.858 [0.856,0.875]|0.999|対象なし|
|determinant-control|random|190|0.860 [0.857,0.884]|1.004|対象なし|
|determinant-control|frontier|190|0.858 [0.855,0.880]|1.001|対象なし|
|determinant-control|mba|190|0.858 [0.856,0.868]|0.999|対象なし|

メモリ: 全条件のWasm線形メモリは65,536 bytes。Node全体のpeak working setは起動・コンパイラを含む。モジュール固有の使用量とはみなさない。
Node peak範囲 41,532–42,428 KiB。

変換時間は別の60試行（4方式×5カーネル×3反復）。全生値はtransform-resources-sequential/results.json。生成メモリはPython親のみ、WABT子プロセスのpeakは未測定。

|方式|変換時間中央値の範囲 ms|Python peak範囲 MiB|
|---|---:|---:|
|output-only|69.11–86.24|17.67–17.82|
|random|67.75–90.18|17.68–17.81|
|frontier|71.27–123.17|17.69–17.84|
|mba|35.24–38.25|17.63–17.81|
