# Joint representations with a shared transition: feasibility gate

2026-10-12. Proposed design screened before Wasm implementation. **Not adopted; no novelty or resistance claim.** This is a different design question from changing polynomial coefficients: can different operations share exactly the same state transition through jointly chosen representations?

## Exact candidate and obstruction

Let S be a finite state space, and T_i:S->S the source operations at a fixed public input. Choose bijections E_i and G_i on the **whole same S**, respectively before and after an operation, and seek a common total U satisfying

    U(E_i(x)) = G_i(T_i(x))  for all x and every i.

Input and output representations can differ; this is two-sided equivalence, not necessarily conjugacy. No separate opcode input, extra state, or restricted image is allowed in this particular candidate.

The multiset of nonempty fiber sizes {|T_i^-1(y)|} is invariant under either bijection. Input permutation merely renames members of each fiber, and output permutation renames fibers. Therefore different fiber profiles make a common U impossible. Conversely, on a finite same-size set, matching fiber profiles suffice for existence of some input/output permutations: match equal-size fibers, then choose bijections within them. This elementary argument is not a new mathematical theorem.

For width w>=2, x+u mod 2^w is bijective, whereas x^2+u is not. For example x=0 and x=2^(w-1) have the same square modulo 2^w. Thus this candidate cannot jointly represent even those two operations. The argument applies at i32 width; finite tests below are checks of an implementation of the invariant, not the proof.

The obstruction does **not** apply automatically to redundant representations, different invariant subsets, lossy representations with retained auxiliary state, varying step counts, or a U with an additional mode argument. Those change the candidate assumptions and require their own correctness and prior-art checks.

## A second pitfall: vacuous common handlers

If every T_i is bijective and unrestricted boundary transformations are free, set E_i=identity, G_i=T_i^-1 and U=identity. All equations hold, but computation has merely moved to a boundary. Any future synthesis must account for the generated entrance, transition and exit code together, including observation of intermediate values and cost. Finding a common U is insufficient as a protection objective.

## Exhaustive finite check

check.py enumerates all 256 functions on four points and groups them by fiber profile. Independently, for each group's representative it enumerates all 24 input permutations and 24 output permutations and compares the resulting orbit to the entire group.

| Fiber profile | Functions | Enumerated orbit |
|---|---:|---:|
| 1,1,1,1 | 24 | 24 |
| 2,1,1 | 144 | 144 |
| 2,2 | 36 | 36 |
| 3,1 | 48 | 48 |
| 4 | 4 | 4 |

All five comparisons pass. Separately, widths 2 through 8 and four values of u per width give 28 add/square profile mismatches with explicit collision witnesses. The JSON includes profiles and witnesses. These are complete finite functional-model checks, not Wasm execution, performance, or deobfuscation measurements.

## Nearest concrete prior work

Schloegel et al., **Loki: Hardening Code Obfuscation Against Automated Attacks**, USENIX Security 2022. Primary paper: https://www.usenix.org/system/files/sec22-schloegel.pdf . This turn inspected passages in §4.1 concerning merged semantics, §4.3 on partial point functions, and §4.5–4.6 on dependent superoperators and interactions. The paper merges semantics with a selecting key, and synthesizes selectors; it also follows use-definition chains for superoperators. It does not impose this gate's same-domain/no-mode bijection constraint. No author experiment or implementation was rerun. Earlier local LOKI source investigations remain separate evidence.

Consequently “one function performs several operations,” “synthesize the selection,” and “merge dependent operations” are already established directions. Adding a disjoint mode subset to escape the obstruction is not automatically novel: compare its actual rule to these existing mechanisms. Neither this overlap nor our mathematical obstruction proves that every possible shared-transition algorithm is already known or impossible.

Searches: `obfuscation synthesis merged handlers semantic key LOKI instruction indistinguishability`; `obfuscation common transition function data encoding instruction fusion polynomial interpolation`. Search snippets were used to locate sources, not as proof of novelty or completeness.

## Reproduction and decision

Python 3.12.14, standard library, deterministic enumeration. Run check.py in a copied directory; it writes results.json beside itself. No new dependencies, external execution, mining, AV changes, or CSEC modifications.

Do not implement this exact common-full-state-bijection design as a purported general obfuscator. Its mixed-operation target is impossible, and the unrestricted bijective subcase has vacuous solutions. The original goal still requires a useful new rule with independently verified behavior and fair comparisons. For an alternative redundant-state design, first define the cross-mode state intersections and prove transition consistency there; mere disjoint embedding recreates a selector. That consistency condition is the next concrete design question, not a claimed solution.
