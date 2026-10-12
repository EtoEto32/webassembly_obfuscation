# Implicit-equation candidate gate — 2026-10-12

Decision: do not adopt the simple nonlinear residual-mixing candidate as a new obfuscation algorithm. This directory is a mathematical feasibility gate, not a Wasm transformer, white-box cipher, or automated binary recovery tool. No CSEC files changed.

## Candidate comparison

| Candidate | Proposed mechanism | Current decision |
|---|---|---|
| Quasilinear equations | Replace evaluation by solving equations affine in output variables | Direct prior framework exists (RVP22); Wasm port alone not novel |
| Nonlinear residual mixer | Apply a nonlinear permutation Q to a vector of residual equations | Correctness feasible, but a known inverse cancels this layer; no supported new protection mechanism |
| Add rotations to mixer | Break the low-to-high-bit dependency of polynomial maps | Naive extension is not injective; explicit counterexamples below |

Threat model considered: analyst has the executable and knows the transformation family, may inspect intermediate computations. Desired asset is the original computational dependencies, not merely recovering identical outputs. This gate gives the analyst Q explicitly. It does not establish that an unknown Q can be recovered automatically from arbitrary binaries.

## Exact mathematical experiment

For a benign two-output program f(x,y)=(x+y,xy), form residual r=(z-f1,t-f2) modulo 2^w. Apply

Q(a,b)=(a+2(a*a+a*b+b), b+2(a+b*b)).

Let H denote the polynomial vector multiplied by 2. Q(r)=0 has exactly the original output as its solution: Q is a permutation and Q(0)=0. To invert Q at (p,q), start with any vector and repeat v := (p,q)-2H(v), simultaneously, w times. Polynomial maps preserve congruence modulo 2^k, so each update gains one correct low bit. Two fixed points must agree modulo successively all 2^k. This gives existence and uniqueness modulo 2^w. This argument is not a proof of implementation security.

Independent exhaustive root enumeration across widths 1..4 checked 69,904 input/output quadruples. Permutation/inverse checks covered all 340 residual pairs across these widths. Further 8,192 seeded random i32 residual pairs inverted correctly. All checks passed. Inputs, SHA-256, seed and per-width counts are saved in results.json and inputs.json. Python 3.12.14, standard library only.

Although Q makes residual equations nonlinear in unknown outputs, Q^-1 immediately returns the original residual system when Q is known. Hence higher equation degree alone is insufficient. This is an algebraic observation and a given-Q test, not measured resistance against a blind deobfuscator, not a test of RVP22, and not a claim all implicit representations are weak. Runtime evaluation overhead and Wasm binaries are intentionally not produced for this rejected gate.

The attempted rotation extension R(a)=a+2*rotl_w(a,1) is not a permutation: at w=4, inputs 2 and 8 both produce 10; at w=8, inputs 26 and 128 both produce 130. Rotation moves high bits into low positions, invalidating the congruence-preservation argument. These are small-width counterexamples to a width-generic claim, not a complete i32 analysis.

## Reproduction

Run check.py with Python. It rewrites results.json and inputs.json. The direct target f is evaluated without the inversion procedure; all possible outputs are checked at small widths. No network, external processes or protected inputs are needed.

## Next design requirement

Do not implement a full Wasm backend for this rule. Any successor must explain why its representation is not removable by a public, separable inverse; prove total, unique evaluation under Wasm arithmetic; and distinguish source recovery from legitimate public evaluation. A different polynomial, added rotations, or moving an existing implicit framework to Wasm is not enough. The broader new-algorithm goal remains incomplete.
