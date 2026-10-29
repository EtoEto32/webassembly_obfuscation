# Carry-sensitive candidate selection: existing simplifier checked locally

2026-10-12. This is an evidence and comparison-environment milestone, **not a new obfuscation algorithm**. The independent research goal remains active. The previous SIMD turn was progress: it added runnable code and evidence against adopting that primitive alone. No accepted novel candidate currently exists.

## Why this changes the next design

The small-width synthesis experiments in `../independent-update-synthesis` did not justify a 32-bit lift. Correcting their coefficients would fix correctness, but would not resolve their novelty deficit. Therefore no additional version of that same family was implemented here.

A broader idea, lifting nonlinear state dynamics into polynomial observables and linear updates, also has substantial mathematical prior art. Anantharaman and Sule, *Koopman operator approach for computing structure of solutions and Observability of non-linear finite state systems*, arXiv:2010.10752v1 (2020), abstract and Sections 1–2 beginning, explicitly constructs a dual linear system and reduced invariant space for finite-field systems. This does NOT prove that every specific Z/(2^32) compiler construction is known; it does prevent claiming the general lifting idea as new. No speculative weighted-ring construction was implemented or claimed successful.

https://arxiv.org/pdf/2010.10752

The next useful test is whether candidate expressions with arithmetic/bitwise dependencies actually challenge a current, externally implemented simplifier while the original expression remains recoverable. CoBRA's publication describes remaining carry-sensitive cases, but its own diagnostic lists are not sufficient evidence of failure at the current commit. We built that commit and checked concrete pairs.

## Pinned implementation and environment

- CoBRA commit `af44b8ad7c8ec548d431463475e93b0118e77a29` (retrieved 2026-10-12).
- Source archive SHA-256 `448f9fda97f1f53488dd589002cd3e92826fb8b92821093abef67f9850d2c654`.
- Local Docker image `wasm-research-cobra:af44b8a`; image ID `sha256:70549175561ea1e090cefaefc24e671122b56492f1ea6951d3563e8c88befbe4`.
- CLI executable SHA-256 `b40cfc4c9e9b4912dbbf1b96f6ecfd932db07e4b90e8fab6360cb84c0195fe8a`.
- Ubuntu24.04, GCC13.3.0; exact base digest and package versions in environment.json. Dependencies use upstream pinned commits, retained in source/dependencies. Build log retained.
- Standalone CLI built successfully. LLVM plugin and upstream test suite were not built. Z3 was NOT linked into CoBRA; its default random spot checks are not formal verification. An independent local Z3 check is described below.
- Host Windows protection settings unchanged. Test containers have network disabled, read-only root, CPU1, memory512MiB, pids128, inner timeout25s. They remove themselves when finished. No external service or mining pool contacted for experiments. Download/build traffic only fetched public packages and sources.

CoBRA code is Apache-2.0. Bundled third-party datasets have separate terms, including GPL-3.0-only for the GAMBA aggregation. LICENSE and THIRD_PARTY_LICENSES are retained. Source snapshots are reference material, not instructions. No upstream code was modified.

## Preselected probes and result

Selected three two-variable cases (physical lines14,85,152 of `test/datasets/gamba/qsynth_ea.txt`) from upstream `test/verify/test_residual_characterize.cpp`. They were chosen before execution, not selected afterwards for a favorable failure. Added add, multiplication decomposition, and `x*y-(x&y)` controls.

For each of six cases, run both the supplied expression and unobfuscated target at widths4,32,64: **36 CLI executions**. The process exit code alone is NOT a success signal: CoBRA exits0 for `Unsupported:` as well. probe.py inspects that diagnostic and records returned text and operation counts separately.

Results: **30 returned without Unsupported; 6 returned Unsupported**. All six Unsupported runs were the unchanged `x*y-(x&y)` control (source and target are identical). This demonstrates why that status by itself is not evidence of obfuscation strength.

The three dataset cases returned compact forms at every width. At32bits:

| Dataset physical line | Original obfuscated expression operations | CoBRA result operations | Dataset target operations |
|---|---:|---:|---:|
|14|36|5|6|
|85|35|4|4|
|152|145|7|10|

Operation count here means Python AST binary/unary operators after safe parsing; it is NOT Wasm instruction count or runtime cost. In lines14/152 the source and target produced identical rendered results; line85 differed only in the order of an addition. Therefore these selected historical diagnostic examples do not justify building a new method around an assumed present failure. This is not a rerun of the entire500-expression dataset and does not disprove every aggregate result in DATASETS.md.

