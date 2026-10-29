# O3 comparison

Times include JavaScript calling and argument lookup costs. Analysis excludes WABT/parse and does not share a cache between repetitions.

|Kernel|Mode|Bytes|Median ns|Process median range ns|Analysis median ms|Analysis range ms|
|---|---|---:|---:|---:|---:|---:|
|range|plain|164|11.31|7.18–11.39|0.1019|0.0976–0.1784|
|range|normalized|552|12.33|11.85–12.61|0.1775|0.1730–0.2389|
|range|fused|232|11.77|7.72–12.19|0.1131|0.1065–0.1926|
|pair|plain|138|6.65|6.61–10.52|0.0966|0.0910–0.2082|
|pair|normalized|432|11.17|10.60–11.81|0.1452|0.1393–0.1630|
|pair|fused|232|9.13|7.68–11.85|0.1025|0.0992–0.1134|
|filter|plain|190|7.69|7.26–7.82|0.1540|0.1483–0.2718|
|filter|normalized|716|13.79|13.44–14.83|0.2693|0.2427–0.4012|
|filter|fused|316|9.44|8.29–13.39|0.1746|0.1671–0.2495|
