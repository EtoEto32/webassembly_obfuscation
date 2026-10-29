# Oracle-only polynomial inversion baseline

2026-10-12. Implement a validation baseline, not a novel obfuscation method. Previous turn implemented and rejected encoded-root-update, so it was progress.

Assume a callable encoding P known to be an integer polynomial permutation modulo 2^w. The recovery routine receives only w and that callable, not its coefficients, inverse, source states, or intermediate roots. No attempt is made to locate P inside an unknown Wasm executable. This assumption is material: arbitrary access to an internal encoding is not automatically available from the whole program's public interface.

Let d be largest i with v2(i!)<w. Query P(0)..P(d). Fit the inverse values Q(P(i))=i in the Newton product basis with nodes P(i). At each stage solve the modular linear coefficient equation by removing the power of two from its denominator and inverting its odd factor. The code will keep Newton-basis coefficients; it does not reproduce the paper's full reduced-monomial output algorithm or author implementation.

Verify exact outputs independently using generated polynomial coefficients kept by the verifier, across widths 3..8 exhaustively and widths 16,32,64 with boundary and seeded holdout values. Include degrees 1,2,3,7,17,65. Count oracle calls; report failures, never replace them with a hard-coded inverse. No performance superiority claim; algorithmic calls are the planned metric. Preserve seed, coefficient inputs, inferred models, script hashes and results.
