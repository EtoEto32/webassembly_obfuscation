# Fixed-point execution: source disambiguation and design review

2026-10-12. Corrected assessment: conditionally correct, independence unresolved,
not adopted. No new obfuscation algorithm is established.

Latest independent-review update, 2026-10-12: generic residual-iteration and
contraction descriptions are insufficient to establish prior identity of the
generator. A provisional complete SHA-256 Wasm implementation is now available
at [sha256-fixedpoint](../../experiments/sha256-fixedpoint/README.md): 531 inputs
per normal/transformed binary matched OpenSSL (1,062 full digest comparisons).
Its concrete construction remains a Level 2 candidate, not an adopted result.
The local-only implementation status in the older discussion below is historical.

New follow-up: [bitlift.md](bitlift.md) implements the local SHA-256 T2 expression
as a polynomial bit circuit, verifies 136 finite-ring runs, and derives/checks
its exact parity factor. It closes the rotation applicability issue for this
representation, while leaving independent novelty unestablished.

Follow-up: [conditional convergence proof](convergence.md) establishes an nw
synchronous-step bound under explicit triangularity and congruence-preservation
assumptions. The check in convergence-results.json passed 4,680 exhaustive
small-width cases and 64 32-bit cases, and confirmed an excluded right-shift
cycle with a unique root. These are evaluator checks, not execution benchmarks
or protection evidence. The former rejection based on easy removal is withdrawn.

## Specific proposed rule

For a pure arithmetic SSA DAG with n internal values, collect the defining equations as v=F(v,x), with triangular dependencies. Consider updating all values simultaneously through

    H(v,x) = v - M (v-F(v,x)),    M=I+2A, over Z/(2^w).

Dense A introduces feedback edges. The implementation would have to expand/fuse the expressions so it does not simply evaluate the entire original program before starting the loop. This is a candidate rule, not an implemented compiler. Only congruence-preserving arithmetic would fit the contemplated argument; shifts moving high bits downward, comparisons, traps, memory and source loops require separate treatment.

M has odd determinant and is invertible over this ring. Consequently H(v,x)=v iff v=F(v,x); the original triangular system has a unique root. **A unique root does not by itself prove iteration reaches it.** No unrestricted convergence or Wasm correctness claim is made here.

When M is supplied, the analyst can recover v-F(v,x) directly as M^-1(v-H(v,x)). This is an algebraic decomposition, not a reason to reject under the current goal: easy decoding and resistance are explicitly not adoption criteria. The concrete construction consists of reversible linear residual mixing and iterative evaluation. Whether its finite-convergence construction has an independent contribution requires comparison of generation rules and solver assumptions. The inverse alone does not resolve that question. Related nonlinear mixers and root lifting were investigated in implicit-equation-gate, nonbijective-residual-gate and residual-root-lifting; do not merely rename them as new candidates.

Decision: do not implement this rule as a claimed novel transformation until its independent construction is established. Additional performance or recovery measurements would not settle novelty. No conclusion about all implicit or iterative computations follows.

## Misleadingly close search hit resolved

Thomas Rinsma, **Seeing through obfuscation: interactive detection and removal of opaque predicates**, Radboud University master's thesis, 23 August 2017. Author-hosted PDF: https://rins.ma/downloads/thesis/thesis.pdf . Acquired and extracted all 63 PDF pages; **read only** title/metadata and the discussion around §2.3, PDF pages 16–17, concerning dynamic predicates and Collatz-based constructs. This is not a full-thesis review.

The located fixed-point passage describes executing protected code after a Collatz-style sequence reaches the chosen stopping value. It does not give the proposed residual solver or a proof of its convergence. The passage summarizes Wang et al.; the underlying paper was not inspected during this turn. Do not attribute that mechanism to Rinsma as its originator, use the search crawl date as the publication year, or treat a search phrase match as proof of identical prior art. No Collatz-based transformation is proposed or implemented here.

PDF and extraction are retained for traceability. Existing records for settling-carry already distinguish repeated circuit evaluation from hiding its dependency graph. That distinction also applies here.

## Search record

- code obfuscation iterative equation solving fixed point polynomial systems
- obfuscation computation iterative convergence fixed point transformation
- program obfuscation residual equations nonlinear systems iteration
- obfuscation "polynomial" "fixed point"
- obfuscation "2-adic"
- obfuscation "system of equations" "iteration"

General numerical-analysis, patent and hardware search hits were not inspected in full and are not evidence of exact overlap. The lack of a direct search match establishes no novelty.

## Consequence for continued development

A successor needs a concrete generation rule, a valid termination argument and an operation-level comparison with the closest constructions. It does not need to defeat a public inverse or tracing. An evaluator's correctness and an algorithm's novelty are separate claims. The authorized independent reviewer confirmed this correction; the prior source review here did not establish an identical finite-convergence construction.

No CSEC source, mining process or protection setting changed. No new correctness/resistance sample count is reported. Overall goal is active and unmet.
