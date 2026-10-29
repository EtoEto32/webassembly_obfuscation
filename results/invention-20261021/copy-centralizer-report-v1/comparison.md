# Copy-compatible encoding: measured workload cost

ns is median of 3 process medians, each from 9 batches. Includes write/read, loop and dispatch.

|profile|workload|plain ns|conjugate ns|native ns|native/conjugate|native/plain|
|---|---|---:|---:|---:|---:|---:|
|blocks16|sequence|2.853|53.065|4.531|0.085|1.588|
|overlap8|sequence|5.974|27.677|6.597|0.238|1.104|
|irregular8|sequence|6.948|22.441|8.162|0.364|1.175|
|allcells8|sequence|8.481|217.154|9.795|0.045|1.155|
|blocks16|dispatch|6.208|25.115|17.632|0.702|2.840|
|overlap8|dispatch|2.490|7.782|3.284|0.422|1.319|
|irregular8|dispatch|6.032|15.964|10.694|0.670|1.773|
|allcells8|dispatch|12.315|27.834|20.596|0.740|1.673|
