# Observational quotient: rejection gate

2026-10-12. This is a feasibility gate, not a proposed novel algorithm. Test whether eliminating non-observable state provides a protection unavailable from ordinary finite-state minimization. Do not call irrecoverable, irrelevant source state a successful protection of behavior.

Use four finite deterministic machines, all 256 possible initial states, two input symbols 0/1, observable output s & 15 at every step. Polynomial, rotation, upper-bit conditional, and division transitions exercise distinct information dependencies. Compute the coarsest output-preserving congruence by elementary signature refinement, NOT an implementation of Hopcroft's optimized algorithm. Independently check it by pair distinguishability fixed point.

Generate native arithmetic and quotient table Wasm, raw and Binaryen -O2. Exhaust all 512 state/input edges per binary and initial outputs. Check commuting transition/output equations against an independent BigInt arithmetic implementation. Closure of the finite relation supports arbitrary finite input strings in this restricted model; it says nothing about arbitrary Wasm, memory, traps, imports, or timing equivalence.

An observer gets the final binary and its documented step/readout ABI and finite valid state range, not source equations or the original-to-quotient mapping. Exhaustively query every valid state/input pair to reconstruct the transformed machine. This is a strong chosen-state observer, not black-box access to a fixed initial state. Record query counts. Reject the candidate if the entire behavior is recoverable by this direct enumeration and there is no additional new transformation beyond ordinary quotienting. No performance claim or long benchmark is needed for a rejected gate.

No randomness. Preserve outputs, Wasm/WAT, hashes, original quotient map (verifier only), reconstructed tables (observer), and independent pair verification counts. This is a small dedicated generator, not a transformer for arbitrary binaries.
