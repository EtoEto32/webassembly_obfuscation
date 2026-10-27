# A: 実Component境界の性能

5 process中央値。手書き方式に対する時間比。単位µs。

|case|mode|median|IQR|ratio/manual|
|---|---|---:|---:|---:|
|read|generated-operation|50.652|4.954|1.062|
|read|manual-operation|48.575|1.652|1.000|
|read|generated-object|47.037|0.686|0.976|
|read|generated-global|48.763|1.452|0.989|
|copy|generated-operation|47.267|7.148|1.098|
|copy|manual-operation|43.056|2.582|1.000|
|copy|generated-object|42.868|0.290|0.996|
|copy|generated-global|44.847|6.032|1.060|
|batch0|generated-operation|43.885|2.039|1.089|
|batch0|manual-operation|40.496|3.913|1.000|
|batch0|generated-object|44.133|3.445|0.998|
|batch0|generated-global|40.398|2.193|1.002|
|batch1|generated-operation|47.118|3.644|1.111|
|batch1|manual-operation|43.077|0.741|1.000|
|batch1|generated-object|44.050|0.886|1.024|
|batch1|generated-global|43.527|0.501|1.003|
|batch8|generated-operation|47.305|2.017|1.033|
|batch8|manual-operation|45.016|1.501|1.000|
|batch8|generated-object|47.246|1.316|1.063|
|batch8|generated-global|45.336|2.831|1.023|
|batch64|generated-operation|60.982|3.365|1.124|
|batch64|manual-operation|55.334|4.838|1.000|
|batch64|generated-object|59.541|1.439|1.067|
|batch64|generated-global|56.482|0.702|1.002|
|optional0|generated-operation|40.026|3.303|1.014|
|optional0|manual-operation|40.066|1.151|1.000|
|optional0|generated-object|39.841|0.211|1.003|
|optional0|generated-global|39.874|2.771|1.010|
|optional1|generated-operation|42.107|4.601|1.059|
|optional1|manual-operation|39.741|0.438|1.000|
|optional1|generated-object|39.153|0.449|0.993|
|optional1|generated-global|39.572|3.709|1.005|
|idle|generated-operation|40.913|8.034|1.073|
|idle|manual-operation|38.438|0.792|1.000|
|idle|generated-object|37.819|1.422|0.984|
|idle|generated-global|39.219|3.356|1.011|

|mode|unsafe|false rejects|scenarios|
|---|---:|---:|---:|
|generated-operation|0|0|54|
|manual-operation|0|0|54|
|generated-object|0|11|54|
|generated-global|0|31|54|

同じ2 resourceを繰り返すlistであり、64独立資源ではない。RSSはruntime込みのprocess指標。新規性の証拠ではない。