# Which constant residual mixers preserve every triangular circuit?

2026-10-12. A derivation to isolate the candidate's construction-level content.
This is not a newly adopted obfuscator, a claimed first publication, or a change
to the tested SHA-256 binary. The independent reviewer checked the argument and
enumeration code without finding a gap; they did not rerun the enumeration.

## Exact quantifiers

Fix n>=1, w>=1, R=Z/(2^w), a coordinate order 1..n, and a constant matrix
M in R^(n*n). External inputs are held fixed during evaluation. Let F range over
**all** strictly triangular, congruence-preserving maps in that order: F_i depends
only on coordinates j<i and fixed external inputs. Every such F has a unique
root r=F(r), obtained recursively. Define

```
H_M(v) = v - M*(v-F(v)).
```

Then the following are equivalent:

1. For every such F and every initial v, iterating H_M eventually reaches r.
2. M modulo 2 is lower triangular with all diagonal entries equal to 1.

Condition 2 gives the uniform sufficient bound n*w. This concerns fixed-order,
constant mixers and the entire source-map class. It does not characterize every
convergent mixer for the particular SHA circuit, input-dependent matrices, or
other coordinate orders.

## Sufficiency

Choose a lower unitriangular lift U of M modulo 2 and write M=U+2A in R.
Set G(v)=(I-U)v+U F(v). Because U is lower triangular with diagonal 1, G_i
depends only on coordinates j<i. It is congruence-preserving, and G(r)=r.
Our update can be written

```
H_M(v) = G(v) - 2A*(v-F(v)).
```

For differences e=u-v use s=min_i[n*nu2(e_i)+i], with nu2(0)=infinity.
Strict triangularity implies that the weighted score of every coordinate of
G(u)-G(v) and F(u)-F(v) is at least s+1. Consequently each coordinate of
e-(F(u)-F(v)) has score at least s. A term transferred by 2A from j to i
adds at least n+i-j>=1 to its score. Addition cannot lower the minimum score.
Thus H_M increases s by at least one. Comparing with the fixed point r gives
equality after n*w steps, since a nonzero difference has score at most n*w.

This proof uses coordinate index as layer. It does not claim that an arbitrary
lower-unitriangular U preserves the smaller original gate-depth bound d*w.
The original M=I+2A does preserve that depth bound by the earlier proof.

Also, M has odd determinant and is invertible in R. Hence no additional fixed
points are introduced. Invertibility by itself is not sufficient for convergence.

## Necessity

Restrict F to F(v)=Lv, where L ranges over all strictly lower triangular
matrices with entries 0 or 1. Its unique root is zero. Reduction modulo 2 of
the update is the linear map with matrix

```
N_L = I - Mbar + Mbar*L  over GF(2).
```

If every initial vector converges to zero, N_L is nilpotent: each basis vector
is eventually annihilated, so a common power annihilates all of them. In
dimension n this is equivalent to N_L^n=0. In particular trace(N_L)=0.

For any i<j, compare L=0 and L=E_ji. Both are permitted source maps, and

```
0 = trace(N_(E_ji)) - trace(N_0) = trace(Mbar*E_ji) = Mbar_ij.
```

Thus all upper-triangular entries of Mbar are zero. N_0 is now lower triangular;
its nilpotence forces each diagonal entry 1-Mbar_ii to vanish. This proves
condition 2. The argument applies for any w: convergence in R implies convergence
of its mod-2 projection from every projected initial vector.

For example, the invertible matrix M=[[1,1],[0,1]] fails with F(v)=(0,v0).
The update is H(v)=(v0-v1,v0). From (1,0) it has a 3-cycle modulo 2, and a
6-cycle modulo 2^w when w>1. The unique root remains (0,0). This excludes a
specific universal-preconditioner claim, not the use of that matrix with every
possible individual source circuit.

## Executed exhaustive audit

`check-mixer-class.py` enumerates all binary matrices M and all strictly lower
binary matrices L, and tests nilpotence directly by matrix powers. It compares
that result with the proposed triangular/diagonal criterion. No early exit
skips source/mixer pairs.

| n | All M | All L | Pairs checked | Accepted M |
|---|---:|---:|---:|---:|
| 1 | 2 | 1 | 2 | 1 |
| 2 | 16 | 2 | 32 | 2 |
| 3 | 512 | 8 | 4096 | 8 |

All **4130** classifications agree. For each rejected M, the JSON stores a
source L, N_L and a basis index j with N_L^n e_j nonzero. In dimension n the
kernel chain has stabilized by n, so this basis vector is not eventually
annihilated. These finite checks audit the linear necessity cases only; the
proof above establishes the arbitrary-n, nonlinear, word-width statement.

Results: `artifacts/mixer-class.json`; script refuses to overwrite it.

## Consequence for novelty assessment

The particular choice M=I+2A is a subfamily of the full order-compatible
preconditioner class. The essential mechanism is that same-bit dependencies
retain a strict order, while terms that can point backward lose at least one
bit of precision. Arbitrary matrix coefficients above that precision barrier
are not, by themselves, an independent new transformation principle.

This is more precise than assigning a generic residual template after choosing
H: it derives exactly which constant preconditioners work uniformly for the
source class, directly from the source order. It also explains why simply
varying A or adding lower-triangular entries should not be advertised as a new
candidate. The mathematical classification has not been established as new or
located as an identical published result. Its elementary proof is not evidence
of either priority or lack of priority.

Earlier inspected sources identify residual preconditioning and shifted p-adic
evaluation as existing tools; see `README.md` and `shifted-slp-comparison.md`.
This turn's focused searches for p-adic preconditioning, nilpotent Jacobian
iteration and triangular residual iteration did not locate an inspected source
with this exact source-to-mixer classification. That absence is not a novelty
proof. No new source-body claim is made from the unrelated search results.

The unresolved adoption question is now specifically whether **constructing
order-compatible residual mixers from the source DAG** provides an independent
program transformation, or is a direct composition of established preconditioning
and precision-ordered evaluation. No additional hash tests, benchmarks or
coefficient variants will answer that question. The full-hash implementation
and its existing 531-input results remain useful concrete evidence of correctness.
