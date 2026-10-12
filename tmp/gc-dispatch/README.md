# B2: GC state dispatcher — rejected candidate

This directory contains a dedicated generator and a comparative rejection experiment, not a general Wasm obfuscator. See [REPORT.md](REPORT.md) for results and limits and [design.md](design.md) for the pre-experiment design.

From this directory, with Node.js 24.15.0, Binaryen 133 and Python/matplotlib 3.10.6:

```powershell
node build.cjs C:/path/to/binaryen-version_133/bin
node evaluate.cjs
node erase-gc.cjs C:/path/to/binaryen-version_133/bin ./artifacts
node verify-erasure.cjs
node report.cjs
python plot.py
```

Commands overwrite their current output files. Copy this directory before a new trial if the preserved results must remain unchanged. The initial short-warmup measurement and its source are archived separately; they are not part of the final timing table.

Key artifacts:

- `artifacts/manifest.json`: 20 binaries, SHA-256, size, build flags, tools, source hashes, Binaryen metrics.
- `artifacts/build-log.json`: build commands and outputs (original staging paths retained).
- `artifacts/correctness.json`: independent BigInt reference checks.
- `artifacts/timing.json`: 140 raw timing observations and measurement order.
- `artifacts/summary.json`: per-condition statistics and paired ratios.
- `artifacts/erasure/results.json`: source-free representation-erasure outputs and type/tag maps.
- `artifacts/erasure/verification.json`: original versus erased output comparisons.
- `artifacts/paired-timing-O2.png` and `.svg`: O2 timing observations.
- `inventory.json`: hashes at preservation time, not automatically refreshed on reruns.

All experiments are local, import-free and use ordinary computation. No CSEC manuscript or existing mining experiments were changed. Rejection of B2 is not completion of the overall research goal.
