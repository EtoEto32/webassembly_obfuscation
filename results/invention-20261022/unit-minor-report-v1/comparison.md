# 行列式変換の実測比較

2026-10-22。main-v2、audit-v1、runtime-v2が主結果。

| 式 | 方式 | 実行 ns/回（process中央値の範囲） | O3 bytes | 読取・証明 ms | 記号計算 ms |
|---|---|---:|---:|---:|---:|
| bilinear | plain | 0.979 (0.953–1.010) | 54 | — | — |
| bilinear | unmixed | 86.884 (85.557–92.754) | 953 | 18.420 | 0.082 |
| bilinear | constant | 184.366 (184.181–188.228) | 1345 | 18.576 | 0.369 |
| bilinear | polynomial | 569.092 (567.770–570.816) | 3383 | 20.203 | 5.624 |
| bilinear | recovered | 1.409 (1.408–1.488) | 54 | — | — |
| horner | plain | 1.058 (1.056–1.113) | 57 | — | — |
| horner | unmixed | 115.144 (112.381–116.315) | 973 | 17.501 | 0.119 |
| horner | constant | 356.177 (355.872–357.043) | 2025 | 18.793 | 1.614 |
| horner | polynomial | 1020.752 (1009.741–1030.896) | 5722 | 23.156 | 13.004 |
| horner | recovered | 1.528 (1.513–1.589) | 66 | — | — |
| product | plain | 1.171 (1.155–1.235) | 63 | — | — |
| product | unmixed | 95.100 (92.696–101.961) | 1001 | 17.428 | 0.130 |
| product | constant | 208.844 (206.587–212.964) | 1502 | 18.289 | 0.523 |
| product | polynomial | 594.421 (589.532–616.882) | 3515 | 20.456 | 6.088 |
| product | recovered | 5.353 (5.352–5.663) | 180 | — | — |

| 式 | 実行 poly/plain | 実行 poly/constant | 記号計算 poly/constant | 読取＋記号計算の中央値和の比 |
|---|---:|---:|---:|---:|
| bilinear | 581.164 | 3.087 | 15.241 | 1.363 |
| horner | 964.848 | 2.866 | 8.059 | 1.772 |
| product | 507.712 | 2.846 | 11.629 | 1.411 |

```json
{
  "positive_conditions": 42,
  "positive_calls": 214032,
  "inputs": 5096,
  "positive_mismatches": 0,
  "positive_traps": 0,
  "negative_conditions": 6,
  "recoveries": 18,
  "recovery_conditions": 18,
  "model_cases": 7488,
  "regenerated": 42,
  "interpreter_calls": 336,
  "controls": 9,
  "processes": 45,
  "batches": 405,
  "short_batches": 25,
  "maxRSS_KiB_range": [
    35624,
    36204
  ],
  "transform_ms_range": [
    39.788400000000166,
    52.57859999999992
  ]
}
```

記号計算は同一Python process内11反復の中央値。読取はvalidation、WAT変換、kernel照合、8通りのparity rank検査を含む。コンパイル時間を含まない。解析器を開発した人間の時間は測っていない。
実行は各方式3 fresh process×9 batch。共通Wasm入力更新・checksum loop、warmup16,384回、batch目標10ms、最大2^24回。CPU affinity/frequencyは未制御。約1nsの通常式はこのloopとJIT最適化を含む値で、JavaScript API呼出しの時間ではない。
各行列式版は非公開linear memory 128KiB、元式・回復式は0。RSSはNode/JIT全体を含み、Wasmのみの消費量ではない。変換時間は各1回の生成・tool呼出し込みで分布推定ではない。
全18条件を回復。polyの解析本体には増加があるが、3小式での限定値である。同等の実行費用に調整した他方式、一般的な逆コンパイラ、人間の読解実験は未実施。大規模行列・多数入力へ外挿しない。
v1の速度測定はplain/recoveredが全てbatch目標未達だったため、capとwarmupを増やしたv2へ更新。v1の正当性件数や速度sampleは加算しない。
