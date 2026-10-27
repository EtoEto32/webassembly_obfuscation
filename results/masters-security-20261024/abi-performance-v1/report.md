# 展開前検査の補助実験

5 process中央値。µs。treeは同じ予算を守る正しい非memo方式。

|case|mode|median|IQR|ratio/tree|
|---|---|---:|---:|---:|
|tiny|late|28.932|0.328|0.881|
|tiny|tree|32.146|3.190|1.000|
|tiny|memo|32.408|0.320|1.011|
|shared-accept|late|73.888|2.738|0.891|
|shared-accept|tree|82.122|3.792|1.000|
|shared-accept|memo|81.254|5.322|0.958|
|shared-deny|late|206.304|2.910|5.116|
|shared-deny|tree|39.216|1.800|1.000|
|shared-deny|memo|34.236|1.380|0.885|
|disjoint-deny|late|210.150|16.368|5.777|
|disjoint-deny|tree|36.194|0.112|1.000|
|disjoint-deny|memo|48.246|4.298|1.412|
|large-shared-deny|late|690.612|68.290|25.668|
|large-shared-deny|tree|26.906|1.610|1.000|
|large-shared-deny|memo|30.268|1.154|1.191|
|empty-leaves|late|517.776|6.820|0.919|
|empty-leaves|tree|559.296|8.678|1.000|
|empty-leaves|memo|512.044|12.346|0.920|