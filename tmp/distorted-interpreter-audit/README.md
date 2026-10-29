# Analysis-guided synthesis: prior-art gate

Date: 2026-10-12. Research record, not a paper. No new algorithm is adopted here.

## Decision

The broad proposal to generate semantics-preserving transformations against a chosen analyzer is already established. Counterexample refinement is also an established target. Neither “analyzer-guided generation” nor “force more refinement” is an adequate novelty claim for our encoding-cosynthesis candidate.

This does **not** establish that every possible recovery-feedback synthesis rule already exists. The following papers do not, in the passages inspected, provide our still-unspecified rule for generalizing a successful decoder into synthesis constraints. That difference is an unresolved design task, not evidence of novelty.

## Primary evidence

1. Giacobazzi, Jones, Mastroeni, **Obfuscation by Partial Evaluation of Distorted Interpreters**, PEPM 2012, DOI 10.1145/2103746.2103761. Author PDF: https://profs.scienze.univr.it/~giaco/download/pepm12-giacobazzi.pdf
   Read: section 5.1 including Example 5.3, end of 5.3 including Proposition 5.8 and Theorem 5.9, section 5.5, discussion. Page 6 visually checked. The distorted interpreter is specialized to preserve behavior while losing information under a specified abstract interpretation. Data refinement and automated encoded operations are explicitly covered. This is not an implementation of our proposed decoder-feedback loop. We did not run Unmix or reproduce its results.
2. Bruni, Giacobazzi, Gori, **Code Obfuscation Against Abstract Model Checking Attacks**, VMCAI 2018. Author PDF: https://pages.di.unipi.it/gori/Papers/VMCAI2018.pdf
   Read: section 3 opening, section 4 algorithm and explanatory text through case 3, section 5 opening and theorem statements 1–4, section 6. Page 14 visually checked. Model replicas and changed transitions force partition refinement. The argument depends on the stated CEGAR partition model; it is not a universal lower bound against program recovery. Full behavior is preserved in the distinguished replica; the protected property is preserved across replicas. We did not implement or reproduce the algorithm.

Both PDFs and extracted text are retained with hashes. Not every page, proof, or reference was read. The original profs.sci host failed TLS hostname validation; the scienze host succeeded without disabling certificate verification.

## Comparison to the current candidate

| Proposed element | Closest evidence | Consequence |
|---|---|---|
| Choose a transformation to make an analyzer lose information | PEPM 2012 §5.1 | Not a new principle |
| Preserve behavior through data representation changes | PEPM 2012 §5.5 | Not a new principle |
| Make iterative refinement ineffective | VMCAI 2018 §§4–5 | Already a concrete research direction |
| Learn a constraint over encoding AND update grammars from a recovered expression | Not established by the inspected passages | Requires a concrete rule and broader synthesis prior-art review |
| Lower such a rule to Wasm | Neither inspected implementation | Porting alone is insufficient |

## Next development gate

Do not create another polynomial-coefficient sweep. Before a new implementation, specify the following as executable mathematical objects:

1. A finite encoding/update grammar and the actual intermediate observations after lowering. Define which internal semantics are protected, despite public outputs.
2. A decoder witness with a proof domain, not just a fit to samples.
3. A constraint on grammar choices derived from that witness. Distinguish exclusion of one exact candidate, exclusion of an equivalence class, and exclusion of an entire template family. Give a reason the generalization is valid.
4. A semantic-preservation verifier independent from the observation-based exclusion mechanism. “Recoverable” means undesirable for this objective; it does not mean semantically incorrect.
5. A concrete example in which the rule changes the update structure rather than merely selecting an encoding coefficient, and a same-budget comparison against enumerative/random search and correctness-only synthesis.

The missing contribution is item 3 together with item 5. Generic CEGIS is not that contribution. The prior 4-bit quadratic/cubic observer experiment and the independent-update synthesis failure remain rejected; this audit does not revive them.

Before claiming novelty for a concrete rule, compare it to conflict learning, syntax-guided synthesis pruning, semantic equivalence classes, and abstract-interpretation-guided synthesis. Failure to find the same wording is not a novelty test. Do not require the entire broad framework to be absent from prior art: a genuinely different, useful, verified rule can still be a contribution within a known framework.

## Scope and status

This turn adds source evidence and narrows an unimplemented proposal. It adds no new Wasm binaries, throughput measurements, or resistance results. The overall goal remains active and unmet. The CSEC paper and its experiments were not changed. User's later remaining-allowance stop threshold is 25%, overriding the stored goal's older 10% text.
