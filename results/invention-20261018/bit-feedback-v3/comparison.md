# Measured comparison (O3)

Runtime is the median of three process medians; each process uses 10,000 warmup calls and 9 x 10,000 timed calls. JS calling/input costs are included. Analysis is 1 warmup + 9 runs after parsing, including settling-bound verification and Boolean digest.

|Kernel|Variant|Bytes|Runtime ns|Process median range ns|Analysis ms|Analysis sample range ms|
|---|---|---:|---:|---:|---:|---:|
|arx|plain|78|6.51|5.07–21.02|12.095|11.922–12.703|
|arx|none0|158|24.14|23.90–24.30|12.192|11.638–12.884|
|arx|uniform17|257|75.28|68.27–76.88|15.752|14.943–19.785|
|arx|masked17|283|79.95|72.99–83.09|14.145|13.741–15.185|
|arx|matched17|158|33.20|32.99–36.10|13.446|12.257–13.649|
|arx|uniform29|246|75.92|72.38–80.17|14.517|14.223–14.664|
|arx|masked29|303|85.73|79.98–99.50|14.739|14.397–15.944|
|arx|matched29|158|34.23|33.62–35.24|12.080|11.769–12.761|
|blend|plain|80|20.76|8.02–21.21|23.208|22.922–23.496|
|blend|none0|158|23.47|23.37–23.72|23.245|22.915–23.494|
|blend|uniform17|248|65.21|63.19–67.45|24.770|24.302–25.196|
|blend|masked17|282|87.69|85.65–89.76|24.511|24.102–24.727|
|blend|matched17|158|32.21|32.08–33.04|23.306|22.129–36.505|
|blend|uniform29|253|80.45|76.64–95.62|24.808|24.518–25.527|
|blend|masked29|283|84.61|74.60–85.44|25.209|24.767–25.503|
|blend|matched29|158|33.45|32.96–36.23|23.128|22.837–23.603|
|carry|plain|71|19.92|6.29–19.95|47.879|46.283–48.319|
|carry|none0|139|21.93|7.58–22.27|48.063|47.835–48.684|
|carry|uniform17|236|60.36|60.19–60.56|50.899|50.515–52.808|
|carry|masked17|236|69.92|65.66–70.15|50.520|50.412–52.423|
|carry|matched17|139|29.16|28.14–29.27|47.998|47.581–51.268|
|carry|uniform29|230|57.80|57.08–57.95|49.769|49.572–50.307|
|carry|masked29|246|61.28|60.16–63.39|50.039|49.655–50.780|
|carry|matched29|139|27.12|26.79–27.18|48.020|47.500–50.420|
