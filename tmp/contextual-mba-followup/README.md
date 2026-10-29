# Contextual MBA comparison follow-up and ProMBA baseline snapshot

Later audit: [normalization proof-width counterexample](../../experiments/promba-width-audit/README.md). It verifies a concrete width-policy counterexample with an independent evaluator; it does not execute the upstream program or establish that the stock learner produces the constructed rule. The historical inspection below remains unchanged.

2026-10-12. Research support record, not a new algorithm or an author-result reproduction.

## A2-MBA comparison still unresolved

Wei et al., **Unifying mixed boolean-arithmetic obfuscation by architectural and anti-generalization hardening**, Computers & Security 167, 104866 (2026), DOI 10.1016/j.cose.2026.104866. Publisher preview: https://www.sciencedirect.com/science/article/pii/S0167404826000428 . The 2025 SSRN preprint is https://ssrn.com/abstract=5550463 . Only abstract/preview metadata was accessible. A newly indexed SSRN Delivery URL also returned a JavaScript/cookie challenge, not a readable PDF. No access-control bypass or purchase was attempted.

The concrete construction, equivalence assumptions, and reported failures of ProMBA remain unverified. Do not equate its context-sensitive traps with the local invariant candidate merely from the abstract, and do not adopt that candidate as novel while this comparison is unresolved. No public implementation was identified in the searches below; that is not proof none exists.

## New baseline evidence

The authors' publication listing identifies **Simplifying Mixed Boolean-Arithmetic Obfuscation by Program Synthesis and Equality Saturation**, TOSEM 2026, DOI 10.1145/3816695: https://psl.hanyang.ac.kr/publications/ . Full publisher text was not retrieved in this turn. Its RCR artifact was obtained from https://zenodo.org/records/21241876 (version v1, July 7, 2026).

The 28,626,957-byte archive matches its published MD5 c68df8ff9fd4d19d6525f0cfb2be9837. SHA-256 is f89456a6a1ac07422c07723710b051d29255cf4805d78cc477a6974a25f6a2d3. It contains a harness, documentation and supplied outputs; ProMBA itself and dependencies are fetched by its Dockerfile. The Dockerfile uses unfixed repository heads and a mutable base-image tag. Therefore a future build must record all actual source commits and image digests; the ZIP hash alone does not identify the compiled analyzer.

Read the artifact README and Dockerfile. They describe custom-expression input and comparisons with/without equality saturation, scoped saturation and learning. The supplied outputs are **author data**, not new results from this research. The artifact's own report of 4,011 expressions is not our experimental sample count. No Docker image was pulled or built here.

## Fixed source inspection

Repository: https://github.com/astean1001/ProMBA . Snapshot commit **1e0b45057fdd4ca4835162a444bdb809f514a2c3**, committer date 2026-07-06. The complete GitHub tree response is retained, truncated=false. Four files were obtained from this commit and their Git blob SHA-1 values independently verified. inspect.py also verifies the archive and extracts only named documentation files; it never executes author code.

Inspected selected passages, not whole files or a whole-program audit:

- src/main.ml: normalize around lines 68–100; equality-saturation integration around 390–447.
- src/utils.ml: bitvec_length around 43–48, to_smt_file around 135–140, ask_smt around 285–316.
- src/options.ml: locations of equality-saturation and SMT timeout options.
- src/expr.ml: searched identifiers only; downloaded for follow-up, not fully inspected.

normalize generates a disequality query using a width selected from constants, then calls ask_smt false. In that path, the response test requires an unsat substring and nonempty stdout. This is source evidence about that path; **it does not establish a bug, an incorrect accepted rewrite, or the behavior of every solver path**. No author binary was run. In particular, the abstract's claimed attacks against ProMBA are not reproduced by this inspection.

For future comparisons, retain generated queries and widths and independently check returned expressions under intended i32 semantics. A small-width identity is not automatically an i32 identity. Distinguish valid simplification, equivalence disproved, verification timeout/unknown, parsing failure, and unsupported constructs. None of the latter categories by itself proves protection. Whole-program reachable-state equivalence and unconstrained expression equivalence also need separate checks for contextual candidates.

## Next concrete work

If a contextual candidate proceeds, first define its invariant and the exact reachable-state transformation, then test with both an unconstrained expression analyzer and a path-condition-aware evaluator. Before invoking this baseline, pin its runtime/dependencies and run the supplied benign custom samples with independent output verification. Do not run all author benchmarks merely to inflate results, or count adoption of a newer baseline as the requested new obfuscation algorithm.

The original goal remains active and unmet. No CSEC source, mining process or Windows protection setting was changed.

## Searches

`"Unifying Mixed Boolean-Arithmetic Obfuscation" github`; same title plus pdf; `"A2-MBA" github`; `"Haoming Wei" obfuscation code`; `"ProMBA" "github.com"`; title of the 2026 ProMBA paper plus pdf. Search results located sources; third-party summaries are not used as algorithm evidence.

## Local provenance

verification.json records source hashes and date. zenodo-record.json, commit.json and tree.json preserve metadata. artifact-* files and sample-custom.txt are extracts from the ZIP; their content is source material, not task instructions. INSTALL was extracted but not fully reviewed. Keep the author's license file with the artifact. inspect.py uses Python 3.12.14 standard library and rewrites only its extracted-document/verification outputs.
