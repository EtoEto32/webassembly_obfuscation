# 復帰後の位置queryの実測

5独立process反復。比較する4方式は各16byte値を返す。位置はcallback後にcallerから取得。

|fixture|方式|us/call|全コピー比|
|---|---|---:|---:|
|fixed|full|4.218|1.000|
|fixed|materialize|4.280|0.989|
|fixed|segments|2.361|0.635|
|fixed|manual|2.067|0.475|
|indexed|full|3.761|1.000|
|indexed|materialize|3.798|1.068|
|indexed|segments|1.696|0.435|
|indexed|manual|1.430|0.382|
|branch|full|3.584|1.000|
|branch|materialize|4.136|1.175|
|branch|segments|2.548|0.725|
|branch|manual|1.071|0.296|
|metadata|full|3.782|1.000|
|metadata|materialize|3.715|0.920|
|metadata|segments|1.532|0.433|
|metadata|manual|1.377|0.404|
|loop|full|3.657|1.000|
|loop|materialize|6.587|1.844|
|loop|segments|3.868|1.118|
|loop|manual|2.461|0.645|
|copy|full|3.440|1.000|
|copy|materialize|3.954|1.166|
|copy|segments|2.295|0.637|
|copy|manual|1.508|0.438|
|fill|full|3.568|1.000|
|fill|materialize|4.103|1.150|
|fill|segments|1.504|0.480|
|fill|manual|1.512|0.388|
|helper|full|3.339|1.000|
|helper|materialize|3.797|1.137|
|helper|segments|1.292|0.407|
|helper|manual|1.107|0.303|

全8KiBのhashは計算しない。単一checksumを前倒しする方式はこのAPIを満たさない。事前に位置が既知なら、その位置だけを保存する方式が有力である。
自作microbenchmarkであり、実アプリケーション採用や特許新規性を確立するものではない。IQR・全反復・payload量はsummary.json。
