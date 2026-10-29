# Temporal cut gate (2026-10-12)

Pre-experiment decision rule: reject this simple temporal-cut instance if adjacent boundary observations recover every original loop state. Do not mistake failure of a snapshot decoder for resistance against a trace observer. This is an arithmetic design gate, not an existing-Wasm transformer or an evaluation against a published deobfuscator.

Source recurrence modulo2^32: X=x*x+3*y; Y=rotl32(y,5) XOR X. Repeat n times, return both. Candidate moves the cut between X and Y: prologue p=F(x,y), then repeat y=G(p,y); p=F(p,y), finally return p,G(p,y). n=0 returns inputs with no prologue. n=1 uses only prologue/epilogue. All operations total, no memory, calls, traps, floats, or external effects.

Adversary knows candidate rule and receives the complete sequence of cut observations (p,y), inputs, and final output; no original source-state trace. Candidate-specific recovery takes x_i from the preceding cut's p and y_i from the current cut's y. Verifier alone holds original states. Thus this is a deliberately rule-aware attack, not blind inference. Analysis success is exact reconstruction of all source states, not original source-code recovery.

Test boundary x,y in 0,1,2,15,2^31-1,2^31,2^32-1, n in0,1,2,3,16,32 plus1024 pseudorandom cases seed1729. Save inputs and observations. Correctness reference uses unbounded integer operations and independent bit rotation. No performance measurement if the recovery gate fails.
