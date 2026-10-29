# O3 comparison

Times include JavaScript calling and argument lookup costs. Analysis excludes WABT/parse and does not share a cache between repetitions.

|Kernel|Mode|Bytes|Median ns|Process median range ns|Analysis median ms|Analysis range ms|
|---|---|---:|---:|---:|---:|---:|
|range|plain|164|7.12|7.06–11.91|0.0968|0.0926–0.1582|
|range|normalized|552|11.63|10.92–11.95|0.1752|0.1721–0.1890|
|range|fused|232|8.65|7.49–8.74|0.1139|0.1101–0.5927|
|pair|plain|138|6.68|6.60–6.87|0.0973|0.0935–0.2154|
|pair|normalized|432|13.60|10.44–13.72|0.1475|0.1405–0.1602|
|pair|fused|232|12.81|7.72–12.91|0.1038|0.1004–0.1529|
|filter|plain|190|7.98|7.22–8.12|0.1503|0.1449–0.2666|
|filter|normalized|716|14.46|13.90–15.62|0.2545|0.2455–0.3635|
|filter|fused|316|8.26|8.25–8.95|0.1718|0.1673–0.2626|
