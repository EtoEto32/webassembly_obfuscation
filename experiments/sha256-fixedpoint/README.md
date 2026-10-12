# Finite-ring residual evaluation in complete SHA-256

2026-10-12. **Adopted as a scoped Level 2 research proposal after independent
review.** The contribution is the source-DAG-to-residual-mixer construction with
its global finite-ring termination guarantee. This is not a claim of a new
residual iteration or established worldwide priority. See the final Japanese
[report](research-checkpoint-ja.md) and the latest decision below.

Latest [independent review decision](independent-decision.md): adopt the limited
construction as a Level 2 proposal. Earlier holds below are retained as the
history of the investigation and are superseded by that scoped assessment.
Generated artifacts retain their original provisional status strings because
their hashes bind the historical execution records.

The final evidence audit, `audit-final.cjs`, checked 13 pinned files, all 531
saved full-digest rows against their corpus bytes, gate order/depth and scratch
layout. `artifacts/final-evidence-audit.json` records the result. It is an
integrity/coverage audit, not another Wasm test run or a novelty proof.

New source comparison: [shifted-slp-comparison.md](shifted-slp-comparison.md)
maps H^67 concretely into a published shifted p-adic evaluation procedure.
A symbolic dependency certificate for this circuit gives 129 as a sufficient
settling bound; the tested Wasm still uses 2144. This narrows the possible
novel contribution to the DAG-to-residual-feedback generator. It supplies no
basis for claiming a new digitwise fixed-point evaluator.

Further construction audit: [mixer-classification.md](mixer-classification.md)
characterizes the constant mixers that work for every strictly triangular
source map in a fixed order: modulo 2 they must be lower triangular with unit
diagonal. A proof and 4,130 exhaustive small-matrix checks support that statement.
This isolates the source-order condition behind I+2A; it does not establish
novelty of that condition or introduce a new algorithm by changing coefficients.

## Algorithm and actual scope

The [linear-system comparison](linear-system-comparison.md) identifies a direct
published overlap for affine source circuits: the transformed error follows
a nilpotent matrix over the finite ring. This rules out claiming the affine
settling bound as a new principle, while leaving the nonlinear generator's
construction-level assessment open.

Replace T2 = Sigma0(a) + Maj(a,b,c) modulo 2^32 in round 63 of the **final
padded block only**. Other rounds, SHA-256 IV, message schedule, padding,
feed-forward and all eight output words remain those of the pinned baseline.
This is a complete input-to-digest SHA-256 program with one transformed internal
operation, not a hash of a precomputed digest or a local-only benchmark.

Construct a Boolean DAG for T2: rotations are wire references, majority is the
XOR of three pairwise ANDs, and addition uses a ripple carry. Lift the gates to
R = Z/(2^32) using AND(x,y)=xy, XOR(x,y)=x+y-2xy and OR(x,y)=x+y-xy.
There are 381 internal coordinates, depth d=67. Inputs are the 96 bits of a,b,c
and constants 0,1. Let F(v) be all gate right-hand sides evaluated from the same
old vector. Let A have a diagonal and a cyclic forward edge:

```
r_i = v_i - F_i(v)
v'_i = F_i(v) - 2*(r_i + r_((i+1) mod 381))  mod 2^32
```

Initialize every coordinate to 0xffffffff. Perform exactly 67*32=2144
synchronous updates using separate old, F, and new buffers. Pack the 32 output
coordinates by shifted addition, **without masking their low bits**. The
settled coordinates are actual 0 or 1 words. No ordinary T2 result or root is
passed to this evaluator. The ordinary expression remains in the other-round
branch, which is not executed for the selected round.

Before: one word expression using rotates, Boolean operations and addition.
After: a 381-word simultaneous polynomial recurrence with backward and cyclic
word dependencies, followed by output packing. The generated WAT contains both
forms and the final-block/round selector. Its expanded bit dependencies are
discussed below; a word-level cycle is not a claim of an irreducible bit cycle.

