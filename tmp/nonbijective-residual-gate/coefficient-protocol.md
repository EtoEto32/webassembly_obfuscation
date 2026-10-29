# Coefficient recovery follow-up, 2026-10-12

Before execution: use exactly the eight existing observations, including all four
large-coefficient cases. No new candidate generation or parameter search.
Observer receives only observations.json entries. Verification receives the old
results.json source coefficients, separately from the observer's arguments.

For a=z-f(x,y), b=t-g(x,y), Q1=a+a(a+1)b and Q2=b+b(b+1)a,
the coefficients [z^2 t^0]Q1=-g and [z^0 t^2]Q2=-f. Coefficients
are polynomials in x,y over Z/(2^w). No integer factorization, division, or
assumption of small coefficients is required. This is direct expansion of the
existing rule, not a novel attack or obfuscation principle.

Success: both recovered coefficient dictionaries equal the saved original
polynomials modulo 2^32 for every case. Negative control: add one to the
recovered constant of f; exact comparison must reject every case. Save recovered
polynomials, all comparisons, runtime and SHA-256 of sources and inputs.
No Wasm extraction, execution, optimization or resistance claim follows.
