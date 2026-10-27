# 零符号の遅延修復：実測

5 fresh processの各9batch中央値の中央値。範囲はprocess中央値の最小–最大で信頼区間ではない。共通Wasm loopを含むns/呼出し。phase seed37、通常入力と全零入力を別測定。

| kernel | 入力分布 | 方式 | ns | process範囲 ns | bytes | RSS中央値 KiB |
|---|---|---|---:|---:|---:|---:|
| fma | normal | plain | 2.207 | 2.143–2.225 | 65 | 37968 |
| fma | zero | plain | 2.207 | 2.201–2.209 | 65 | 37944 |
| fma | normal | eager | 4.159 | 4.049–4.180 | 121 | 38072 |
| fma | zero | eager | 4.190 | 4.179–4.253 | 121 | 38032 |
| fma | normal | deferred | 2.657 | 2.650–2.679 | 160 | 37988 |
| fma | zero | deferred | 4.452 | 4.349–4.483 | 160 | 37988 |
| fma | normal | residual | 2.193 | 2.165–2.253 | 205 | 38080 |
| fma | zero | residual | 5.105 | 5.077–5.130 | 205 | 38008 |
| horner12 | normal | plain | 6.097 | 6.065–6.129 | 135 | 37992 |
| horner12 | zero | plain | 6.030 | 5.902–6.086 | 135 | 37976 |
| horner12 | normal | eager | 26.361 | 25.999–26.637 | 713 | 38084 |
| horner12 | zero | eager | 41.916 | 41.491–42.089 | 713 | 38124 |
| horner12 | normal | deferred | 8.898 | 8.826–9.081 | 781 | 38212 |
| horner12 | zero | deferred | 32.932 | 32.482–33.161 | 781 | 38240 |
| horner12 | normal | residual | 6.591 | 6.511–6.622 | 892 | 38108 |
| horner12 | zero | residual | 35.339 | 35.205–36.293 | 892 | 38092 |
| rotation8 | normal | plain | 7.596 | 7.405–7.658 | 242 | 37988 |
| rotation8 | zero | plain | 7.580 | 7.380–7.619 | 242 | 37980 |
| rotation8 | normal | eager | 34.747 | 33.771–34.889 | 1173 | 38136 |
| rotation8 | zero | eager | 47.538 | 47.311–47.807 | 1173 | 38120 |
| rotation8 | normal | deferred | 11.927 | 11.612–11.959 | 1527 | 38104 |
| rotation8 | zero | deferred | 45.200 | 44.065–47.121 | 1527 | 38072 |
| rotation8 | normal | residual | 8.511 | 8.303–8.583 | 1754 | 38100 |
| rotation8 | zero | residual | 52.186 | 50.937–52.459 | 1754 | 38116 |

全方式のlinear memoryは0。RSSはNode/JIT等を含むprocess全体の最高値。binaryは共通wrapper追加前で、residualの元プログラムを含む。

| kernel | 入力分布 | deferred/eager | residual/plain | residual/deferred |
|---|---|---:|---:|---:|
| fma | normal | 0.639 | 0.994 | 0.826 |
| fma | zero | 1.063 | 2.313 | 1.147 |
| horner12 | normal | 0.338 | 1.081 | 0.741 |
| horner12 | zero | 0.786 | 5.860 | 1.073 |
| rotation8 | normal | 0.343 | 1.121 | 0.714 |
| rotation8 | zero | 0.951 | 6.884 | 1.155 |

80/120 processはbatch上限2^20に到達。10msに届かない条件も保存しており、短い通常計算のns値を単独APIの遅延へ外挿しない。

候補抽出の単発analysis_msはWABT readerを除く。元ソースを与えずに抽出するが、変換方式は知っており、zero修復の真正性は機械証明していない。候補の4件の零符号不一致と、元zero経路を残したresidual版の全条件一致を区別する。