## Mathematical correctness

The ordinary topological Boolean gate values form r with F(r)=r. They are
0/1 and hence fixed by the transformed update. Every lifted gate is an integer
polynomial, so congruence modulo 2^k of its arguments implies congruence of its
output. Bit extraction applies only to fixed external inputs, not unknown
coordinates; no right shift of an unknown ring coordinate breaks this condition.

For gate layers l_i in 1..d and nu the 2-adic valuation modulo 2^32 (nu(0)=infinity),
define s(u,v)=min_i[d*nu(u_i-v_i)+l_i]. Each F dependency advances at least one
layer at unchanged precision. Each factor-2 residual edge gains a precision bit
and may lose at most d-1 layers. Therefore every update increases s by at least
one. A nonzero difference has score at most 32d; every initial difference has
score at least one. After 32d steps the vector equals r. This is a universal
algebraic argument, not an inference from the finite tests. See
[the detailed proof](../../tmp/fixed-point-source-audit/weighted-contraction.md).

The local result equals ordinary T2 for every triple of i32 words. Substitution
at the selected round therefore preserves the full working state at the next
round boundary. Padding chooses exactly one final block; induction over the
unchanged preceding rounds and blocks, followed by identical feed-forward and
serialization, gives H'(m)=H(m) throughout the supported domain. The finite
OpenSSL comparisons separately validate that both implemented programs compute
the expected SHA-256 digests on the corpus.

## Novelty status and corrected review gate

This is a candidate for Level 2 evaluation, **not an adopted Level 2 result**.
The independent reviewer identified two overly broad exclusion arguments:

* Writing H(v)=v-P(v) cannot establish prior identity: every H has P=v-H.
  The specific residual P=(I+2A)(v-F(v)) needs comparison as a generator.
* The quotient rho(v)=v mod 2 gives rho H=F_B rho. It permits a different
  evaluator that stops after d rounds and masks low bits. Our actual reader
  uses whole coordinates after 32d rounds. Existence of a simpler evaluator is
  not, by itself, evidence that this generator was previously published.

Known mathematics still explains the construction, and independent novelty
remains a real requirement. The concrete comparison unit is **DAG polynomial
lifting + cross-residual feedback + a compile-time finite settling bound**.
Merely labeling it a contraction, an implicit encoding or a cyclic circuit is
too broad to prove either equivalence or novelty.

Closest inspected sources and limits:

