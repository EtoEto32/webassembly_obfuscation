# 同一処理計画と分離した依存抽出の比較

5 process中央値、単位µs。1 KiBの入力ファイル、OS cacheあり、fsyncなし。

|case|mode|median|IQR|ratio/manual|
|---|---|---:|---:|---:|
|read|separate-manual|85.268|5.144|1.000|
|read|separate-generated|83.274|0.390|0.977|
|read|plan-generated|85.686|5.764|1.004|
|write|separate-manual|81.804|2.686|1.000|
|write|separate-generated|81.882|0.602|1.002|
|write|plan-generated|81.788|2.084|1.005|
|copy|separate-manual|93.772|0.876|1.000|
|copy|separate-generated|93.460|3.402|0.989|
|copy|plan-generated|93.664|0.518|0.999|
|batch8|separate-manual|188.668|4.146|1.000|
|batch8|separate-generated|188.252|3.974|1.013|
|batch8|plan-generated|189.216|2.554|1.003|
|optional1|separate-manual|90.088|0.936|1.000|
|optional1|separate-generated|89.204|1.864|1.001|
|optional1|plan-generated|89.230|1.922|0.992|
|idle|separate-manual|43.444|1.482|1.000|
|idle|separate-generated|44.370|1.444|1.006|
|idle|plan-generated|43.556|2.524|0.999|

全方式で36失効条件の誤判定0。新しい安全原理、第三者アプリケーションでの効果、汎用WIT対応を示す試験ではない。