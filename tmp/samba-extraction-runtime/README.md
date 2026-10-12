# SaMBA extraction prerequisite: actual egg 0.10.0 run

2026-10-12. Actual runtime follow-up to ../samba-source-audit/. No new obfuscation algorithm is claimed; goal remains active and unmet. This closes the previous distinction between a grammar witness and executing an extraction library.

## Scope and environment

Our own small Rust harness uses egg **exactly 0.10.0**, two active rewrite rules identified in the pinned SaMBA source, and the same negative-size cost formula. The author program as a whole was NOT run. Rules: add-to-and-or and or-to-add. The runner uses a node limit of 60 and iteration limit of 3. Two repetitions for each of four conditions, each in a fresh process with a three-second watchdog. The watchdog kills and reaps its own child if needed. Every process finished naturally in this run.

Rust compiler: rustc 1.97.0-nightly (64a965e90 2026-05-11), Windows, debug/dev build with overflow checks. Python 3.12.14. Cargo.lock here records resolved dependencies; transitive versions are not the author's full lockfile. The version match is specifically egg 0.10.0. This is a minimized behavioral reproduction, not an exact reconstruction of the published experiment environment. No release-build claim is made.

## Observed outcomes

| Input and extraction | Outcome in both repetitions |
|---|---|
| x+y, both rules, ordinary positive AST-size minimization | Success; x+y, cost 3 |
| x+y, both rules, negative AST-size minimization | Panic in the cost function's addition: integer overflow, exit 101 |
| x+y, only add-to-and-or, negative size | Success; expanded expression with AST cost -31 |
| x==y, both rules, negative size | Success; unchanged expression, cost -3 |

With both rules and x+y, the runner stopped at three iterations, with 27 classes and 35 nodes. The printed graph shows the cyclic dependency discussed in the preceding audit. In both negative-cost runs, the saturation-complete and extraction-start markers precede the panic; extraction-complete is absent. The positive-cost control on the same graph completes. Thus a generation failure cannot fairly be counted as resistance to simplification or reverse engineering.

The three-second timeout did not fire. Wall times near 0.21 seconds include process setup and saturation; they are diagnostic timings, not obfuscated-program performance measurements. The one-rule expression's size is an extraction observation, not evidence of security. No Wasm execution or new semantic testing was performed here; the previous independent identity checks remain separately recorded.

## Limits and research consequence

This demonstrates that the inspected negative-cost setup can fail even with a small finite graph. It does not show that every SaMBA expression fails, that the reported datasets are invalid, or how the full batch generator's panic-retry logic behaves. Its configured standalone x==y example is represented by the unmatched control and succeeds without transformation. Release integer arithmetic may behave differently and was not tested.

Do not silently repair the author generator and label the result an unmodified author baseline. A bounded extraction variant would need an explicit identity and separate results. Merely making this generator terminate is not the user's requested novel obfuscation algorithm. The next design must supply an actual new transformation rule and a protected dependency, with this method retained as a related comparison where usable. The current goal is not converted into a bug-finding study.

## Artifacts and reproduction

- src/main.rs: minimized harness, not upstream source.
- Cargo.toml and Cargo.lock: pinned library and resolved dependency set.
- run.py: watchdog and raw-output recorder; refuses to overwrite results.json.
- results.json: every stdout/stderr, return code, timeout flag, wall time, and executable SHA-256.
- target/debug/extraction-audit.exe: exact executable used in this run.

Copy the source to a fresh directory, run `cargo build --locked`, then `python run.py`. Do not overwrite the saved results. The copy in the sibling research repository preserves the executable but omits unnecessary build intermediates.

Primary references: https://eprints.cs.univie.ac.at/8730/1/2026_samba.pdf , section 3.1 and Algorithm 1; https://github.com/CDL-AsTra/SaMBA/tree/74ccd067f9d0b0b255f1140d0f581f499ed71cb9 ; https://raw.githubusercontent.com/egraphs-good/egg/v0.10.0/src/extract.rs . Source-reading details and the algebraic witness are in ../samba-source-audit/README.md. No external report, message, or issue was sent. CSEC files unchanged.