| Source | Actual overlap | Unresolved distinction |
|---|---|---|
| [Ranea et al., CRYPTO 2022](https://crypto.iacr.org/2022/papers/530630_1_En_2_Chapter_OnlinePDF.pdf), sections 2–3 | Implicit polynomial representations and zero-fixed permutations | Their evaluated equations are affine in output unknowns; these internal gate unknowns are nonlinear and evaluated by bounded recurrence. This difference alone is not sufficient for adoption. |
| [Brune et al.](https://arxiv.org/pdf/1607.04254), section 4.2 | Residual/preconditioned update template | Substitution does not supply the DAG-to-ring generator or its global exact 32d guarantee. |
| [Gurney](https://arxiv.org/pdf/1701.07434), Lemma 4/Theorem 5 | Finite-image ultrametric contraction theory | Explains convergence once the metric is constructed; does not establish prior identity of the compiler. |
| [Roshanisefat et al.](https://arxiv.org/pdf/2001.08999), section IV-B | Hardware cyclification by templates, correlated-input restrictions, or node merging | Inspected section constructs Boolean feedback using template matching, non-occurring inputs and SAT validation. It does not describe this finite-ring residual rule. No claim about all cyclic-circuit literature follows. |

The first three comparisons reuse earlier inspected primary sources. Section
IV-B of the fourth source was read in this turn. Searches were limited to the
candidate's fixed-point, cyclic-circuit and 2-adic evaluation mechanisms.
Failure to find an identical generator is not proof of novelty.

An additional structural observation from review is significant: bit k of F_i
depends on at most bit k of lower-layer predecessors, while the doubled
residual depends only on bits below k. In lexicographic (bit index, gate layer)
order the expanded update has a DAG of dependencies. The 32d bound can also be
understood as synchronous settling of this DAG. Any future novelty argument
must account for this concrete reduction, without equating analyzability with
failure. The remaining question is whether constructing this dependency order
by residual feedback is an independent transformation or a direct instance of
known bit-level circuit regrouping. Do not claim an intrinsically cyclic bit
computation, improved attack resistance, or a new fixed-point theorem.

## Implementation and reproduction

`build.cjs` pins and derives the existing baseline WAT. It constructs the DAG,
emits the simultaneous i32 evaluator, changes the compress ABI to carry a last
block flag, and builds/validates three binaries with WABT 1.0.42. The baseline
file is never modified. Its sha.js 2.4.11 provenance/license is retained in
`../sha256-research-baseline/vendor/LICENSE`.

Domain D: all byte strings of length 0..1,048,576, loaded at memory offset 1024.
Call `hash(length)`; return value is 512 and the 32-byte digest is at 512..543.
The fixed 17-page non-shared memory contains constants at 768..1023, which callers
must preserve. Calls are sequential and non-reentrant. Internal buffers are
1,060,000..1,064,571, beyond the maximum input end 1,049,600 and within memory.
Every call initializes its evaluator state. Invalid unsigned lengths trap before
writes. Extra exports `t2` and `evaluations` are test instrumentation; normal hash
execution requires no host callbacks. `evaluations` counts helper calls and wraps
as i32; its value never affects a digest.

From the repository root (output directory must not already exist):

```powershell
& 'C:\Program Files\nodejs\node.exe' experiments/sha256-fixedpoint/build.cjs experiments/sha256-fixedpoint/reproduction
& 'C:\Program Files\nodejs\node.exe' experiments/sha256-fixedpoint/verify.cjs experiments/sha256-fixedpoint/reproduction
```

## Executed verification and limits

Node 24.15.0, OpenSSL 3.5.5, WABT 1.0.42. `artifacts/manifest.json` binds the
generator and generated files; `artifacts/verification.json` saves all digests,
local inputs, negative-control outputs and script/manifest/corpus hashes.

* Normal and transformed Wasm: **531 inputs each, 1,062 complete digest
  comparisons, zero mismatches** against freshly computed OpenSSL SHA-256.
* Reused corpus includes empty, abc, published long vector, million-a, every
  length 0..256, larger boundaries through 1 MiB, and 256 seeded random messages.
  Exact corpus bytes are pinned; old success counts were not reused as new tests.
* 36 T2 triples: independent word expression agrees, and all 381 final words
  equal an independent Boolean-gate evaluation, not only their low bits.
* Every transformed hash executes the new helper exactly once. All its final
  coordinates are 0/1. Input and post-input canary remain intact.
* Four invalid lengths per main binary trap without changing memory or helper
  count; a subsequent abc call succeeds.
* A negative-control binary changes mixing coefficient 2 to 1. Both empty and
  abc produce a wrong digest, confirming the harness detects that defect.

The first verifier invocation stopped before executing Wasm because the corpus
bundle hash was mistakenly pinned as the JSON index hash. The index and bundle
were inspected separately, the pin was corrected, and the full run above passed.
No semantic failure was hidden or converted into a passing vector.

New binary sizes: plain 3,128 bytes; transformed 35,930 bytes. Size is a structural
observation, not a novelty metric. No new SMT run, performance benchmark,
optimizer-survival test or attack evaluation was performed. Earlier Python
contraction checks are separate historical evidence. Novelty remains unresolved;
this full-hash prototype is now available for a concrete construction comparison.
