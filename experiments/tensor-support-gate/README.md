# Tensor basis changes: discovery without internal decoding matrices

2026-10-12, Asia/Tokyo. **Research assessment: Inconclusive; this construction is rejected for adoption.** The original invention goal remains active and unmet. This experiment examines a different representation from scalar rotation or polynomial encoding, but basis changes themselves have established prior art. It is not a newly invented obfuscation algorithm.

The previous turn was progress: three concrete designs, counterexamples and Wasm primitives were saved. Those experiments were family-aware diagnostics, not unknown-binary attacks. This turn does not retract their mathematical results, but explicitly tests whether private decoding correspondences are needed for a new candidate's reconstruction. A short inverse alone is not used as proof of general program recovery.

## Candidate rule and correctness

Work over R=Z/(2^32). For each Boolean wire v select an invertible 2×2 matrix M_v; an odd determinant is necessary and sufficient for the generated matrices. Encode bit b as the column vector M_v e_b, where e_0=(1,0), e_1=(0,1).

For a binary Boolean gate f with input wires a,b and output c, the ordinary truth tensor T_f has coefficients

    T_f[k,i,j] = 1 if k=f(i,j), otherwise 0.

Emit the eight-coefficient bilinear tensor

    U_f = M_c T_f (M_a^-1 ⊗ M_b^-1).

Its evaluation on encoded inputs gives M_c e_f(i,j), since the inverse matrices cancel their corresponding encoders. Addition and multiplication wrap modulo 2^32. This cancellation holds over this ring because the matrices have genuine inverses; it does not rely on treating the ring as a field. Compiler inversion happens only at generation time. At runtime the IR uses additions/multiplications of ordinary words and public coefficients.

The target DAG uses XOR/AND/OR gates, including ripple-carry word addition. Shared wires are read by multiple gates; a wire remains a vector associated with one Boolean value. It does not contract a general correlated tensor network or form arbitrary superpositions over complete internal assignments. Public input encoders and output decoder rows are included in the generated program, as required to accept/return ordinary bits without an external secret.

Intended protection: dense numerical tensors replace recognizable gate truth tables, while the internal basis matrices and logical gate labels are absent from the public artifact. Arbitrary labels and shuffled storage order prevent recovering those details merely from semantic node names or file order. Dependency edges are still explicit. This is the actual tested candidate, not an assumption that a later Wasm compiler would hide its graph.

The generic tensor compiler in `experiment.py:build` emits this rule for each binary gate. It is a limited DAG prototype, not an arbitrary-Wasm compiler. The source operation used for validation is

    F_w(x,y) = (rotl_w(x+y,7) XOR (x AND y))
               + (x XOR rotl_w(y,13))    mod 2^w.

It includes carries, rotations, reused input wires and nonlinear Boolean operations. Rotates and masks use width w. It is not SHA-256; no full SHA integration is justified once the early gate fails.

## What the attacker actually receives

`recover.py` runs as a separate process with the public JSON path and output path only. It does not import the generator. Public fields contain the modulus, input encoder columns, constant vectors, anonymous DAG edges/tensors, and output decoder rows. They contain no generator seed, width name, internal M_v, original gate operator or expected logical intermediate values. Verification-only `*.private.json` files retain those facts separately. Process separation checks the implementation's information use, not filesystem security isolation; this is not an OS-sandboxed competition.

The attacker enumerates possible vector values at each node:

1. Start with the two public columns per input and one vector per constant.
2. Process any node whose parents' supports have been discovered.
3. Evaluate its public tensor on every pair of parent support values, at most four pairs.
4. Deduplicate result vectors and assign arbitrary bit labels to them. Save the induced tiny lookup table.
5. Evaluate public output decoders on those final support values.

Each node has at most two values for this construction, even if its parents' candidate pair is unreachable due to correlations. All those pairs still correspond to ordinary Boolean gate inputs, so outputs remain encoded Boolean columns. The propagated supports may overapproximate reachable states, which is safe for the equivalence check. A generic tensor can have more values; that is detected as outside this two-state model, not called strong obfuscation.

