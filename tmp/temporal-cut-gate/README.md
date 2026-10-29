# Temporal-cut candidate: rejected at design gate

2026-10-12. Previous goal turn was progress: independent synthesis audited, equivalence evidence saved, and next candidate identified. This turn implements a concrete scheduling candidate and its trace-aware rejection test.

## Rule and preservation

Define F(x,y)=x²+3y modulo2^32 and G(p,y)=rotl32(y,5) XOR p. Source iteration produces (F(x,y),G(F(x,y),y)). At transformed cut i the invariant is p=x_(i+1), y=y_i. The next cut executes G then F, while prologue executes F and epilogue G. Induction establishes final-output equivalence for every finite n, including separate n=0. This reasoning assumes total pure operations. It does not permit moving trapping, imported, or externally visible operations across boundaries without additional treatment.

The cut no longer stores x_i directly, but the previous cut stores it as p. Adjacent observations therefore reconstruct (x_i,y_i). This is an explicit recovery rule, not a claim that all possible scheduling obfuscations are easy. It also does not prove original source-code reconstruction.

## Executed result

Python3.12.14. Run experiment.py; no external packages.1,318 inputs (294 boundary cases and1,024 random cases, seed1729). All final outputs agree with the independent integer/bit-string reference. All20,868 source states, including input/final states, are reconstructed. Observations and expected/recovered traces saved in observations.json; digest in results.json. Two implementations use different rotation implementations. Finite tests complement the stated invariant; they are not by themselves a proof for arbitrary n.

Attack is rule-aware and receives cut ordering; it is not a blind attack against a compiled artifact. Both facts favor the analyst and are intentional for this early rejection gate. The claim under test—hiding state merely by moving the cut—is defeated even without full instruction traces. No Wasm or performance experiment was run because this concrete protection mechanism failed before lowering. This directory is a candidate prototype, not the requested final algorithm.

## Prior-art comparison

Li Li and Hai Zhou, Structural Transformation for Best-Possible Obfuscation of Sequential Circuits (author-hosted file host13li.pdf,2013 association from filename; venue/year metadata not independently verified in this gate).
https://users.ece.northwestern.edu/~haizhou/publications/host13li.pdf

Read abstract, III.B–III.E and IV.A–IV.C. They use structural circuit transformations and state re-encoding; their practical protection concerns a keyed performance mode. This establishes that retiming plus encoding is not new. It does not establish that every possible software scheduling algorithm is already implemented there, nor that its security claim transfers to Wasm. The completeness discussion is not used to reject all future algorithms. Our simple cut rule has no demonstrated novel mechanism beyond ordinary rescheduling, and fails the specified observer.

Searches2026-10-12: software obfuscation retiming loop state pipeline temporal encoding; program obfuscation retiming; obfuscation wavefront computation. Primary paper inspected via author PDF. Chisel author PDF reopened but no new detailed result extracted this turn; prior local audits remain authoritative for its scope. No author software implementation run.

## Decision and next constraints

Reject this simple temporal-cut rule. Do not rename it, randomize the offset, or count adjacent-trace blindness as a new algorithm. The joint-synthesis and temporal experiments together require a next candidate to change actual computation representation, with protection evaluated across the full trace. Pointwise encoding alone and scheduling alone each left an explicit recovery relation in the tested instances. That is not a general impossibility result.

Next unresolved work is to specify a distinct rule whose representation cannot be reduced to the already tested low-degree state decoder or a time-shifted copy, compare it with existing data-refinement/virtualization methods, and only then implement the full Wasm comparison. No adopted candidate yet. Goal remains active; CSEC paper untouched; user stopping threshold remains25% account allowance remaining.
