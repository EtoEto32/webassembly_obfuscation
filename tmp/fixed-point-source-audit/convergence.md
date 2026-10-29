# Conditional termination of the old residual iteration

2026-10-12. Corrected assessment: mathematical validity under stated conditions,
independence unresolved, not adopted. This closes a correctness question left
open in README.md; it does not establish a novel transformation.

Let R=Z/(2^w), hold external input x fixed, and number n SSA values in
topological order. F_i may depend only on x and v_j with j<i. Require each
F_i to preserve congruences modulo 2^k for every 0<=k<=w. Define

    H(v)=F(v)-2A(v-F(v)) = v-(I+2A)(v-F(v))

for any fixed matrix A over R, with synchronous updates using the old vector.
The unique solution r=F(r) is given by ordinary topological evaluation.

**Bound:** from every initial v, H^(nw)(v)=r. To prove it, suppose v=r mod 2^k.
Congruence preservation gives F(v)=r mod 2^k. Thus the correction
2A(v-F(v)) vanishes modulo 2^(k+1), and the entire iteration remains equal
to r modulo 2^k. Modulo 2^(k+1), each step therefore acts like F.
The first coordinate becomes correct after one step, the second after two,
and so on: triangularity and congruence preservation propagate the additional
bit. After n steps all coordinates equal r modulo 2^(k+1). Start at k=0
(v=r mod 1 holds automatically) and repeat w times. The root then stays fixed.
Replacing n by DAG depth is possible with the same layer argument, but the
check below uses n=2 and the stated nw bound.

The hypothesis is material. For w=2, F(v)=(0,v0>>1) and
A=[[0,1],[0,0]], the sole root is (0,0), yet H cycles through
(2,0), (2,1), (0,1), (2,0). Logical right shift does not preserve all these
congruences. This also directly demonstrates why uniqueness is insufficient.
It does not assert that every use of a right shift prevents convergence.

## Why this is not an adopted algorithm

The same old exposed residual layer remains: if A is given, set
B=sum[j=0..w-1](-2A)^j. The finite geometric identity gives
B(I+2A)=I because (2A)^w=0 in R. Consequently F(v)=v-B(v-H(v)).
This is an explicit rule-aware removal, not an unknown-binary matrix extractor.
This inverse is not a rejection criterion under the current goal. Proving
termination does not itself establish novelty either.
SHA rotations, memory, traps and source loops are not covered by this theorem.
Bit-blasting to different equations would require its own implementation and
correctness assessment; none is claimed in this original proof. Do not label
this family a new obfuscator merely because the conditional bound is available.

## Fixed verification scope (written before execution)

Use F(v)=(x,v0*v0+1), A=[[1,1],[1,0]], n=2. Exhaust x and both initial
coordinates at widths 1..4, then 64 seeded cases at width 32 (seed 20261012).
Check every two-step precision milestone and the final root; log counts and
one 32-bit trace. Separately confirm the three-step excluded right-shift cycle.
No parameter search, Wasm, security trials or performance measurement.

Run `.tools/runtime-analysis-py312/Scripts/python.exe tmp/fixed-point-source-audit/check_convergence.py`.
The script refuses to overwrite convergence-results.json. To repeat, copy
the script and this document to a fresh directory. Results record source
hashes and Python version. Finite tests support the implementation of the
examples; the universal bound rests on the induction above, not those tests.

Overall status: Inconclusive, goal active. No new algorithm, SHA After,
comparison advantage, optimizer result or successful obfuscation improvement
cycle is supplied by this proof supplement. No additional literature or
novelty claim is made; prior provenance remains in README.md.
