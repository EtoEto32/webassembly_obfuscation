# アクセサを既存linkerとoptimizerで消す対照

2026-10-26、実行前。workload-v2ではcached-project/splitがsharedと近い時間だった。raw Wasm-to-Wasm accessorの呼出し費用も、既存のwasm-mergeとwasm-optで消える可能性がある。新しいinline手法を作らずBinaryen 133の既存CLIで確かめる。

同じproducer/accessor consumerをimport allowlistとGC checkerで検査後、libというmodule名でmergeし、通常O3で最適化する。`--closed-world`は使わない。exportされたinit/private-atを保持する。静的linkでconsumerを固定できる追加前提がある。任意のhot-plug hostや複数storeの同一性を保持する汎用linkerの保証とはしない。

65536行、1/8 pass、stride1、Node/Wasmtime、各3process、12warmup/11測定。merged-onlyとmerged-O3を測り、独立expected checksumとprivate-at(0)を確認する。v2の時間と比較するが別runであるため小差の優位性は主張しない。実行時admissionを含まないsetupをv2と直接比較しない。
