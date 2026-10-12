# Residue-state cost and candidate decision

2026-10-12. Previous turn was progress: actual-binary coefficient recovery, corrected input selection, and continuation verification saved. This turn completes the current prototype's no-quotient cost comparison. It does not complete the broader research goal.

## Recorded benchmark

Node24.15.0/V8 13.6.233.17-node.48, CPU model reported by Node os.cpus() in raw.json. PowerShell CIM CPU query was denied; no permission or system-setting change was made. One process,11 rotated-order rounds,524,288calls per batch,256 fixed random input arrays,31 source iterations per call. Timings include JS/Wasm crossing and result arrays. No CPU pinning or frequency control. See protocol.md for calibration/warmup and limitations.

| artifact | median ms/batch | minimum | maximum |
|---|---:|---:|---:|
| normal raw |174.2351|169.1121|179.3533|
| normal O2 |173.1684|169.7993|184.8685|
| coefficient raw |572.2112|563.0644|601.3294|
| coefficient O2 |535.1870|522.2227|557.8563|

Ratio of O2 medians is approximately3.09, or209% extra elapsed time. Ratio of raw medians is approximately3.28. These are measured end-to-end sample costs on one environment, not universal overheads. Optimized file size increases from860to1,140bytes and coefficient variant additionally allocates a64KiB private memory page. All individual timings, checksums, binary hashes, calibration attempts, inputs and summary/CSV are saved. This benchmark does not reproduce an author's obfuscator or prove a statistical population effect.

## Decision across this candidate family

1. symmetric-state implemented integer symmetric reduction and eight Wasm samples,32,384 output comparisons without mismatch. The mathematical reduction is established machinery, so it is not a new-algorithm claim.
2. symmetric-recovery recovered a known simple quadratic family from public I/O. Because that API is preserved by any transformation, this result limits the benchmark's secrecy claim rather than distinguishing all possible obfuscators.
3. residue-state enabled lane-specific branches and class merges, but singleton classes directly exposed individual values.
4. residue-occupancy removed singleton classes for an explicitly constructed source family with three values in each of four classes. Correctness tests and routing invariant support that restricted construction; they do not provide an arbitrary-module transformer or wide practical coverage.
5. residue-roots found compatible values for196/256 format-aware observations at the declared budget (duplicate raw/O2 instances included);60 exhausted cases remain unresolved. Alternative values continued the computation in the fully recovered cases even when historical values differed. This undermines treating nonunique original-state recovery as protection by itself.
6. Current timing adds a factor of roughly3.09 afterO2, without a demonstrated compensating analysis-resistance benefit.

Decision: **do not adopt this concrete coefficient/residue representation as the requested new obfuscation algorithm**. The conclusion is a research-selection decision based on insufficient original mechanism/protective evidence and measured cost, not a proof that every related representation is insecure or already published. Preserve all code and partial/unresolved results. Do not inflate the source degree or lane count merely to exceed this recovery budget and call it a new algorithm.

## Next design constraints

Keep the actual objective: develop a distinct transformation, not a polynomial benchmark or deobfuscation project. A next candidate needs an explicit transformation rule beyond ordinary pointwise data encoding, fixed temporal cuts, or this quotient construction. It must protect a meaningful reconstruction target rather than labels that are irrelevant to computation, and be assessed against equivalent-program recovery as well as exact historical-state recovery. Broad prior-art frameworks do not automatically rule out every concrete new algorithm, but copying their mechanisms with a Wasm backend is insufficient.

No new candidate is declared adopted in this report. Goal remains active. The existing CSEC manuscript and original research artifacts were not edited. User threshold remains25% allowance remaining; most recent usage check20% used,80% remaining (shared account window).
