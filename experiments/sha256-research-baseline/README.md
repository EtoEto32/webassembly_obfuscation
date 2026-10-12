# SHA-256 research comparison substrate

2026-10-12 (Asia/Tokyo). **Overall research goal remains active and incomplete.** This directory supplies a previously missing, tested SHA-256 Wasm benchmark and a deliberately simple existing-MBA comparison. It does not invent or adopt a new obfuscation algorithm. Interim research assessment: Inconclusive with respect to novelty and superiority, not Complete or globally Blocked.

## Existing assets and reuse decision

Read the current repository, its initial Git commit, the sibling `C:/Users/ettotto/Documents/wasm-structured-encoding` repository and relevant candidate records. The sibling contains the earlier affine prototype and accumulated candidate work. Neither inspected repository supplied a dedicated reusable SHA-256 Wasm source/build/test harness. A filename search including ignored files did find sha.js under the acquired Wobfuscator corpus; its reviewed source is reused here. This is an inspected-scope statement, not proof that no SHA implementation exists anywhere in the corpus.

| Asset | Class | Reason and current verification |
|---|---|---|
| sha.js 2.4.11 `sha256.js`, `hash.js`, license, metadata | A | Copied unchanged with license; original hashes checked; 531 inputs agree with Node/OpenSSL. Runtime replaces only the two helper dependencies with Node builtins. |
| WABT 1.0.42 and Binaryen 133 | A | Existing executables reused; builds, validation, disassembly, O2/O3 and a clean rebuild succeeded. |
| Existing Node v24.15.0 | A | Executes all six binaries; V8 and OpenSSL versions recorded in results. |
| Earlier affine prototype and Wasm recovery/measurement scripts | B | Useful examples and comparison candidates; restricted semantics, no SHA coverage, not rerun here. They require adaptation and current validation before comparative claims. |
| Rounding residual, targeted-window and local-mixing observer experiments | C | Rejection/diagnostic evidence, not adopted algorithms. All 39 + 6 + 11 inventory entries match. This checks preserved files only, not rerun results. |
| Other rejected candidates inspected through their READMEs | C | Design constraints and failure history, not independently reproduced measurements this turn. |
| Historical Z3/Docker execution assumptions | B | Current Python 3.9 has no z3, the Python 3.12 environment also lacks it, and the old package directories are access-denied. Docker configuration/pipe also access-denied in this execution context. Existing results are retained; current SMT execution is unavailable through these paths. |
| Old successes treated as evidence of new algorithm novelty | D (that inference only) | They do not prove this goal. The artifacts themselves are retained. |

Reliability checklist: vendor and new runs identify exact code by SHA-256, tool versions, inputs, environment, comparison and metrics. New build/results were rerun in a fresh directory. Old inventories establish identity/integrity but do not establish current execution, hardware comparability or reproducibility; their numerical results remain reference evidence until rerun. The initial repository commit does not identify uncommitted experiments; manifests do.

## Implementation and semantics

`build.cjs` generates an ordinary SHA-256 implementation using the reviewed sha.js round formulas and constants. Padding, block iteration, all 64 rounds, chaining and digest output execute inside Wasm. Host code only copies message bytes and reads output. It is not a compression-only test.

Public ABI: write 0..1,048,576 message bytes at offset 1024, call `hash(length)`, read 32 big-endian digest bytes at the returned offset 512. Each call resets chaining state. Memory has 17 fixed pages. Scratch is private to the ABI in bytes 0..415; constants occupy 768..1023. Callers must preserve constants and avoid simultaneous/reentrant mutation. Input bytes and the following canary are preserved. Length is unsigned i32; values above the limit trap before any writes. General pointer aliasing, larger messages, streaming API and concurrent shared memory are outside this ABI.

All word arithmetic is modulo 2^32. The explicit byte swap reconciles little-endian loads/stores with SHA's byte order. The length cap means the high 32 bits of the padded 64-bit bit length are zero. Tail zeroing covers both possible padding blocks.

The existing-MBA comparison replaces 159 statically generated data additions with calls evaluating operands exactly once:

```wat
;; Before, instantiated throughout the generated SHA computation
(i32.add (local.get $x) (local.get $y))
;; After, body of the generated helper
(i32.add
  (i32.xor (local.get $x) (local.get $y))
  (i32.shl (i32.and (local.get $x) (local.get $y)) (i32.const 1)))
```

This displayed excerpt is explanatory; complete generated sources are `artifacts/plain.wat` and `artifacts/mba-add.wat`, with `plain-to-mba.diff`. The rule is the known identity x+y=(x XOR y)+2(x AND y) modulo 2^32. The helper introduces no memory effects or traps. The 159 count is static call sites, not runtime additions. Address calculations and loop bookkeeping are not transformed. This is a controlled elementary baseline, not an author-tool reproduction or a representative substitute for every stronger existing scheme. The generator is not an arbitrary-Wasm transformation pass.

## Results and boundaries of evidence

`plan.json` was saved before execution. Six binaries: plain/MBA × raw/O2/O3. Each passed 531 cases (3,186 comparisons): four known digests including one million `a`, every length 0..256, larger padding/block boundaries, 256 seeded lengths and the ABI maximum. Both vendored sha.js and Node/OpenSSL agree. Message bytes, canaries, repeated calls and four rejected lengths are checked. Corrupting a round constant gives a wrong digest and is detected. No whole-program formal proof is claimed.

A fresh build in `artifacts-recheck` produced identical hashes for all six binaries and again passed all 3,186 cases. These are repeated tests of the same cases, not 6,372 independent inputs. `artifacts/verify-used.cjs` preserves the first verification source; its only later change corrects a misleading comment about the mutation control. `artifacts-recheck` corresponds to the current verification source.

