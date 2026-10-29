# 未対応featureによる初回中断

2026-10-26。Binaryen 133へ`--all-features -O3`を渡したため、最適化結果がcustom-descriptors proposalのexact heap typeを含み、Node 24.15で`invalid heap type 'exact', enable with --experimental-wasm-custom-descriptors @+58`としてcompile拒否された。Node runは0回。この失敗を安全性や保護効果の証拠に数えない。

原因は実験driverが必要以上の出力featureを有効化したこと。次版はMVP + reference-types + GCに限定する。残した2binaryは失敗の再現用であり主性能データではない。
