# Cost protocol2026-10-12

Use unchanged normal/quotient raw/O2 artifacts from residue-occupancy. Node process, one instance each. Same256 random inputs (last256 original inputs.json cases), always31 source rounds per call. Include JS-to-Wasm call, argument spread, and multi-result array; this is end-to-end call cost, not instruction-only timing. XOR all outputs; an odd4093-call checksum check precedes timing to avoid cancelling complete repeated XOR cycles. Strong output correctness was already checked in prior independent tests.

Warm all variants16,384calls. Calibrate O2 normal from4,096calls doubling until>=100ms or1,048,576calls; then identical call count for all four variants,11rounds, rotated order. Save every round before starting the next. Report full observations, median/range and order-statistic Q1/Q3 (indices2/8 in11sorted measurements). No pinning/frequency control/independent machine replication. No microarchitecture or statistical significance claim. This compares our generator and its no-quotient control only; no author obfuscator was reproduced.

Correctness/recovery conclusions must remain separate from timing. Increased cost or incomplete recovery attempts do not establish obfuscation quality. Do not mark the full goal achieved on benchmark completion.
