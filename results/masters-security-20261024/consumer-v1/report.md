# 区間consumerの実測

5独立process反復、各100 warmup、300呼出し×9 batch。表はprocess中央値の中央値。方式間checksum一致。

|fixture|方式|us/call|全コピー比（対応反復の中央値）|保持payload合計|復帰後payload合計|
|---|---|---:|---:|---:|---:|
|fixed|full|11.414|1.000|1114112|0|
|fixed|materialize|12.956|1.137|136|1114112|
|fixed|segments|10.959|0.955|136|0|
|fixed|manual|10.759|0.936|136|0|
|indexed|full|12.904|1.000|1114112|0|
|indexed|materialize|13.561|1.044|136|1114112|
|indexed|segments|11.230|0.848|136|0|
|indexed|manual|10.710|0.816|136|0|
|branch|full|11.123|1.000|1114112|0|
|branch|materialize|13.739|1.291|272|1114112|
|branch|segments|11.525|1.006|272|0|
|branch|manual|10.343|0.930|136|0|
|metadata|full|8.780|1.000|1114112|0|
|metadata|materialize|12.987|1.462|136|1114112|
|metadata|segments|10.812|1.231|136|0|
|metadata|manual|10.269|1.188|136|0|
|loop|full|11.382|1.000|1114112|0|
|loop|materialize|16.184|1.307|1114112|1114112|
|loop|segments|12.814|1.108|1114112|0|
|loop|manual|10.872|0.949|18423|0|
|copy|full|12.795|1.000|1114112|0|
|copy|materialize|13.621|1.016|18423|1114112|
|copy|segments|10.754|0.849|18423|0|
|copy|manual|10.869|0.854|18423|0|
|fill|full|13.052|1.000|1114112|0|
|fill|materialize|14.147|1.038|18423|1114112|
|fill|segments|10.936|0.838|18423|0|
|fill|manual|10.743|0.810|18423|0|
|helper|full|13.794|1.000|1114112|0|
|helper|materialize|13.750|0.997|136|1114112|
|helper|segments|10.405|0.752|136|0|
|helper|manual|10.265|0.751|136|0|

payloadは136入力分の合計。全コピーbaselineは復帰後の全量コピーを行わない。segments/manualはconsumer終了まで別writerを許可しない。
本測定は同一機器・自作8KiB fixture。IQR/全反復はsummary.json。RSSは各process JSONにあるが方式単独のpeakを示さない。
