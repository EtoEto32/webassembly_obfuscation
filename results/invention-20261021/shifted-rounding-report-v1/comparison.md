# 倍率に合わせた丸め格子：保存値の集計

4個の合成DAGを使う限定実験。復元成功を記録し、難読化としての優位は主張しない。

主32条件204,800呼出し、復元16条件102,400呼出しが一致。
量子化器16,380 probe、WABT 384 probe、48 binary再生成一致、5拒否対照。

## O3の実行時間（ns/呼出し）

各値は3 fresh processの中央値。各process内は9 batchの中央値。

| 入力分布 | kernel | plain | eager | grid0 | shifted | shifted / plain |
|---|---|---:|---:|---:|---:|---:|
| normal | multiply-add | 2.257 | 5.756 | 7.000 | 9.138 | 4.049 |
| normal | horner6 | 3.329 | 29.629 | 41.418 | 51.525 | 15.478 |
| normal | butterfly4 | 3.506 | 28.968 | 41.146 | 50.544 | 14.415 |
| zero | multiply-add | 2.266 | 5.714 | 4.949 | 6.192 | 2.733 |
| zero | horner6 | 3.380 | 29.766 | 18.111 | 23.661 | 6.999 |
| zero | butterfly4 | 3.326 | 28.496 | 25.723 | 28.308 | 8.511 |
| underflow | multiply-add | 25.428 | 34.929 | 10.645 | 12.182 | 0.479 |
| underflow | horner6 | 150.439 | 200.629 | 85.288 | 94.928 | 0.631 |
| underflow | butterfly4 | 168.973 | 254.451 | 65.722 | 77.662 | 0.460 |

## サイズと測定の限界

| kernel | plain bytes | eager bytes | grid0 bytes | shifted bytes |
|---|---:|---:|---:|---:|
| multiply-add | 65 | 177 | 336 | 419 |
| horner6 | 99 | 459 | 392 | 646 |
| butterfly4 | 128 | 673 | 444 | 777 |
| cancellation | 75 | 255 | 352 | 480 |

下記の範囲は条件ごとの中央値（変換時間のみ各条件1回）。

- 復元本体: [0.2229, 0.3397] ms。WABT読取: [16.027, 16.8234] ms。
- 読取・生成・compile/validateの合計: [35.7577, 42.0842] ms。O3時間は含まない。
- 最大process RSS: [37876, 38488] KiB。linear memoryは未使用だが、stack/JIT/heapの費用はある。
- 量子化器の再実行を独立した追加検体に数えない。4個のkernelを多数の実アプリと読み替えない。
- 高速な条件は呼出し数の上限に達して目標10ms未満のbatchを含む。細かな速度差は断定しない。
- underflow条件ではgrid0もshiftedより速い。倍率変更による保護効果や新規な高速化原理は示していない。
- CPU固定・周波数固定・hardware counter測定なし。CPFloatそのものとの性能比較ではない。
- [実験と再現手順](../../../research/shifted-rounding/README.md)、[先行性の対応](../../../research/shifted-rounding/prior-art.md)。
