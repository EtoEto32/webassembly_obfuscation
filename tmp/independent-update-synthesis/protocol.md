# Independent update synthesis feasibility gate

2026-10-12. Unlike the previous algebraic expansion, update coefficients here are independent unknowns in an SMT problem. Z3 is only a synthesis engine; Python integer arithmetic separately exhausts the finite state space. This is standard CEGIS infrastructure, NOT an established novel obfuscation algorithm.

Use 4-bit source states and inputs. Encode x as (a,b), D=a+k*b*b+l*b, k odd. Mask advances to b+1. Source update x'=x*x+c*x+u with c=3/5 depending on input parity. Synthesize k,l and two vectors of update polynomial coefficients, one per branch. Basis: 1,a,b,a²,ab,b²,ab²,b³,b⁴,u. No coefficient expansion formulas are supplied to the solver. All coefficients range over Z/16.

CEGIS alternates synthesis from sampled states and independent full checking over all 16³ (a,b,u). Add up to16 counterexamples per round. Timeout per solver call10s; stop after60 rounds. unknown/timeouts are inconclusive, not unsat. Save every candidate and counterexample batch before another iteration.

Control: fixed k=1,l=0 with separately synthesized updates. Joint case: k,l independent unknowns under same basis and bounds. Testing feasibility here does not demonstrate analysis resistance. Verify whether 4-bit coefficients lift to i32; do not claim that finite-width equivalence automatically lifts. A counterexample means reject that lifted artifact, not reject all possible co-synthesis.

Wasm generation should only proceed after a found candidate has been independently checked. No arbitrary-Wasm transform, no author implementation comparison, no performance claims at this gate. Goal still requires new transformation rules and analysis/cost evidence beyond generic CEGIS.
