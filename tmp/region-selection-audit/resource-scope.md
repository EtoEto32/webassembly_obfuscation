# ReSource: scope check, 2026-10-12

Primary source: Zhou et al., [Decoupling is a Necessity](https://arxiv.org/html/2608.27889v1), arXiv:2608.27889v1, 2026-08-28. Opened the previously uninspected lead directly. Read sections 3.2–3.4 and 4.1–4.2, and inspected Tables 1–3. No author implementation or artifact was inspected or executed.

The pipeline retrieves line-level suggestions, predicts a control skeleton, and refines generated code. Evaluation uses x86_64 programs decompiled with IDA 7.5, code similarity measures, and GraphCodeBERT retrieval against 10,853 source functions. Reported 83% Top-5 retrieval is source identification, not demonstrated executable equivalence or target-specific internal-state recovery. This distinction follows directly from the stated metric; it is not a reproduction of their experiments.

Decision for this project: do not substitute retrieval accuracy for the preregistered internal-binding recovery objective, or treat a predictor's unsupported representation as resistance. Do not implement a new evaluator solely to obtain a favorable score. The paper does not supply the missing independent transformation rule.

Current research status remains Inconclusive/active. No new algorithm, Wasm After, SHA verification, attack comparison, overhead measurement, or improvement cycle was produced by this reading. Existing phase-conjugacy README and BRIDGE were inspected; their limited-width obstruction still does not settle the 32-bit question. No additional toy-width sweep was run.
