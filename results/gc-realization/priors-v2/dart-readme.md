# Benchmarks Results for Wasm

These are the current benchmark results created via
```
./run.sh --wasm --d8
./run.sh --wasm --jsc
./run.sh --wasm --jsshell
```

Benchmark Name                                    |         D8     |         JSC    (vs D8) |       JSShell  (vs D8)
------------------------------------------------- | -------------- | ---------------------- | ----------------------
FluteComplex.TimeToMain                           |    53018.00 us |   188548.00 us  (3.56) |   253074.00 us  (4.77)
FluteComplex.TimeToFirstFrame                     |   151018.00 us |   471548.00 us  (3.12) |   369074.00 us  (2.44)
FluteComplex.AverageBuild                         |       94.00 us |      891.00 us  (9.48) |      324.00 us  (3.45)
FluteComplex.AverageDraw                          |     6925.00 us |    51995.00 us  (7.51) |    19252.00 us  (2.78)
FluteComplex.AverageFrame                         |     7019.00 us |    52886.00 us  (7.53) |    19576.00 us  (2.79)
--- | --- | --- | ---
ParseCpuSamples.FromBrowserStringViaBrowserJson   |   551750.00 us |  1330000.00 us  (2.41) |   911000.00 us  (1.65)
ParseCpuSamples.FromBrowserString                 |  1490000.00 us |  4374500.00 us  (2.94) | 11786500.00 us  (7.91)
ParseCpuSamples.FromBrowserBytes                  |  1272500.00 us |  3718500.00 us  (2.92) | 11223000.00 us  (8.82)
ParseCpuSamples.FromDartBytes                     |  1166000.00 us |  2683500.00 us  (2.30) |  2723000.00 us  (2.34)
ParseCpuSamples.FromDartString                    |  1059500.00 us |  3284000.00 us  (3.10) |  3015500.00 us  (2.85)
--- | --- | --- | ---
WasmDataTransfer.FromBrowserString.10             |        0.18 us |        0.74 us  (4.16) |        0.31 us  (1.76)
WasmDataTransfer.FromBrowserBytes.10              |        0.27 us |        0.73 us  (2.66) |        1.60 us  (5.84)
WasmDataTransfer.ToBrowserString.10               |        0.12 us |        0.50 us  (4.01) |        1.93 us (15.61)
WasmDataTransfer.ToBrowserBytes.10                |        0.15 us |        0.50 us  (3.45) |        1.45 us  (9.96)
WasmDataTransfer.FromBrowserString.1KB            |        8.31 us |       13.95 us  (1.68) |      116.63 us (14.03)
WasmDataTransfer.FromBrowserBytes.1KB             |        2.92 us |       13.04 us  (4.46) |      117.40 us (40.16)
WasmDataTransfer.ToBrowserString.1KB              |        3.71 us |       18.58 us  (5.01) |      152.19 us (41.04)
WasmDataTransfer.ToBrowserBytes.1KB               |        6.72 us |       11.34 us  (1.69) |      112.99 us (16.81)
WasmDataTransfer.FromBrowserString.1MB            |     9383.89 us |    14228.19 us  (1.52) |   120000.00 us (12.79)
WasmDataTransfer.FromBrowserBytes.1MB             |     3215.89 us |    12700.00 us  (3.95) |   118882.35 us (36.97)
WasmDataTransfer.ToBrowserString.1MB              |     3396.85 us |    18544.64 us  (5.46) |   154846.15 us (45.59)
WasmDataTransfer.ToBrowserBytes.1MB               |     2044.00 us |    11318.68 us  (5.54) |   115333.33 us (56.43)
--- | --- | --- | ---
NonDevirtualizedList                              |       15.58 us |       49.75 us  (3.19) |       47.78 us  (3.07)
MatrixMultiply                                    |      873.33 us |    10527.36 us (12.05) |      854.00 us  (0.98)
VectorTransform                                   |      358.50 us |     5210.00 us (14.53) |      370.50 us  (1.03)
setViewMatrix                                     |      253.83 us |    10190.00 us (40.14) |      894.67 us  (3.52)
aabb2Transform                                    |      776.00 us |    17573.91 us (22.65) |     1626.67 us  (2.10)
aabb2Rotate                                       |      631.75 us |    15792.31 us (25.00) |     1434.03 us  (2.27)
aabb3Transform                                    |     1509.00 us |    34810.34 us (23.07) |     2938.67 us  (1.95)
aabb3Rotate                                       |      894.00 us |    27240.00 us (30.47) |     2358.75 us  (2.64)
Matrix3.transform(Vector3)                        |     5291.21 us |    95409.09 us (18.03) |     6880.00 us  (1.30)
Matrix3.transform(Vector2)                        |     3281.86 us |    49357.14 us (15.04) |     3907.34 us  (1.19)
Vector2()                                         |    16881.36 us |   505250.00 us (29.93) |    37127.27 us  (2.20)
Vector2.zero()                                    |    17245.76 us |   294571.43 us (17.08) |    24402.44 us  (1.41)
Vector2.array()                                   |    20230.00 us |   712666.67 us (35.23) |    52205.13 us  (2.58)
Vector2.all()                                     |    14695.65 us |   510250.00 us (34.72) |    41937.50 us  (2.85)
Vector2.copy()                                    |    36109.09 us |   526500.00 us (14.58) |    57314.29 us  (1.59)
Vector2.fromFloat32List()                         |     8283.90 us |   109947.37 us (13.27) |    14818.84 us  (1.79)
Vector2.fromBuffer()                              |    17252.17 us |   327571.43 us (18.99) |    39411.76 us  (2.28)
Vector2.random()                                  |    43478.26 us |  1135500.00 us (26.12) |    97095.24 us  (2.23)
Vector2.setFrom()                                 |    13964.54 us |   223300.00 us (15.99) |    32500.00 us  (2.33)
Vector2.dot()                                     |    22109.89 us |   524250.00 us (23.71) |    36509.09 us  (1.65)
Matrix4TweenBenchmark1                            |    16827.87 us |   902000.00 us (53.60) |    86416.67 us  (5.14)
Matrix4TweenBenchmark2                            |    13288.59 us |   745333.33 us (56.09) |    71892.86 us  (5.41)
Matrix4TweenBenchmark3                            |    14057.97 us |   749000.00 us (53.28) |    73107.14 us  (5.20)



# Benchmarks for WasmGC

This repository contains benchmarks for WasmGC based on the Dart2Wasm compiler.

## (Optional) Compling the benchmarks

For ease of use, the repository already contains compiled benchmarks under
`benchmarks-out`. So this step is optional.

To compile the benchmarks, ensure you have the Dart SDK installed (see
[dart.dev](https://dart.dev/get-dart)) and available in `PATH`.

Then you can compile them via
```
% ./compile.sh
```
on a linux machine.

## Running the performance benchmarks

The benchmarks can be run via
```
% ./run.sh
```
on a linux machine.

When changing `third_party/wasm-opt` binary one can re-optimize the performance
benchmarks with the new binaryen via
```
% ./reoptimize.sh
...
% ./run.sh
```

(For ease of use and reproducability, we have checked-in command-line versions
of the JS/Wasm runtime (e.g. D8) in repository under `third_party/*`)

## Running size benchmarks

The size benchmarks can be run via
```
% ./run_size.sh
```
on a linux machine.

(For ease of use and reproducability, we have checked-in
`third_party/wasm-opt` binary)
