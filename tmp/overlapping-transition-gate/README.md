# Partially overlapping transition representations

2026-10-12. A design feasibility experiment following shared-transition-gate. **No adopted obfuscation algorithm, no Wasm performance or resistance result.**

## Proposed relaxation

Instead of bijections onto the same whole space, let fixed injective representations E_L:S_L->Z and E_R:S_R->Z have partially overlapping images in a larger carrier Z. For every public input u, seek a deterministic common update U_u such that

    U_u(E_L(x)) = E_L(T_L(x,u))
    U_u(E_R(y)) = E_R(T_R(y,u)).

The representation persists across arbitrarily many transitions. Each mode has its own decoder on its image. There is no external mode parameter passed to U, no time-varying representation, and no change to the public input u. Allowing those mechanisms would define a different candidate.

Define R={(x,y):E_L(x)=E_R(y)}. Injectivity makes R a partial bijection. Determinism requires

    (x,y) in R => (T_L(x,u),T_R(y,u)) in R for every u.

This condition is also sufficient: identify paired points in the disjoint union of S_L and S_R, then apply the source transition on each class. Closure prevents conflicting successors. This is an elementary transition-system construction, not a new obfuscation principle. Shared states alone do not establish resistance; mode-specific decoding also needs accounting in a complete implementation.

## Experiment

Each mode has four states (2-bit words). check.py enumerates **all 209 partial bijections** per case, including the empty one. Every rejected relation has a stored first closure counterexample. For each accepted relation, the script constructs explicit embeddings and a common transition table, then checks decoding of every state/input transition through both embeddings. This second check uses the constructed table rather than the closure predicate, but shares the source transition definitions; it is not an independent specification implementation.

| Source pair | Public inputs | Maximum overlap | Accepted relation sizes/counts |
|---|---|---:|---|
| x+u / y²+u modulo 4 | 0,1,2,3 | 0 | 0:1 |
| x+1 / y XOR 1 | singleton | 0 | 0:1 |
| identity / square modulo 4 | singleton | 2 | 0:1, 1:8, 2:12 |
| identical addition | 0,1,2,3 | 4 | 0:1, 4:4 |
| addition / relabeled addition | 0,1,2,3 | 4 | 0:1, 4:4 |

The relabeling is p(y)=y XOR 3 and the right update is p(p(y)+u mod 4). Positive controls show the checker permits full and partial overlap where appropriate. Across five cases: 1,045 relations classified, 528 constructed-table transition checks, zero mismatches. These are finite state-model checks, not 1,045 programs or measurements of analysis resistance. All accepted embeddings/tables and rejected witnesses are retained in results.json.

## General obstruction for the add/square pair

For S_L=S_R=Z/(2^w), w>=2, suppose R contains one pair. Under all additive inputs, the projection of R onto S_L must then contain every state. As R is a partial bijection between equally sized finite sets, R is a full bijection. Taking u=0 forces every right state y to satisfy y²=y. This is false, e.g. y=2. Hence R is empty.

This argument, unlike the finite implementation check, covers i32 under the stated assumptions. It says the two invariant images must be disjoint in this design. It does not prove they are easy to identify in arbitrary binaries, nor rule out contextual, redundant, time-varying, multi-step or differently decoded representations generally. Encoding the mode in disjoint regions also needs comparison with existing virtual handlers; disjointness alone gives no new mechanism.

## Prior-art scope

Jan Rutten, **The Method of Coalgebra: exercises in coinduction**, February 2019, CWI. Primary authored text hosted for a university course: https://www.cs.cornell.edu/courses/cs4810/2022sp/Handouts/Rutten.pdf . Inspected title metadata and §8.2, Definitions 127, 129, 131–134. Transition-preserving maps and closure of related successors are established notions. The text's deterministic automata also have acceptance outputs; our calculation removes that observation constraint and adds partial-bijection requirements. It is not a reproduction of that text's language-equivalence algorithms, and it is not a source claiming novelty or security for our application.

The LOKI comparison in shared-transition-gate remains relevant to disjoint-mode fallbacks. This turn did not rerun the author's code or infer new claims about it. Broader amalgamation/automata search results were leads only; they were not used to assert that an exact obfuscator already exists.

Search queries: `automata amalgamation common subautomaton embedding partial isomorphism transition systems`; `obfuscation overlapping state encoding automata shared transition function`.

## Decision and reproduction

Reject this fixed, single-step, partially overlapping representation design for the intended mixed-operation example. It fails at the mathematical specification stage. Building Wasm lookup tables for these models would not resolve the missing novel rule and is not warranted by this result.

Python 3.12.14, standard library, deterministic enumeration, no seeds/dependencies. Copy the directory before running check.py because it writes results.json beside itself. No CSEC modification, mining, external execution, or protection-setting change. Overall goal remains active and unmet.

Next design must change how computation is represented, not merely how many states are allocated or how labels are permuted. Returning to different per-boundary bijections would revive an already rejected candidate. Any variable-duration or history-dependent alternative requires concrete rules and comparison to existing interpreters and virtualization before implementation.
