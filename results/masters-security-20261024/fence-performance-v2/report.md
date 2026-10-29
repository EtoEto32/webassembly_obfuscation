# A: 実Component境界の性能

5 process中央値。手書き方式に対する時間比。単位µs。

|case|mode|median|IQR|ratio/manual|
|---|---|---:|---:|---:|
|read|generated-operation|47.669|2.634|1.032|
|read|manual-operation|46.183|1.429|1.000|
|read|generated-object|48.194|1.822|1.020|
|read|generated-global|46.617|3.133|1.005|
|copy|generated-operation|42.544|1.485|0.964|
|copy|manual-operation|44.709|2.156|1.000|
|copy|generated-object|43.868|0.870|0.956|
|copy|generated-global|45.730|0.541|1.014|
|batch0|generated-operation|41.255|2.107|0.960|
|batch0|manual-operation|42.962|3.101|1.000|
|batch0|generated-object|43.173|1.457|1.028|
|batch0|generated-global|40.711|0.965|0.941|
|batch1|generated-operation|43.251|2.204|1.011|
|batch1|manual-operation|43.195|1.168|1.000|
|batch1|generated-object|44.969|0.696|1.051|
|batch1|generated-global|44.093|0.984|1.021|
|batch8|generated-operation|46.294|2.684|0.976|
|batch8|manual-operation|45.526|0.638|1.000|
|batch8|generated-object|46.972|0.924|1.034|
|batch8|generated-global|45.135|1.470|0.980|
|batch64|generated-operation|58.996|2.430|1.081|
|batch64|manual-operation|56.256|1.457|1.000|
|batch64|generated-object|59.156|1.062|1.042|
|batch64|generated-global|56.328|1.227|0.993|
|optional0|generated-operation|41.318|2.273|1.019|
|optional0|manual-operation|40.558|0.200|1.000|
|optional0|generated-object|40.453|0.232|1.003|
|optional0|generated-global|40.263|1.530|0.987|
|optional1|generated-operation|39.575|0.923|0.989|
|optional1|manual-operation|40.659|1.328|1.000|
|optional1|generated-object|39.166|0.292|0.972|
|optional1|generated-global|38.761|1.950|0.979|
|idle|generated-operation|38.887|0.532|0.987|
|idle|manual-operation|39.626|0.562|1.000|
|idle|generated-object|38.044|0.329|0.973|
|idle|generated-global|38.522|1.717|0.995|

|mode|unsafe|false rejects|scenarios|
|---|---:|---:|---:|
|generated-operation|0|0|54|
|manual-operation|0|0|54|
|generated-object|0|11|54|
|generated-global|0|31|54|

同じ2 resourceを繰り返すlistであり、64独立資源ではない。RSSはruntime込みのprocess指標。新規性の証拠ではない。