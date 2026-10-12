# Residual coordinates: what a conjugacy does and does not establish

Later same-day decision: the scoped Level 2 proposal was adopted following the
criterion audit in independent-decision.md. The hold recorded at the end of
this comparison is historical. This comparison alone did not establish novelty.
The reviewer subsequently confirmed the image-cardinality argument as well.

2026-10-12. New algebraic comparison, independently reviewed by the previously
authorized reviewer. No new hash execution, source-publication claim, or adoption.

## Explicit change of coordinates

Fix external input x and a strictly triangular polynomial gate map F over
R=Z/(2^w). Define E(v)=v-F(v). This is a triangular polynomial automorphism,
even though F itself generally is not invertible. Its inverse V is obtained by

    V_i(e) = e_i + F_i(V_1(e), ..., V_(i-1)(e)).

This is a finite recursive polynomial construction. It sends the original root
r to zero, E(r)=0. An expanded inverse need not be an efficient encoding of a
large circuit; no size bound or runtime implementation is claimed here.

For H(v)=v-M E(v), M=I+2A, the exact conjugated transition is

    K(e) = E(H(V(e)))
         = (I-M)e + F(V(e)) - F(V(e)-Me).

The final difference term cannot generally be discarded. For example, take
F(v1,v2)=(x,v1^2) and M=I. Then

    V(e) = (x+e1, e2+(x+e1)^2)
    K(e) = (0, 2*x*e1+e1^2).

The difference from zero is already visible at x=0,e1=1 for any w>=1. This
example belongs to the triangular polynomial source class used in the theorem;
it is not described as a changed SHA gate or a new full-hash experiment.

## State-dependent matrix form

For polynomials, telescoping the substitutions of their individual arguments
gives F(a)-F(b)=L(a,b)(a-b), with L strictly lower triangular because F is
strictly triangular. This uses a polynomial factorization of differences, not
division by coordinate differences or an assumption that R is a field.
Consequently, with a=V(e), b=V(e)-Me,

    K(e) = [I-M+L(e)M] e.

For affine F(v)=Bv+c, L=B is constant, yielding the usual linear residual
iteration. For nonlinear F, L depends on the source, inverse coordinate map,
and current residual. Calling this a matrix expression does not make its
coefficients constant or establish equivalence to the previously inspected
finite-ring linear-system theorems.

## An even narrower exclusion can be disproved outright

H is not in general merely a bijective encoding of the original simultaneous
transition F. Conjugation by a bijection preserves image cardinality. In the
one-coordinate example F(v)=x, A=1, w>=2,

    H(v)=3*x-2*v.

F has image size 1, whereas H has image size 2^(w-1). Hence there is no
bijection B of the same state space with H=B^-1 F B in this example.
This only disproves that exact same-state-space, one-step-conjugacy claim.
It does not exclude encodings of another transition, added state, time changes,
or a composition of existing constructions. It is not evidence of priority.

## Consequence for the review decision

The E-conjugacy gives a correct source-dependent zero-attractor representation.
It does not independently select a previously known zero-attractor and derive
the candidate using that representation: the formula above was computed from
the already chosen H and still contains the source-dependent difference term.
To make the stronger reduction, one must identify a prior generator that
constructs this K (or another concretely equivalent procedure) from the source.

Furthermore, a map taking every state of a nontrivial finite state space to
one fixed point after sufficiently many iterations cannot be a permutation.
Thus K itself is not a zero-fixed permutation. This does not rule out use of
permutations as components of a larger prior construction.

The independent reviewer derived the E/V/K expressions, the state-dependent
matrix factorization and this distinction without editing files or rerunning
tests. The image-cardinality example was subsequently added by the main agent
as a direct elementary argument; it has not received that independent review.

Decision remains **hold, not adopted**. This closes two overly broad rejection
arguments (dropping the difference term, or claiming conjugacy to F itself),
but supplies no new Level 2 acceptance evidence. Do not start coefficient
variants or repeat the 531-input corpus in response to this comparison.
