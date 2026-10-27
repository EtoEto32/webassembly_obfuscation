# 区間consumerの実測

5独立process反復、各100 warmup、300呼出し×9 batch。表はprocess中央値の中央値。方式間checksum一致。

|fixture|方式|us/call|全コピー比（対応反復の中央値）|保持payload合計|復帰後payload合計|
|---|---|---:|---:|---:|---:|
|fixed|full|12.537|1.000|1114112|0|
|fixed|materialize|13.240|1.066|136|1114112|
|fixed|segments|10.876|0.869|136|0|
|fixed|manual|11.266|0.899|136|0|
|fixed|hoisted|5.881|0.469|544|0|
|indexed|full|13.036|1.000|1114112|0|
|indexed|materialize|13.627|1.064|136|1114112|
|indexed|segments|10.581|0.812|136|0|
|indexed|manual|11.063|0.820|136|0|
|indexed|hoisted|5.966|0.464|544|0|
|branch|full|12.157|1.000|1114112|0|
|branch|materialize|14.323|1.164|272|1114112|
|branch|segments|11.072|0.895|272|0|
|branch|manual|10.539|0.854|136|0|
|branch|hoisted|6.031|0.496|544|0|
|metadata|full|12.458|1.000|1114112|0|
|metadata|materialize|13.963|1.124|136|1114112|
|metadata|segments|10.471|0.842|136|0|
|metadata|manual|10.432|0.837|136|0|
|metadata|hoisted|5.905|0.479|544|0|
|loop|full|12.552|1.000|1114112|0|
|loop|materialize|16.335|1.300|1114112|1114112|
|loop|segments|12.831|1.035|1114112|0|
|loop|manual|11.060|0.892|18423|0|
|loop|hoisted|5.976|0.481|544|0|
|copy|full|12.756|1.000|1114112|0|
|copy|materialize|13.510|1.070|18423|1114112|
|copy|segments|10.826|0.838|18423|0|
|copy|manual|11.330|0.875|18423|0|
|copy|hoisted|9.975|0.788|544|0|
|fill|full|13.412|1.000|1114112|0|
|fill|materialize|14.048|1.047|18423|1114112|
|fill|segments|10.915|0.812|18423|0|
|fill|manual|11.319|0.850|18423|0|
|fill|hoisted|10.424|0.779|544|0|
|helper|full|13.466|1.000|1114112|0|
|helper|materialize|13.021|1.007|136|1114112|
|helper|segments|10.440|0.777|136|0|
|helper|manual|10.747|0.790|136|0|
|helper|hoisted|10.425|0.784|544|0|

payloadは136入力分の合計。全コピーbaselineは復帰後の全量コピーを行わない。segments/manualはconsumer終了まで別writerを許可しない。
hoistedは再入前にchecksumを計算し論理的に4byteの結果を保持する。任意の旧値viewを提供しないが、このconsumerの契約を満たす。JS Number実体のメモリ量を4byteと主張しない。
本測定は同一機器・自作8KiB fixture。IQR/全反復はsummary.json。RSSは各process JSONにあるが方式単独のpeakを示さない。
