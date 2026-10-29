# Encoded root update — pre-experiment protocol

2026-10-12. A local arithmetic candidate gate, not a general Wasm transformer. No mining or external interaction. Novelty unestablished.

For width w>=3, E(x)=x+2x² modulo 2^w. Source step: x'=x+v, where v=u²+(u if x is odd else 3u), modulo 2^w. This includes nonlinear input arithmetic and a state-dependent branch, but is not a cryptographic hash benchmark.

Compute a root r congruent to 1+4x modulo 2^w directly from z=E(x). Start r=1; for k=2,...,w-1 toggle bit k when bit k+1 of 1+8z-r² is 1. Update z'=z+v*r+2v² modulo 2^w; parity of x equals parity of z. There is no explicit full x local in this update. Root lifting is known mathematics, not the novelty claim. The question under test is whether avoiding a full decoded local actually prevents an easy intermediate-state recovery.

Analyst receives w and each (z,r) pair before update and knows this fixed representation family. No source x or generator trace is supplied to observer.py. The verifier retains x for checking. This is an intentionally rule-aware observer, not blind binary recognition. Success is exact pre-update x recovery, distinct from source-code recovery. An easy recovery rejects the proposed benefit for this rule; it does not prove all encoded computations weak.

All x,u at widths 3..8 will be tested independently against direct source evaluation followed by E. Further 32-bit traces: boundary combinations and 1,024 seeded random starting states/input lists, eight steps each. Save actual counts, checksums, mismatches and versions. Zero mismatches does not establish general analysis resistance. Do not benchmark/lower this specific rule to Wasm if its defining protection claim fails.
