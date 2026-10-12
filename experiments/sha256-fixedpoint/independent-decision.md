# Independent review decision

## Latest decision: adopt a scoped Level 2 research proposal

2026-10-12, subsequent review after resumption under the user's explicit weekly
usage-limit rule. This supersedes the hold decision below; the historical
correctness artifacts and their original status strings remain unchanged.

The reviewer audited whether the earlier decision was demanding proof that no
unknown publication exists. They concluded that the objective permits a Level 2
construction supported by concrete differences and does not require that
impossible form of literature exhaustiveness. The main agent accepts the revised
decision for the following limited contribution:

**Compile a triangular program DAG into nonlinear internal-state equations,
construct residual mixers from its source order, and generate an evaluator
guaranteed to preserve the root and terminate exactly from every initial state
over a finite word ring.**

The distinguishing design condition is not arbitrary invertibility: uniformly
over all strictly triangular congruence-preserving source maps, constant M must
be lower unitriangular modulo 2. The I+2A construction also preserves the
original depth-based d*w bound. Proof and a counterexample to the weaker
invertibility condition are in mixer-classification.md.

This adopts the joint program transformation as a Level 2 proposal, not a new
fixed-point theorem, a new residual update, a new digit evaluator, a world-first
claim, or a priority/legal opinion. Future evidence of the same construction
requires updating the assessment. Its basis is the positive source-to-mixer
condition and the specific comparisons, not a search returning no matching name.

The reviewer also considered the stronger direct substitution into Firedrake's
documented nonlinear Richardson update G(v')=G(v)-R(v): set R(v)=v-F(v) and
G(v)=M^-1 v to obtain exactly our update. This confirms that the update itself
is known. The inspected section does not construct M from a source DAG or give
the finite-ring all-initial-state bound. The reviewer maintained the scoped
adoption after inspecting that additional correspondence. Source:
https://www.firedrakeproject.org/preconditioning.html#nonlinear-preconditioning

Ranea's inspected construction evaluates equations affine in output unknowns;
the proposal evaluates nonlinear internal gate unknowns. Brune supplies the
residual iteration, but not this source-order constructor and finite-ring
guarantee. Lebreton evaluates a supplied shifted SLP; our construction generates
one with a guaranteed shift from the original DAG. The remaining sections and
all possible related publications are not asserted exhaustively excluded.

No new correctness test was requested to establish novelty. The reviewer also
confirmed the image-cardinality example in residual-coordinate-comparison.md.
This decision is an assessment of the existing construction against the stated
Level 2 criterion; no new mathematics was invented by changing its status.

## Earlier decision, retained for provenance

2026-10-12. The user explicitly authorized one independent reviewer. The same
reviewer inspected README.md, shifted-slp-comparison.md and
mixer-classification.md; they did not edit files or rerun tests.

Decision: **hold, not adopted; stop peripheral searches and repeated tests of
this candidate unless new construction-level evidence becomes available.**

The unresolved operation is generation, from F's source order, of a mixer and
evaluation rule guaranteeing both the original root and convergence from all
initial states. Supplying a previously generated H to a known evaluator is not
proof that this generation step is already published. Conversely, failure to
find that exact step is insufficient for Level 2 adoption.

The reviewer provided no substantiated different candidate in that initial
review. A later proposed Boolean nilpotent wrapper was separately checked;
its exact local prior construction and rejection are recorded in
../../tmp/boolean-nilpotent-gate.md. That separate rejection does not establish
Level 3 status of this finite-ring residual generator.

Keep the implementation, its existing 531-input full-digest results and the
proofs as research assets. Do not convert correctness, additional coefficients,
different schedules or unrelated convergence references into a novelty claim.
