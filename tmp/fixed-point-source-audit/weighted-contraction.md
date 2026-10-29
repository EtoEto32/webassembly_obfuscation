# Concrete contraction model for the residual evaluator

2026-10-12. This is a derivation and prior-method comparison, not an adopted
new obfuscation algorithm. It narrows the remaining novelty question.

**Later independent-review correction (same date):** the adoption gate at the
bottom was too strong as a reason to prevent a provisional full-hash experiment.
Every H admits H(v)=v-P(v) with P=v-H; a residual template and a theorem that
proves convergence do not establish prior identity of the concrete generator.
The construction steps below must be assessed together, rather than requiring
an additional invention beyond them solely because their mathematics is known.
The candidate remains unadopted, with Level 2 novelty unresolved. A complete
SHA-256 Wasm prototype is now implemented and tested in
[experiments/sha256-fixedpoint](../../experiments/sha256-fixedpoint/README.md).
The old local-only status and instruction to defer that prototype are superseded.
The mathematical proof and historical test results below remain unchanged.

The reviewer also identified a concrete structural interpretation: on complete
bit expansion, bit k of an F gate depends on at most bit k of lower-layer
predecessors, while doubled residual terms depend only on bits below k of any
coordinate. Lexicographic (bit, layer) order is a dependency DAG. Its settling
bound is another explanation of d*w, not evidence of a published identical
DAG-to-word-feedback compiler. This distinction is part of the remaining
novelty assessment, not an attack-resistance condition.

## Setting

Use the setting of convergence.md: R=Z/(2^w), fixed external inputs, a
triangular congruence-preserving gate map F, and

```
H(v) = F(v) - 2A(v-F(v)).
```

A is any fixed matrix over R. Choose gate layers l_i in {1,...,d}, such that
each internal predecessor j of gate i satisfies l_j < l_i. The bit-lift T2
circuit has d=67. Write nu(z) for the power of 2 dividing nonzero z in R,
with nu(0)=infinity. Define, for two states u,v,

```
s(u,v) = min_i [d*nu(u_i-v_i) + l_i]
D(u,v) = 2^(-s(u,v)), with 2^(-infinity)=0.
```

D is a product ultrametric: each coordinate distance is a positive multiple
of a power of the usual finite-ring 2-adic distance, and D is their maximum.
Its nonzero range is finite. In particular its balls are coordinatewise boxes.

## Pairwise contraction, without assuming either state is the root

Let s=s(u,v), e=u-v and f=F(u)-F(v). Congruence preservation gives

```
nu(f_i) >= min_(j predecessor of i) nu(e_j).
```

An input-only gate has f_i=0. For other gates, l_i-l_j>=1, so

```
d*nu(f_i)+l_i >= s+1.
```

It follows that each residual difference e_j-f_j has weighted score at least
s. Multiplying a residual by 2 and moving it from coordinate j to coordinate i
raises its score by at least

```
d+l_i-l_j >= 1.
```

Matrix coefficients cannot reduce a 2-adic valuation, nor can addition reduce
it below the minimum valuation of the terms. Both parts of
H(u)-H(v)=f-2A(e-f) therefore have score at least s+1. Hence

```
s(H(u),H(v)) >= s(u,v)+1
D(H(u),H(v)) <= D(u,v)/2.
```

This is a strict contraction of the whole finite state space, not only an
increase in precision along a previously chosen trajectory. The ordinary
topological solution r satisfies H(r)=r. Initially s(v,r)>=1 unless equal;
any nonzero difference has score at most d*w. After d*w updates no nonzero
difference is possible. This proves the earlier global bound by a second route.

The use of a weighted metric does not remove the congruence-preservation
hypothesis. Word-level right shifts still need not satisfy the gate inequality.

## Source comparison with scope limits

Brune, Knepley, Smith and Tu, *Composing Scalable Nonlinear Algebraic Solvers*,
section 4.2, Algorithms 3–4, PDF page 6:
https://arxiv.org/pdf/1607.04254

The paper gives a residual-direction update x_next=x-lambda*r(x), with line
search, and a preconditioned form. Algebraically, choosing
P(v)=(I+2A)(v-F(v)) as the residual and a fixed unit step gives exactly H.
This identifies the update template. Their real-valued line-search analysis
does not establish global finite convergence over R; the proof above supplies
that condition for this specific construction. The source is not claimed to
contain the bit-circuit generator or the d*w bound.

Gurney, *Asynchronous iterations in ultrametric spaces*, Theorem 1, Lemma 4,
and Theorem 5, PDF pages 4 and 7:
https://arxiv.org/pdf/1701.07434

The paper treats discrete iterations using nested boxes and finite-image
ultrametrics, with contraction conditions sufficient for asynchronous safety.
Our explicitly constructed product metric supplies those conditions. This
connects the convergence mechanism to existing theory; it does not establish
that the same transformation generator was previously published. No concurrent
Wasm implementation or finite bound for an arbitrary asynchronous schedule is
claimed. Fairness alone does not give a uniform number of wall-clock steps.

Both PDFs were opened successfully this turn and the cited passages inspected.
These replace the need to rely on the previously inaccessible Kelley PDF for
the residual-update comparison. No uninspected source is used as proof of an
identical algorithm.

## Finite verification

`check_weighted_contraction.py` uses F(v)=(x,v0^2+1), layers (1,2), and
A=[[1,1],[1,0]]. For w=1,2,3 it exhausts every input x and every pair of states:
32+1,024+32,768 = **33,824 pair checks**. It also checks 256 seeded pairs at w=32.
Every check satisfies the strict score increase. No root is supplied to the
checker. Script hash, counts and seed are in `weighted-contraction-results.json`.
This is a two-node Python example, not a SHA, Wasm, or SMT test. The universal
statement follows from the derivation, not this finite enumeration.

## Adoption decision

The following are now separated:

| Part | Evidence | Remaining issue |
|---|---|---|
| Residual update template | Exact substitution into a known residual iteration | Not a new template |
| Global termination | Explicit weighted strict contraction and d*w bound | Exact generator not located in prior work |
| SHA bit-lift execution | Previous 136 local T2 cases | No complete hash implementation for this candidate |
| Output dynamics | rho H = F_B rho at every step | Mixing contributes no new low-bit transition |
| Independent construction | Not established | Required before adoption |

The current bit-lift is generated by standard gate polynomials, a residual
iteration, and a factor-2 perturbation that leaves the Boolean execution
unchanged. Its correctness and termination are now explained concretely.
This gives no basis to label it Level 1. A Level 2 claim would still need an
independent construction beyond those steps; no such step has been supplied.
The candidate remains unadopted. Neither ease of inversion nor resistance is
part of this decision.

Do not perform further tests or a full-hash port solely to improve confidence
in this already-proved convergence property. Retain the evaluator as a reusable
tool, and require a new construction-level difference before extending it.
The overall research objective remains active and unmet.
