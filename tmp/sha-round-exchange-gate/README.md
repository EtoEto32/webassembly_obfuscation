# SHA-256 round exchange: injection-only repair is trivial

2026-10-12. **Mathematical rejection of a restricted proposal.** No new
obfuscation principle, Wasm implementation, or universal impossibility of
round restructuring is claimed.

## Proposal and exact obstruction

Write T_u for the ordinary SHA-256 round with effective injected word
u=K_t+W_t modulo 2^32. All rounds otherwise use the same function. The proposal
was to exchange adjacent round operations and repair their message injections,
while keeping the same start and end working state and the same later schedule.

For every fixed initial state s and words u,v,p,q,

```
T_q(T_p(s)) = T_v(T_u(s))  =>  p=u and q=v  modulo 2^32.
```

Proof: the a output of the first round is C(s)+p, where C(s) does not depend
on p. After the second round, that word is the b coordinate. Equality of the
two-round endpoint therefore forces p=u. The entire intermediate state is
then identical. Equality of the final a coordinate similarly forces q=v.
The converse is immediate. This is an elementary consequence of the round
equations, not a new cryptographic theorem.

Even state-dependent repair functions cannot change the effective injections
on the compared execution. This does not assert equality of their definitions
at unreachable states. If a compiler exchanges the K labels but compensates W
so that the effective sequence stays u,v, it has only renamed the decomposition
of the same injected words; it has not exchanged their actual action.

## Executed complete-message counterexample

`check.py` reuses the existing import-safe SHA round, padding, constants and
schedule helpers. It computes the entire one-block SHA-256 for an eight-byte
message, then exchanges just the first two effective injections and runs the
remaining 62 unchanged. Python 3.12.14 was used. The ordinary result agrees
with the independent `hashlib.sha256` result.

```
message: 0000000000000001
ordinary: cd2662154e6d76b2b2b92e70c0cac3ccf534f9b74eb5b89819ec509083d00a50
exchanged:701e0f5325876dabcc04d9a5f7e8548e9d32b9465e07e8201fd2e481f344acc8
```

The original first two effective words are 1116352408 and 1899447442.
Their difference, 783095034, equals the changed b-coordinate difference at
boundary two. The working states differ at all 64 tested round boundaries.
The 256-bit digests differ; no claim that every output word differs is needed.

For this single-block case the final difference is also proved, independently
of the numerical test: each remaining round with fixed injection is invertible.
Given its output (A,B,C,D,E,F,G,H), the old a,b,c,e,f,g are B,C,D,F,G,H;
T1=A-(Sigma0(B)+Maj(B,C,D)); old d=E-T1; and old h is recovered by subtracting
Sigma1(F), Ch(F,G,H) and the injected word from T1. Hence unequal states stay
unequal through the fixed remaining rounds. Adding the same IV coordinatewise
and serializing all eight words also preserve inequality.

This argument deliberately uses one padded block. It is not an assertion that
arbitrary unequal chaining states stay unequal through later compression blocks.

`results.json` stores the input, padding, both complete state traces, digests,
runtime version and hashes of the executed sources. The script refuses to
overwrite it. Reproduce in a copy of the repository with that result absent:

```powershell
.\.tools\runtime-analysis-py312\Scripts\python.exe tmp/sha-round-exchange-gate/check.py
```

## Decision and boundaries

The independent reviewer checked the argument and script, without rerunning
the experiment. They confirmed the modular equality and the restriction to
injection values on the compared execution.

Do not build a Wasm variant of this failed injection-only exchange proposal.
The test is a counterexample, not successful hash preservation. Existing 531-input
Wasm results concern a different candidate and are not reused as results here.

The result does not exclude different boundary representations, partial output
observation, changing later injections, or longer compensation intervals. Those
are separate constructions requiring their own novelty checks. In particular,
the previously reviewed eight-word steering construction must not be repackaged
as a novel long-interval repair merely to evade this two-round obstruction.