The recovered circuit need not use original zero/one labels on internal wires. Its local tables and boundary labels are mutually consistent and compute the same public outputs. Thus restoring the exact author's variable meaning is unnecessary. At most four tensor evaluations per binary node suffice for this algorithm. The current implementation scans pending nodes repeatedly rather than using a linear-time queue, so this operation bound is not a claimed linear wall-time bound.

This is actual reconstruction from the proposed public IR, beyond knowing a private inverse. It is still **not** recovery of graph boundaries, paired vectors or dependencies from an arbitrary optimized Wasm binary. No instruction extraction, dynamic traces, hidden input sampling or source annotations are supplied. An IR that intentionally erased those boundaries would be a different, untested construction requiring a concrete transformation rule, not a license to infer security here.

## Preregistered test and results

`protocol.json` was saved before the run: three seeds (271,577,811), two widths (3,32), at most 1,000 nodes per construction, 30-second per-attacker process limit, no follow-on parameter search. No enforced memory cap; no large-memory task. The primary metric is recovery of the entire public DAG with local equivalence certificates and correct public outputs, not code-size growth or failure of an unsupported tool.

| Width | Encodings | Gates each | Cases each | Local recovery rows each | Failures |
|---|---:|---:|---:|---:|---:|
| 3 | 3 seeds | 39 | all 64 input pairs | 144 | 0 |
| 32 | 3 seeds | 416 | 64 boundary + 256 random pairs | 1,652 | 0 |

All six constructions are recovered. There are 1,152 input comparisons between the tensor program, extracted lookup circuit and direct word-arithmetic reference, with no mismatch. These are two widths of one arithmetic kernel with three matrix seeds, not six independent algorithms. Raw input/expected/tensor/recovered outputs are saved in `*.checks.json`. Random input seeds derive from the construction seed using the fixed XOR constant in the script. The construction's random matrix choices and the input draws are reproducible; they are not runtime secret randomness.

The compiler also evaluates all four logical input combinations for each generated tensor before publication: 5,460 local compiler rows across 1,365 generated gates. This checks its basis-conjugation rule independently of the word test inputs. It is not exhaustive evaluation of all 64-bit input combinations of the 32-bit kernel.

`verify_certificate.py` independently checks the recovered circuit against its public tensor program: input/constant support, unique node identities, dependency/order consistency, every local support row and all output decoder rows. There are 5,388 local rows for the six encoded constructions. An additional identity-basis positive control has 39 nodes, 144 rows and all 64 input tests. The seven certificates therefore cover 5,532 local rows. Initial support and local simulation imply public-program equivalence for every Boolean input by induction over each DAG. This is a finite certificate of the generated IR relation, not an SMT proof, arbitrary-Wasm proof or formal verification of Python itself. The source kernel's word semantics are additionally checked on the specified input sets.

Negative control: an arbitrary tensor deliberately yields four distinct vectors for its four input pairs. The attacker reports `outside-two-state-model` after four evaluations. It does not claim reconstruction or resistance. Per-encoded-run attack timings are about 0.9–1.0 ms at width 3 and 13.5–15.3 ms at width 32, excluding process startup. These single-run diagnostics are not a statistical comparison or a new-method performance result.

No Wasm binaries, SHA application, execution-performance benchmark or optimized-code resilience result was produced for this rejected candidate. Avoiding those follow-on costs follows the early-failure rule rather than narrowing the original completion goal.

## Prior-art audit

Search/read date 2026-10-12. No author implementation was executed.