| Binary | bytes | 64 KiB median hash time, first run |
|---|---:|---:|
| plain raw | 3,128 | 231.222 µs |
| plain O2 | 3,097 | 219.844 µs |
| plain O3 | 4,990 | 190.175 µs |
| MBA raw | 3,311 | 486.191 µs |
| MBA O2 | 3,280 | 516.178 µs |
| MBA O3 | 7,031 | 323.453 µs |

Each timing is median of nine trials of 32 calls after 16 warmups. Raw times, 1 KiB results, CPU/runtime and the separate repeat run are saved. Host copy is excluded. Conditions rotate cyclically; nine trials do not give perfectly equal counts in every one of six order positions. No CPU isolation, uncertainty estimate or significance claim. These are baseline diagnostics, not new-method superiority evidence. Memory caps were not enforced; no large search was run.

`attack-plan.json` precedes `recover.cjs`. The attacker reads binaries, disassembles them and recognizes only the exact pure-local MBA pattern. No source variable map, generator or trace labels are supplied. Raw and O2 each yield one helper-body rewrite; O3 yields two local rewrites. O3 also contains inlined expressions outside this pattern, so two is not total removal. All three plain controls have zero rewrites. All six resulting binaries pass the 531 saved cases and rejected-length memory checks. Attack times are single diagnostics including external tool startup, not comparative performance statistics.

This supplies a concrete distinction: an MBA pattern can survive optimization yet be locally restored. It does not measure whole-program reconstruction or demonstrate resistance of the remaining expressions. Before/after attack WAT, local diffs and recovered binaries are in `artifacts/recovery`. Full optimizer outputs and raw-to-O2/O3 diffs are preserved. `mba-add.smt2` is a local identity query prepared for a solver; **it was not executed here**. Access failures do not count as protection.

## Sources checked

2026-10-12: searched `site.nist.gov FIPS 180-4 SHA-256 pdf` and opened the [NIST FIPS 180-4 PDF](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf), especially §6.2.2, to verify schedule/round structure and modular word semantics. These are standard SHA rules, not proposed inventions.

The additional search `SHA256 rescheduling round computation T1 T2 carry save architecture paper` returned possible hardware rescheduling work. No primary full text of those candidates was inspected here, so this search supplies neither a novelty judgment nor an implemented next candidate. The algorithm-level literature audit remains open.

## Reproduction

Requires Node, Python 3.10+ for audit, WABT 1.0.42 and Binaryen 133. No npm installation is required. Set `WASM_TOOLS_ROOT` if tools are elsewhere; expected subdirectories are documented in `build.cjs`. From the repository root, use a fresh output directory:

```powershell
node experiments/sha256-research-baseline/build.cjs experiments/sha256-research-baseline/fresh
node experiments/sha256-research-baseline/verify.cjs experiments/sha256-research-baseline/fresh
node experiments/sha256-research-baseline/recover.cjs experiments/sha256-research-baseline/fresh
```

Build and result scripts refuse to overwrite existing output. `audit.py` checks preserved old inventories and the two designated runs; it is a workspace audit, not needed to run the self-contained SHA example. `inventory.json` hashes the package. Before/after examples are identified by source and binary hashes in each manifest. Inputs, seed and expected digests are stored in `inputs.bin` and `inputs.json`.

## Completion audit and next bounded work

| Goal §13 requirement | Current evidence |
|---|---|
| 1. Independent technical principle | Missing. No accepted candidate. |
| 2. New algorithm mathematical definition | Missing; only known SHA/MBA rules specified. |
| 3. Reusable new Wasm transformer | Missing; this generator is baseline infrastructure. |
| 4. New algorithm applied to SHA-256 | Missing; ordinary SHA and existing-MBA comparison now available. |
| 5. New algorithm semantic preservation | Missing; baseline finite tests pass, SMT not run. |
| 6. Fair comparison including proposal | Incomplete; two baseline conditions only. |
| 7. Attack-metric superiority | Missing. No protected candidate evaluated. |
| 8. Proposal performance/size/optimization | Missing; baseline measurements only. |
| 9. Evidence-driven algorithm improvement | Missing for an adopted new principle. Harness work is not that cycle. |
| 10. Reproducible full research package | Partial: new substrate and past assets preserved, no final new-method report. |
| 11. Adopted-method before/after examples | Missing; existing-MBA examples and optimizer/recovery diffs available. |

This turn's progress is new runnable comparison infrastructure, repeatable verification and preservation checks. It is not merely a plan, but it also does not satisfy the original invention goal. No goal-complete or global-blocked state is justified.

Resource allocation for the next bounded cycle: at most three structurally distinct designs; 30 minutes of primary-source comparison and 20 minutes of mathematical/adversarial screening before implementation. At most one survivor receives a 30-minute prototype budget, then 20 minutes of attack/correctness checks. Reserve 10 minutes each for SHA integration, one evidence-driven revision, and artifact audit, extending only with concrete intermediate evidence and an explicit recorded budget revision. Per process: 30 seconds for builds/attacks; bounded proof queries with unknown separately reported. A rejected principle receives no full SHA benchmark. Failure of this bounded cycle means Inconclusive, not weakened success criteria.

The next design must change the computation representation or update rule beyond affine/polynomial recoding, dependency expansion, generic observer-guided search, or parameter changes already rejected. Use the existing full-trace and quadratic-recovery evidence as a negative gate. First define a specific protected reconstruction task and compare the concrete rule with its closest prior work. Only then integrate a survivor into this common SHA harness. Do not spend further turns polishing this baseline as a substitute for invention.
