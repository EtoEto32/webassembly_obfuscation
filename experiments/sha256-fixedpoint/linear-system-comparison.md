# Linear finite-ring systems: exact overlap and limit

2026-10-12. Source comparison only; no new hash run or new candidate.

## Primary passages inspected

* Yannic Rohde and Eva Zerz, *Linear Dynamical Systems over Finite Rings*,
  IFAC PapersOnLine 58-17 (2024), 374–379,
  https://publications.rwth-aachen.de/record/997085/files/997085.pdf .
  Sections 3–4, especially Theorems 11–12 on printed page 378: a nilpotent
  linear system over Z/(p^w) has height at most n*w; the reduced system's
  height can give a tighter bound w*h1. The underlying objects are module
  endomorphisms. These statements concern a given linear system, not a
  compiler from nonlinear gate definitions.
* Guangwu Xu and Yi Ming Zou, *Linear Dynamical Systems over Finite Rings*,
  arXiv:0810.3164 (2008), https://arxiv.org/pdf/0810.3164 .
  Introduction and opening of section 2 inspected. The paper develops
  matrix-power tests for finite linear dynamics. Its example 1.1 already
  exhibits a matrix over Z/8 whose sixth power is zero. A fixed-point
  system need not have a unique fixed point; do not equate that term alone
  with the candidate's all-states-to-one-root property.

## Direct specialization, derived here

Take the affine source subclass F(v)=L*v+b, with L strictly lower triangular
over R=Z/(2^w). Its root r exists uniquely. For any constant mixer M,

```
H(v) = v - M*(v-F(v))
H(v)-r = N*(v-r),       N = I - M*(I-L).
```

Thus the affine subclass is exactly a linear error system; this is more
specific than observing a general resemblance to fixed-point methods.
When M modulo 2 is lower unitriangular, N modulo 2 is strictly lower
triangular, so N^n=2B for a matrix B over R. Consequently

```
N^(n*w) = (2B)^w = 0.
```

For the original M=I+2A, N modulo 2 equals L modulo 2. If L^d=0 modulo 2,
the same calculation gives N^(d*w)=0. These are linear instances of the
published nilpotence-height mechanism. We therefore cannot present the
affine special case's exact finite convergence or n*w bound as a new principle.

## What this does not establish

The actual 381-coordinate SHA construction includes products of unknown
coordinates. Its differences do not evolve by one constant N. Applying a
linear-system theorem directly to that nonlinear recurrence would be invalid.
The existing weighted dependency proof covers it instead.

Nor do the inspected passages classify M uniformly over all strictly
triangular nonlinear congruence-preserving F. Our classification uses linear
examples for necessity and a separate nonlinear proof for sufficiency.
This comparison therefore closes a possible novelty claim for the affine
subclass, but neither establishes nor refutes independent Level 2 novelty
of the whole DAG-to-residual-feedback generator.

Further generic searches for linear stabilization are unlikely to resolve
that remaining question. The next decision should compare construction
steps, or examine a different transformation principle. Existing full-hash
verification remains unchanged and should not be rerun merely for activity.
