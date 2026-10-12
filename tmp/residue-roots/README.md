# Cubic coefficient-state recovery

2026-10-12. Previous turn was progress: occupancy invariant, real Wasm and independent execution validation saved. This turn attempts compatible-value reconstruction from the candidate's actual memory state. It does not identify the state format automatically and does not reconstruct source code.

## Corrected experiment and preserved initial run

v1/ preserves the original protocol, scripts, binaries and results. Its selection of first16/last16 of wasm-inputs.json accidentally included appended boundary cases instead of the intended random tail. Its134/256 success result is not the main result. The corrected observe.cjs uses first16 and the16 preceding the24 appended cases, i.e. last16 of the original1,294-case list. Thus the final set contains16 boundary and16 pseudorandom cases per raw/O2 module. Selection was not based on attack outcomes. This correction supersedes the literal tail rule in protocol.md.

observe.cjs edits only the binary export section to add an export for memory0. It confirms unchanged code-section bytes, checks all64 selected outputs against original binaries, then reads coefficient groups. Original and instrumented SHA-256 values and output checks are in instrumentation-checks.json. No exports or files of the preserved original artifacts were modified. Adding an export is for analysis, not a claimed application security boundary.

## Recovery algorithms and results

Known to recovery: each record's residue and three elementary coefficients; bit width32. It receives no input lane values, historical roots or reference trace. The known representation and buffer selection are supplied by observe.cjs, so this is a format-aware analyst.

recover.py uses monic root lifting and recursive synthetic division. Corrected selection:192 compatible triples,64 budget-exhausted observations, out of256. Budget is20,000 polynomial evaluations per group.

recover_joint.py uses x,y variables and z=s-x-y, enforcing pair/product coefficients together. With all values congruent mod4, changing x or y by a multiple of2^b while fixing the sum cannot change e2/e3 below2^(b+2), for b>=2. The search uses this lookahead and checks complete coefficients on every returned triple. The pruning has also been tested on all256 same-residue4bit tuples; this finite test is not an independent formal proof. Result:196 compatible triples,60 budget-exhausted observations, total1,540,104 visited nodes. Budget is20,000 nodes per group, not equivalent work units to the first method; these counts do not establish a fair algorithm-speed comparison.

Raw/O2 observations duplicate the same semantic inputs and states. The256 records are not256 independent challenges:32 source inputs x4 classes x2 binaries. Likewise the196 recoveries and60 exhausted cases count both binary versions. Do not interpret the latter as secure instances: the cap is small and stronger algorithms/budgets have not been exhausted.

## Historical values versus usable alternative values

Independent verifier verify_continuation.py consults source inputs only AFTER recovery.76 of the196 returned multisets equal the actually executed historical values; the other120 differ while producing exactly the same coefficients.36 complete execution instances (18 input cases, each raw/O2) had all4 classes reconstructed. Advancing the reconstructed and historical values through7 fresh-u steps each gave identical class coefficients and outputs for all252 follow-up steps. Inputs and outputs are saved in continuation.json.

This result supports a limited but material conclusion: for the successful instances, an analyst need not find the historically executed values to continue the same coefficient computation. Non-unique inverse representation by itself is not evidence of protection. This is not a source-code recovery claim, not an efficient algorithm for every modular cubic, and not a general impossibility result for obfuscation.

## Reproduction and remaining work

Node24.15.0: observe.cjs. Python3.12.14: recover.py, recover_joint.py, verify_continuation.py. Scripts overwrite current results; copy this directory to rerun safely. Source candidate path is the fixed absolute candidates/residue-occupancy directory. No additional packages. The experiment measured local recovery attempts, not program execution overhead.

Candidate remains unadopted: meaningful protection, original algorithmic contribution and fair comparative cost have not been established. Next research must compare this representation with existing quotient/data-refinement and algebraic encodings, assess lower-cost partial/equivalent-computation recovery without supplied layout, and decide whether any justified advantage remains before expanding implementation. Increasing polynomial degree alone is not an acceptable new algorithm. Preserve the observed partial successes and unresolved cases.

Goal remains active; user pause threshold25% remaining; CSEC files untouched.
