# Alias circuit measurements

4000 warmups, 11 batches of 2000 calls, 3 fresh Node processes per condition. Median of per-process medians; host calls included.

|family|input optimization|mode|bytes|median ns|process median range ns|median peak RSS MiB|
|---|---|---|---:|---:|---:|---:|
|mix|raw|plain|47|20.40|20.20–21.00|43.72|
|mix|raw|alias|8040|4820.65|4742.70–4931.90|51.79|
|mix|raw|recovered|7637|93.05|92.40–99.95|44.08|
|mix|O2|plain|47|20.55|20.25–21.65|43.73|
|mix|O2|alias|4624|4681.60|4673.40–5165.55|51.81|
|mix|O2|recovered|6912|91.55|91.35–95.25|44.16|
|mix|O3|plain|47|20.40|20.35–20.85|43.81|
|mix|O3|alias|5496|4904.25|4862.50–4939.90|52.65|
|mix|O3|recovered|6551|175.35|169.95–175.85|44.41|
|carry|raw|plain|47|20.25|20.20–20.35|43.75|
|carry|raw|alias|8017|4722.60|4717.70–4783.70|51.67|
|carry|raw|recovered|7614|86.35|86.20–91.05|44.13|
|carry|O2|plain|47|20.50|20.35–21.75|43.79|
|carry|O2|alias|4864|4824.95|4787.75–5236.45|51.77|
|carry|O2|recovered|7251|90.35|90.30–92.60|44.17|
|carry|O3|plain|47|20.20|20.00–21.45|43.71|
|carry|O3|alias|5426|4813.10|4771.05–4919.40|52.82|
|carry|O3|recovered|6529|177.80|176.95–180.40|44.38|
|mask|raw|plain|54|20.45|20.25–21.85|43.91|
|mask|raw|alias|8912|5122.90|5108.45–5179.80|51.75|
|mask|raw|recovered|8507|95.80|95.40–96.25|44.12|
|mask|O2|plain|54|20.30|20.25–20.60|43.86|
|mask|O2|alias|4976|5176.90|5108.75–5212.50|51.70|
|mask|O2|recovered|7602|95.25|94.95–96.95|44.15|
|mask|O3|plain|54|20.95|20.45–21.70|43.77|
|mask|O3|alias|6002|5163.50|5000.25–5175.90|53.09|
|mask|O3|recovered|7431|182.85|181.45–186.55|44.46|

Recovered means scalar circuit emitted from that input optimization level; the emitted circuit was not optimized again.
RSS includes Node, JIT, GC, and harness. Zero linear memory does not mean zero heap usage.
The historical checks.json field heap_after_gc was sampled after timed calls; it is not a retained-heap-after-GC result. It is not used in this summary.
All values are descriptive microbenchmark results. No confidence interval or cost-matched superiority claim.
