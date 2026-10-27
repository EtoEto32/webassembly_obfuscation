# 同一処理計画と分離した依存抽出の比較

5 process中央値、単位µs。1 KiBの入力ファイル、OS cacheあり、fsyncなし。

|case|mode|median|IQR|ratio/separate manual|ratio/manual plan|
|---|---|---:|---:|---:|---:|
|read|separate-manual|83.122|10.656|1.000|0.981|
|read|separate-generated|84.918|1.780|1.068|0.998|
|read|plan-manual|84.492|4.484|1.020|1.000|
|read|plan-generated|83.504|1.144|0.994|1.010|
|write|separate-manual|81.666|1.830|1.000|1.007|
|write|separate-generated|81.184|1.228|1.012|1.007|
|write|plan-manual|81.134|1.112|0.993|1.000|
|write|plan-generated|81.692|0.086|1.001|1.007|
|copy|separate-manual|94.934|3.120|1.000|1.020|
|copy|separate-generated|93.514|5.480|1.001|1.028|
|copy|plan-manual|92.012|0.772|0.981|1.000|
|copy|plan-generated|92.452|3.430|0.984|1.000|
|batch8|separate-manual|190.228|2.400|1.000|0.994|
|batch8|separate-generated|186.588|1.866|0.979|1.001|
|batch8|plan-manual|190.164|4.550|1.006|1.000|
|batch8|plan-generated|187.892|3.066|0.999|0.994|
|optional1|separate-manual|90.224|0.688|1.000|0.995|
|optional1|separate-generated|90.074|0.076|1.006|0.993|
|optional1|plan-manual|90.824|0.988|1.005|1.000|
|optional1|plan-generated|90.828|2.272|0.999|1.001|
|idle|separate-manual|44.006|0.602|1.000|1.011|
|idle|separate-generated|43.744|1.032|1.010|1.021|
|idle|plan-manual|43.606|1.578|0.989|1.000|
|idle|plan-generated|44.140|0.750|1.003|1.018|

全方式で36失効条件の誤判定0。新しい安全原理、第三者アプリケーションでの効果、汎用WIT対応を示す試験ではない。