- Al-Bashabsheh and Mao, [Normal Factor Graphs and Holographic Transformations](https://arxiv.org/pdf/1004.3833), arXiv:1004.3833 (2010). Read the introduction and §2.4, Theorem 1 and cancellation proof (PDF pp.9–11). Inverse transformation pairs preserve the exterior computation while changing local functions. The article explicitly relates this to gauge transformations. Its complex-valued formalism and general factor graphs are broader/different from our forward Boolean DAG over a finite ring; we use a direct ring calculation rather than importing its full results unchanged.
- Cai, Lu and Xia, [Holographic Algorithms with Matchgates Capture Precisely Tractable Planar #CSP](https://pages.cs.wisc.edu/~jyc/papers/planar.pdf). Inspected introduction and the location of §2.3 as a supporting basis-change reference; this audit does not rely on its complexity classification or claim a reproduction. Publication metadata was not independently resolved here.

These sources are sufficient to reject “put tensors on nodes and cancel neighboring inverse bases” as an independent new mathematical principle. They do not claim a Wasm obfuscator identical to our prototype or establish a universal attack. An exact application match was not proven, and search absence is not novelty evidence. The construction is rejected on the concrete reconstruction result as well as its insufficient independent-principle argument.

| Required comparison | Construction | Closest existing principle / assessment |
|---|---|---|
| Mathematical rule | Conjugate a truth tensor by input inverses/output basis | Holographic/gauge basis change; no independent principle established |
| Representation | Two-word encoded one-hot bit | Ordinary local basis representation |
| State transformation | Per-wire bijection onto two valid columns | A data representation with small finite support |
| Dependencies | Same parent graph, dense coefficients replace truth tables | Local basis change preserves topology; graph is explicit |
| Difficulty mechanism | Internal bases and Boolean labels removed from public file | Labels can be reassigned during finite-support propagation |
| Generalization | Acyclic two-input Boolean DAGs | Small-support argument generalizes within stated model; not arbitrary tensor networks or Wasm |

Queries: `program obfuscation tensor`, `obfuscation tensor network`, `white box tensor encoding`, `circuit obfuscation gauge`, `Valiant holographic algorithms basis transformation tensor boolean circuits pdf`, `holographic reduction tensor basis change inverse cancellation Holant theorem pdf`. Other search results about neural-network privacy, multilinear-map obfuscation and patents were leads only, not inspected algorithmic evidence. Earlier contextual-MBA/local-mixing records were reread for observer constraints; their results were not rerun or combined with these counts.

## Samples, provenance and reproduction

Actual Before: `*.private.json` contains ordinary Boolean operation nodes and the separately retained generation bases. Actual After: `*.public.json` contains the generated eight-coefficient tensors, without internal matrices or gate types. Recovered: `*.recovered.json` contains induced tiny truth tables and their supports. `sample.json` extracts the same node through all three forms; it is a presentation extract, not a hand-invented example. `sample.diff` shows that selected original/public/recovered representation change. Complete artifacts are referenced by their hashes in `inventory.json`.

Python 3.12.14 standard library. In a fresh copied directory without `artifacts`:

```powershell
python experiment.py
python verify_certificate.py
```

Both refuse to overwrite results. Compiler/evaluator, independent attack process, certificate verifier, protocol, raw cases, public and private artifacts and control failures are retained. All arithmetic is local; no imported services or nondeterministic runtime calls. Existing SHA baseline, CSEC sources and earlier experiments remain unchanged.

## Decision and remaining goal

Reject this specific tensor-basis-only design. The experiment improves the evidence boundary from “an inverse exists if a mapping is given” to “the published local tensor program reveals enough to reconstruct an equivalent Boolean circuit without internal mapping metadata.” It does not justify blanket rejection of all nonlinear representations, all tensor contractions or all label-discovery problems.

No new candidate survives. Goal §13 items 1–11 remain unmet in relation to an adopted new algorithm: independent principle, mathematical specification of that principle, reusable Wasm transform, SHA application, complete verification, fair proposal comparison, superiority, proposal costs/resilience, successful improvement, full reproducibility package and adopted-method examples. This directory is a rejected-candidate record only. No Complete or global Blocked status is warranted.

Next useful design constraint: merely replacing a finite-valued local object with dense numerical coefficients cannot support a protection claim when its support can be propagated from public boundaries. A different design would need a concrete update/representation rule that changes this property while preserving efficient evaluation. Enlarging a local table or concealing the graph by an unspecified future compiler is not such a rule. Any continuation should start from that rule and its nearest prior comparison, not further runs of this rejected construction.
