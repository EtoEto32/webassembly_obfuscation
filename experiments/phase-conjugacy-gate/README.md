# Phase-specific encodings: a reduced-model conjugacy obstruction

2026-10-12, Asia/Tokyo.

## 1. State

**Inconclusive; invention goal active and unmet.** This is a mathematical gate on a contemplated representation, not a new obfuscation algorithm. The preceding goal turn added a specific prior-art constraint and counts as progress, but did not supply an implementable novel rule.

## 2. Established result

In an explicitly defined 2-bit-word SHA-shaped state machine, arbitrary phase-specific bijections cannot produce one phase-independent update for every input word across boundaries 8 through 16. This result removes the *common decoder* restriction from the earlier capacity gate **only for this reduced model**. It does not settle standard SHA-256.

## 3. Unmet requirements

No new reusable Wasm transformer, new full SHA application, fair resistance comparison, performance/size/optimizer evaluation, or successful new-method improvement cycle exists here. A negative mathematical gate is not the goal's deliverable.

## 4. Rule, assumptions and necessary invariant

For width w, let S={0,...,2^w-1}^8. T_(i,u) uses the ordinary eight-word SHA round expression, with each addition reduced modulo 2^w, K_i reduced modulo 2^w, and every big-sigma rotation reduced modulo w. This is a separately defined toy machine. There is no message schedule, padding, memory or trap behavior. All states and all word inputs are permitted.

The contemplated transformation would have bijections E_i:S→Z onto the **same** set Z of size |S| and one update U_u:Z→Z, with

```text
Before: s' = T_(i,u)(s)
Intended After: z = E_i(s); z' = U_u(z) = E_(i+1)(s')
Required: E_(i+1) T_(i,u) E_i^-1 = U_u, for all s,i,u.
```

E_i is otherwise unrestricted. No common decoder, polynomial degree bound or fixed zero-input normalization is assumed. External phase, a larger carrier, phase-dependent input recoding and multiple microsteps are excluded from this particular hypothesis. No E_i or U_u was synthesized.

Composition applies the rightmost map first. For input vector v of length L, define P_(i,v)=T_(i+L-1,v[L-1]) ... T_(i,v[0]). If the hypothesis holds, E_(i+L) P_(i,v) E_i^-1=Q_v, where Q_v=U_v[L-1] ... U_v[0] is independent of i. Hence

```text
R_(i,v) = P_(i,0)^-1 P_(i,v)
E_i R_(i,v) E_i^-1 = Q_0^-1 Q_v.
```

Choose v=(1,0,...,0) and t=(0,...,0,1), and write A_i=R_(i,v), B_i=R_(i,t). Every word in A_i,B_i and their inverses must have the same cycle histogram at each phase, because its conjugate is independent of phase. In particular this holds for A_i B_i and C_i=A_i B_i A_i^-1 B_i^-1. Bijections relabel each cycle, preserving its length and fixed-point count. This is a necessary condition, not a sufficiency test.

## 5. Prior art and novelty

