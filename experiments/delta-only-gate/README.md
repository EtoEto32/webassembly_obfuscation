# Difference-only execution: early rejection

2026-10-12. Inconclusive for the invention goal; no candidate adopted.

## Rule and scope

Before: s'=T(s,u), an eight-word SHA-256 round, each word modulo 2^32.
Choose a reference execution r'=T(r,u), encode d=s-r componentwise, and
contemplate an After update d'=V(d,u) that does not need r. The intended
output reconstruction would use the final reference value. This would hide
the base trajectory only if the difference update could avoid it.

For fixed u, let F(s)=T(s,u). Such V exists for every r,d exactly when
F is affine as a map of additive groups: F(x)=L(x)+c for a homomorphism L.
Indeed, F(r+d)-F(r)=V(d). Setting r=0 gives V(d)=F(d)-F(0).
Writing L(x)=F(x)-F(0) yields L(r+d)=L(r)+L(d). Conversely this identity
makes the difference independent of r. This is an elementary derivation,
not a claim about arbitrary change representations or restricted trajectories.

For the actual 32-bit round, use u=0 (the combined K+W input), d=(1,0,...,0),
and bases r=(0,0,...,0) and r=(3,0,...,0). With b=c=0 the relevant nonlinear
term is Sigma0(a). The difference Sigma0(1)-Sigma0(0) differs from
Sigma0(4)-Sigma0(3) modulo 2^32. A deterministic V with the same arguments
cannot return both answers. These are round states, not full padded messages.

Keeping r repairs computation via d'=T(r+d,u)-T(r,u), but the exposed pair
(r,d) immediately gives s=r+d. This does not reject all incrementalized
programs or protected representations of their reference state. It rejects
the claimed protection from this specific pair/difference rule alone.

## Prior work and decision

Read the author-final [Cai et al., PLDI 2014](https://inc-lc.github.io/resources/pldi14-ilc-author-final.pdf),
section 2.1, definitions 2.1 and 2.4, and theorem 2.9. Their change structures
already express computation of output changes from a base input and its change.
The definition explicitly permits dependence on the base input. No author
implementation or performance claim was reproduced. Cornell's incremental
computation overview was also opened as a lead, not as proof of equivalence
to a complete obfuscator.

Searches: `obfuscation "finite differences"`; `obfuscation "incremental computation"`;
`program obfuscation "differential encoding"`; `"A theory of changes" "incrementalization" pdf`.
The existing representation-gate-20261012 concerns a different carry-difference
profile of one word; its observations are not new results of this gate.

The mathematical change-propagation mechanism is known. The specific proposal
additionally fails correctness without the base and gives a direct decoder
when the base is exposed. Therefore it will not receive a Wasm transformer,
full SHA integration, optimizer runs or parameter search. This is not evidence
that every future change representation is unoriginal or insecure.

## Fixed check and artifacts

Before execution: exactly the two bases above, one delta, u=0. Reuse
sha-history-gate/check.py:reference and independently compute Sigma0 using
bit-string rotation. Check both expected difference vectors, their inequality,
and reconstruction r+d at both inputs. Save all states, outputs and differences,
runtime version, and SHA-256 of script, report and dependency. No random search,
statistical security estimate, performance comparison, or proof assistant run.

Run from repository root:

    .tools/runtime-analysis-py312/Scripts/python.exe experiments/delta-only-gate/check.py

The script refuses to overwrite results.json. For reproduction copy check.py
and README.md to a fresh sibling directory under experiments and execute it.
No previous artifacts need deletion. Results are primitive feasibility evidence,
not a completed After or a successful improvement cycle. Independent novelty,
reusable transformation, full SHA correctness and comparative resistance remain unmet.
