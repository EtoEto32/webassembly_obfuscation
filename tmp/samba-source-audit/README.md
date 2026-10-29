# SaMBA comparison prerequisite: finite graph versus finite extraction

2026-10-12. This is a primary-source audit and an independently constructed semantic witness, not an adopted novel obfuscation algorithm. The research goal remains unmet. CSEC files unchanged.

## Sources inspected

König et al., **SaMBA: Increasing Mixed Boolean-Arithmetic Complexity Through Equality Saturation**, AsiaCCS 2026, DOI 10.1145/3779208.3785382. Author institutional PDF: https://eprints.cs.univie.ac.at/8730/1/2026_samba.pdf . Read abstract, section 3.1, Algorithm 1 and selected evaluation passages, not every page. The method explores equivalent expressions with egg, then selects using negative AST size. It specifies graph-size limits and rule verification with 32-bit Z3 queries. This establishes direct prior art for a proposal consisting only of equality saturation plus complexity-maximizing extraction. It does not establish that every different concrete search rule is already known.

Author artifact: https://github.com/CDL-AsTra/SaMBA , fixed tree/revision 74ccd067f9d0b0b255f1140d0f581f499ed71cb9. Read both Rust generators and Cargo.toml; read the beginning of z3_rules.py, not the entire verification file. Cargo.lock pins egg 0.10.0. Downloaded files are unmodified author material, kept separately from our check_cycle.py. The complete tree response is tree.json. No repository LICENSE filename was found in that response; this is not a claim about permissions outside the repository. No upstream code was published or sent to others.

The repository README's abbreviated source location initially returned 404. The saved recursive tree resolved the actual paths under equality saturation/src/bin/. No evidence depends on the failed URL.

egg 0.10.0 source: https://raw.githubusercontent.com/egraphs-good/egg/v0.10.0/src/extract.rs . Read CostFunction documentation and implementation context. Its documented cost condition requires the parent cost to exceed its children's costs. A negative node-count cost does not meet that condition. This is a compatibility concern, not by itself an observed execution failure.

## Independently constructed witness

Let arithmetic wrap modulo 2^w. Define A=x+y, B=x AND y, C=x OR y, and D=1+(NOT x OR NOT y). Two active rules present in **both** downloaded generators establish A=B+C and C=A+D. Substitution yields A=B+(A+D).

The resulting grammar has 10 classes and 12 nodes, recorded explicitly in cycle-results.json. Nevertheless, its root permits arbitrarily many traversals of the A-to-C-to-A cycle before terminating in x+y. Each traversal adds 12 nodes to the unfolded AST. Thus AST sizes 3+12k are available for all k>=0, so no largest finite AST exists. A limit on the number of graph nodes is not a limit on the AST represented by that graph. This reasoning concerns this specific reachable grammar and objective; it is not a claim that all extraction methods diverge.

Our script verifies the two source-rule strings are active, checks both identities and 16 bounded unfoldings on every 8-bit input pair and 4,096 seeded 32-bit pairs, and saves source hashes. There were 69,632 distinct pairs, 1,253,376 equality checks, and zero mismatches. Repeated unfoldings are not independent input samples. The unboundedness conclusion comes from the recurrence, not from finite testing. The identity also follows algebraically because D=-B modulo 2^w.

## What has not been established

We did not run the author generators or egg. The standalone generator's configured starting expression is (== x y), which the shown rules do not rewrite. The batch generator has different input handling, a three-iteration runner limit, and panic handling. Whether particular author experiments encounter a problematic cycle requires a bounded actual reproduction; the grammar witness does not discredit all published output or measurements. No runtime, compiler optimization, Wasm output, or deobfuscation success rate was measured here.

## Consequence for candidate design

A new candidate cannot claim novelty merely by maximizing expression size with equality saturation: there is now an inspected direct comparison. Before using SaMBA as a runtime baseline, verify finite extraction and preserve any failures as generation failures. Imposing an AST depth/size budget may make an extraction problem well-defined, but this would be a baseline engineering repair, not the requested new obfuscation algorithm. A promising successor must change the protected dependency or analysis problem, and demonstrate more than expansion by the cancelling B and D terms.

Next concrete check: execute a tightly bounded egg 0.10.0 harness with the two inspected rules, separate saturation completion from extraction completion, and compare a positive-size control. Then decide whether the author generator is usable unmodified for the required comparison. Do not treat a parser error, hang or unsupported operator as evidence of protection.

## Reproduction

Copy check_cycle.py, eqsat.rs and batch_processing.rs into a fresh directory, then run Python 3.12+ check_cycle.py. It refuses to overwrite cycle-results.json. Standard library only, seed 0x53414D42. This reproduces the independent witness, not the author experiments. Exact upstream paths are in tree.json; fetched source files retain their original names.

## WAMO source status update

The official ACM SIGWEB proceedings index now provides its abstract: https://www.sigweb.hosting.acm.org/toc/www26a.html . It identifies protection of model weights, operators and computation graphs. This improves primary-source confirmation beyond bibliography alone, but full transformation rules remain unread. Neither overlap nor non-overlap with a proposed exact-semantics arithmetic transformation is established. The earlier award-certificate identification remains valid.

Search trail: WAMO WebAssembly obfuscation pdf; 3774904.3792297 pdf; asmMBA pdf; WAMO Wang obfuscation github; WAMO Fengyuan pdf; asmMBA Hongjoo github; WAMO WebAssembly SIMD; SaMBA Increasing Mixed pdf; SaMBA Caroline github. Tigress's publication list supplied the SaMBA lead, not independent evidence of its effectiveness. No authors contacted.