The invariant is standard permutation conjugacy, not an invented mathematical principle. [MIT Algebra I, Lecture 21](https://ocw.mit.edu/courses/res-18-011-algebra-i-student-notes-fall-2021/mit18_701f21_lect21.pdf), §21.2, PDF pp.1–2, Definition 21.4 and Proposition 21.6, was read as primary text on 2026-10-12. It states that conjugation preserves cycle type. The application to relative input-prefix maps above is our direct derivation, not a theorem attributed to that lecture.

Searches: `simultaneous conjugacy permutations cycle structure commutator invariant`; `nonautonomous control system state transformation time invariant conjugacy input`. Other search results were leads only, not evidence of novelty or general impossibility.

| Comparison | Assessment |
|---|---|
| Mathematical rule | Boundary bijections and cancellation; familiar representation changes |
| Representation | Arbitrary phase-specific permutations, no explicit new efficient representation |
| State transformation | Exact conjugacy condition for relative input effects |
| Dependencies | Input word is unchanged; phase may only be reflected by E_i |
| Difficulty | No attack-resistance claim; a correctness/existence obstruction |
| Generalization | Invariant applies to finite bijective input systems; numerical obstruction only to the specified toy |

## 6. Reused work

Inspected `sha-zero-phase-gate/README.md` and `sha-phase-capacity/README.md` (category C: narrower prior obstructions). Read `sha-history-gate/check.py` and `sha-joint-history-gate/check.py` for round conventions. Reused the existing `sha256-research-baseline/vendor/sha256.js` K table with its hash recorded. Used Python 3.12.14 and NumPy 2.5.3 already installed; no dependencies installed. Existing SHA results were not counted as new tests.

## 7. Implementation and results

`protocol.json` was saved before execution: widths 1 and 2, phases 8 and 9, L=2..7, two fixed impulses, two fixed permutation words, one exhaustive run and a 120-second budget. No result-driven extension of widths, inputs or words occurred.

`check.py` enumerated every state and constructed complete prefix/relative permutations. It checked round inversion using a separately expressed inverse formula for **262,656** state/input pairs. All tested maps were checked to be bijections. It saved all four word permutations for each of the 12 width/window cases.

Exactly one case distinguished phases: w=2,L=7, the commutator C.

| Case | States | Fixed points at i=8 | Fixed points at i=9 | Result |
|---|---:|---:|---:|---|
| w=2,L=7,C | 65,536 | 80 | 48 | Cycle types differ; required E_i/U_u cannot exist |

Full cycle histograms are in `artifacts/results.json`. All other tested histograms matched; that does **not** prove simultaneous conjugacy or the existence of a common update. The product histogram also matched in the distinguishing case.

An independently written scalar forward evaluator, `verify_scalar.py`, used bit-string rotations and alternative Ch/Maj expressions. It performed **2,752,512** scalar rounds, matched all **262,144** saved entries of the four distinguishing-case permutations, and independently counted fixed points **80 and 48**. This verification was added after discovery and is a confirmation, not an additional preregistered discovery trial.

Controls: 24 deterministic bijective relabelings preserved histograms. A four-state pair example had matching individual cycle types but different product cycle types, verifying why checking generators separately is insufficient. Counts are exhaustive identities in the toy domains, not statistical security trials. No SMT or proof assistant was run.

## 8. Attack comparison

None. This is an existence obstruction for a desired transformed update, not a recovery attack on an unknown Wasm binary. There are no timeout-as-security or unsupported-tool claims.

## 9. Performance, size and optimization

Not evaluated. The short verification runtime is not a program overhead measurement. The `.npz` files are mathematical permutation tables, not executable transformed Wasm.

## 10. Design implication

Earlier evidence excluded a shared decoder or one chosen normalization. This gate excludes **every** same-size bijective boundary representation for the specified 2-bit machine and input interface. Therefore a proposed width-generic common-update formula covering this toy cannot be repaired merely by searching for another E_i. It would need different assumptions or an explanation of why it applies only to other widths. This is not the required successful obfuscation improvement cycle.

Do not increase toy widths just to accumulate negative counts. A next substantive step on this line would need an analytical connection to real 32-bit rotations, or an explicit independent rule avoiding the failed premise. No such connection or rule is claimed here.

## 11. Before/After evidence

Section 4 gives the original round and the unimplemented intended replacement. `round_maps` implements the reduced Before family. Saved prefix-derived permutations are actual computed obstruction witnesses; they are **not** fabricated After programs. There is no completed transformed example or optimizer diff.

## 12. Reproduction

From repository root:

```powershell
& .\.tools\runtime-analysis-py312\Scripts\python.exe experiments/phase-conjugacy-gate/check.py --out experiments/phase-conjugacy-gate/reproduction
```

The output directory must not exist. Numerical rows, round checks and tables should match the original; this fresh-directory rerun has not been performed. Python/NumPy versions and hashes of generator, protocol and K source are recorded in results. Original run command omitted `--out` and wrote `artifacts`. `verify_scalar.py` was actually run against those artifacts; it refuses to overwrite its verification JSON. To repeat it, copy this experiment's sources and generated artifacts to a fresh sibling location with the same vendor relative path, excluding the old scalar verification JSON. No existing result needs deletion.

`manifest.json` at this directory's root covers the final sources, report and generated data. The generator's own `artifacts/manifest.json` covers its initial outputs; the later scalar verification is covered by the root manifest.

## 13. Limits

Standard SHA-256 does not reduce to this 2-bit machine by taking low bits: rotations move higher bits into lower positions. Thus the numerical obstruction must **not** be lifted to 32 bits or to real SHA messages. It also does not cover larger/redundant encodings, input feedback, external phase state, or non-bijective representations. There is no global blocker and no completion claim. The central unmet task remains inventing and evaluating an independent effective obfuscation rule.