Output equivalence checks use an independently written, restricted Python AST interpreter with modular arithmetic at each node, not CoBRA's evaluator. For4bits all256 two-variable inputs are enumerated. For32/64bits each expression uses49 boundary combinations and2,048 seeded random inputs (seed90217+width). **53,400 output comparisons, no mismatches**. Source-vs-target checks also run before invoking the CLI. Small-width enumeration does not prove wide-width correctness.

Independent Z3 4.13.3.0 checks54 distinct input/target or output/target pairs: **46 unsat (equivalence proved within the specified bitvector semantics), 8 unknown at the3-second limit, 0 sat**. unknown is not a proof and is not evidence of obfuscation strength. In particular several64-bit source/target comparisons and two output/target comparisons remain formally unproved by this run. Their finite checks passed. proof-results.json identifies each case; do not report all expressions as formally proved.

Wall times include launching Docker and are not a performance comparison. Wasm lowering, binary-analysis resistance, general algorithm novelty, and comparisons against other tools have not been established here.

## Design consequences

1. A next candidate must specify a new construction rule, not merely reuse QSynth's complex expressions or its previously reported failure list.
2. Use simple original operations that the comparator demonstrably handles, and compare the same target before/after transformation. A difficult target or unsupported feature is not protection gained from a transform.
3. Do not use only tool return status. Measure whether a semantically correct compact form was recovered, with the verification status and parser coverage explicit.
4. Correlated arithmetic subexpressions are a possible design question, but creating correlations, increasing MBA depth, or feeding existing counterexamples into a generic search is not by itself a novelty argument. A concrete new identity/construction and closest-prior comparison are still required before adoption.
5. Check the intended32-bit semantics directly. An identity observed at4bits cannot be assumed to lift; use exact algebra or an independently checked word-width proof.
6. Keep CoBRA as a reusable comparator, not the sole definition of security. A future candidate must also be examined with different analyses and optimized Wasm.

## Reproduction and resumption

From this directory (PowerShell), after inspecting Dockerfile and upstream sources:

```powershell
& 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' build --progress=plain -t wasm-research-cobra:af44b8a .
& 'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\runtime-analysis-py312\Scripts\python.exe' .\probe.py
& 'C:\Users\ettotto\Documents\webassembly_obfuscation\.tools\runtime-analysis-py312\Scripts\python.exe' .\prove.py
```

Reproduction overwrites probe-results.json and proof-results.json; make a new experiment directory before rerunning to preserve this record. The existing local image can be reused without another build. `prove.py` accepts WASM_SYNTH_DEPENDENCIES to locate the existing Z3 installation. Binary/docker access may require the same sandbox approval used for this run.

No build or test remains running at this checkpoint. Next work should define and screen a concrete transformation against prior art, then use this existing comparator. Do not call setup work a novel algorithm or change the goal into a deobfuscation-only study. CSEC files untouched; no paper produced. Latest usage check:22% used/78% remaining; stop threshold remains the user's newer25% remaining instruction.

## Sources and scope checked

- CoBRA official project and fixed source: https://github.com/trailofbits/CoBRA/tree/af44b8ad7c8ec548d431463475e93b0118e77a29 . Read BUILD.md, DATASETS.md relevant GAMBA section, lifting methodology, residual diagnostics, CLI result classification, build configuration; compiled standalone CLI. Selected source snapshots and full archive retained.
- Developers' report dated2026-04-03: https://blog.trailofbits.com/2026/04/03/simplifying-mba-obfuscation-with-cobra/ . Used as a lead, not independent confirmation of its aggregate results.
- John Regehr, *Synthesizing Constants*: https://blog.regehr.org/archives/1636 . Opened while investigating reduced-bitwidth synthesis; no claim of a specific new lifting result derived from it.
- Koopman paper above: finite-field setting; do not silently substitute a power-of-two ring for a field.

Searches2026-10-12: program obfuscation bit width lifting synthesis Hensel; bitvector synthesis lifting small bitwidth solutions carry encoding; obfuscation Hensel; Carleman obfuscation; Carleman modular polynomial finite; Carleman nilpotent linearization; finite ring linearization polynomial iteration; Koopman finite rings; obfuscation linearization polynomial; polynomial obfuscation lifting; Koopman finite state linear representation polynomial; program obfuscation monomial. Non-primary hits were not used to certify novelty or security.
