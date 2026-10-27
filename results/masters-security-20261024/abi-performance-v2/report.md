# 展開前検査の補助実験

5 process中央値。µs。treeは同じ予算を守る正しい非memo方式。

|case|mode|median|IQR|ratio/tree|
|---|---|---:|---:|---:|
|tiny|late|30.748|1.456|0.975|
|tiny|tree|31.588|1.402|1.000|
|tiny|memo|31.682|0.450|1.025|
|shared-accept|late|78.000|4.930|0.953|
|shared-accept|tree|77.360|2.622|1.000|
|shared-accept|memo|81.896|2.064|1.026|
|shared-deny|late|207.136|13.400|6.951|
|shared-deny|tree|30.178|1.214|1.000|
|shared-deny|memo|34.880|0.984|1.101|
|disjoint-deny|late|211.234|7.104|7.698|
|disjoint-deny|tree|28.318|1.290|1.000|
|disjoint-deny|memo|49.208|2.448|1.799|
|large-shared-deny|late|691.716|40.658|28.006|
|large-shared-deny|tree|25.918|0.616|1.000|
|large-shared-deny|memo|30.592|2.038|1.251|
|empty-leaves|late|505.434|8.896|0.997|
|empty-leaves|tree|516.540|19.404|1.000|
|empty-leaves|memo|515.846|9.440|0.970|