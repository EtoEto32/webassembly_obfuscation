# Concrete comparison with shifted p-adic straight-line programs

2026-10-12. This is a new source comparison and dependency certificate for the
existing prototype, not a new candidate or a new full-hash test. Adoption remains
unresolved. Existing WAT/Wasm and the 531-input verification files are unchanged.

## Primary source actually inspected

Romain Lebreton, *Relaxed Hensel lifting of triangular sets* (journal version 2015):
https://www.lirmm.fr/~lebreton/fichiers/LiftTriangularSet.pdf

Read sections 2.3–2.4, Definitions 11/13 and Propositions 12/15, printed pages
12–16. Definition 13 assigns zero path weight to arithmetic operations and
weight s to multiplication by p^s. Minimum path weight is the shift index.
ShiftedEvaluation constructs a digitwise evaluator with that shift.
OnlineRecursivePadic feeds already determined digits back into a shift-one
evaluator to compute its fixed point. Page 12 explicitly explains that the
zeroth digit need not be supplied separately: it is encoded in the evaluator.
The inspected algorithms therefore provide more than an abstract contraction
theorem. They do not explicitly construct our residual-feedback map from a
Boolean DAG. The remaining sections on lifting triangular representations were
not reviewed as a whole. Do not confuse triangular sets of polynomials there
with our triangular list of gate definitions.

## Our explicit mapping into that framework

Fix the external Boolean input x. Lift the integer polynomials of our update
to Z_2, and let H(v)=F(v)-2A(v-F(v)). This is possible because the evaluator
contains only addition, subtraction and multiplication on unknown coordinates.
Reduction modulo 2^32 commutes with those operations.

Represent d successive H updates as one unrolled straight-line program
Psi=H^d. Treat x as constants, and v as its internal-vector inputs. An edge from
an original gate predecessor through F has weight zero; an edge through a
doubled residual has weight at least one. A zero-weight path through d complete
updates would require a chain of d internal predecessor edges in a depth-d
source DAG. This is impossible: external-to-first-gate paths have no internal
input, and internal-to-internal chains have at most d-1 edges. Hence every path
from an initial internal coordinate to any final output has weight at least one.

Thus Psi has shift index at least one. Its fixed point includes the source
Boolean gate vector r, because F(r)=r implies H(r)=r and Psi(r)=r. Supplying
the explicit Psi SLP to ShiftedEvaluation and then OnlineRecursivePadic is a
concrete way to compute that vector using the cited existing procedure.
Repeated whole-word H updates and that digitwise procedure are different
evaluation schedules for this same recursive specification. Neither schedule
requires a previously computed T2 result. Lack of a separately supplied modular
root therefore does **not** distinguish us from this source.

This establishes an operation-level correspondence for the evaluation and
precision-propagation mechanism. It does not alone establish that the preceding
DAG-to-H transformation is published or lacks an independent contribution.
The narrow question is whether gate lifting, residual preconditioning, and this
shifted-SLP construction form only a direct composition. Calling everything a
fixed-point computation would not answer that question; the explicit steps
above are the relevant comparison. The independent reviewer inspected the same
primary passages and agreed with this direction distinction: the evaluation
mechanism is concretely accounted for, while the F-to-H construction is still
supplied before calling the known evaluator. They also reviewed the certificate
recurrence as a conservative bound, without independently rerunning it. Their
conclusion is neither adoption nor Level 3 certainty for the whole generator.

## Certificate for the actual generated circuit

`check-shift.cjs` reads and hashes the actual `circuit.json`, manifest and WAT.
It derives internal predecessor sets P_i, verifies their layer order, and applies
the following minimum-path recurrence for the current diagonal-plus-next A:

```
q_i(0) = 0
f_i(t) = min { q_j(t) : j in P_i }       [empty minimum = infinity]
r_i(t) = min(q_i(t), f_i(t))
q_i(t+1) = min(f_i(t), 1+r_i(t), 1+r_(i+1 mod N)(t))
```

Here q is a conservative dependency shift, not a gate value. Polynomial
evaluation cannot reduce an input congruence precision; addition/subtraction
use the minimum of their inputs' guarantees, while multiplication by 2 adds
one. Induction therefore proves that inputs congruent modulo 2^k yield output
coordinate i congruent modulo 2^(k+q_i(t)). Cancellation can only strengthen the
bound, so q is not claimed to be exact semantic sensitivity.

Executed result (Node 24.15.0), bound to the existing circuit/manifest:

* First t with min q_i(t)>=1: **67**.
* First t with min q_i(t)>=32: **129**.
* Every sampled generic d-step milestone satisfies min q_i(k*d)>=k.

The 129 bound follows by comparing an arbitrary initial vector to r: their
initial difference is always divisible by 2^0; after 129 steps all coordinates
agree modulo 2^32. This is a symbolic dependency certificate, not 129 runtime
samples and not a measured minimal settling time. The generic theorem's 2144
bound remains valid and is still what the Wasm executes. No performance-driven
rewrite or additional digest run was needed for this comparison.

Reproduce against an existing build directory without a previous certificate:

```powershell
& 'C:\Program Files\nodejs\node.exe' experiments/sha256-fixedpoint/check-shift.cjs experiments/sha256-fixedpoint/reproduction
```

The certificate is stored in `artifacts/shift-certificate.json`. No claim of
new shift-index mathematics or a new recursive p-adic evaluator is supportable.
The root-preserving construction, rather than its known evaluator, is the
remaining object of novelty review.
