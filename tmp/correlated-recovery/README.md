# Correlated-state candidate: compatible-state reconstruction

2026-10-12. Follows the observation model and 100,000-check budget specified in ../correlated-state/README.md before this run. This is a candidate rejection test, not a general Wasm deobfuscator. The overall new-algorithm goal remains unmet.

## Observer and success criterion

The observer receives width and five coefficients X,Y,P,Q,R with their known definitions. It does not receive the original four values, external input sequence, source program, or private verifier records as arguments. A compatible quadruple is sufficient: success does not require recovering the original labels or historical values. A successful quadruple must encode to all five supplied coefficients, and the verifier checks eight subsequent updates against the original state.

observer.py runs in a separate child process. Its input is observations.json only; its output is recovered.jsonl. Original states are in verifier-only.json and are used by experiment.py after reconstruction. This is an interface separation, not OS filesystem isolation. The observer has a known representation; it does not discover the layout from an unknown binary. No Wasm binary was used or instrumented.

## Algorithm

From the two sums eliminate c=X-a and d=Y-b. Starting modulo 1, extend a and b by one bit, considering four possibilities at each depth. Reject a partial assignment unless ac=P, bd=Q and ad+cb=R hold modulo the current power of two. Depth-first search returns the first full-width compatible state. The budget counts each tested partial assignment, including rejected ones, and is 100,000 per observation. A no-solution result and a budget result are distinct; the former did not occur.

The procedure is ordinary modular constraint solving with a representation-specific elimination, not a new protection mechanism. Integer-polynomial congruence makes low-bit rejection sound: a candidate failing modulo 2^k cannot become valid modulo 2^32.

## Corpus and results

The source inputs are exactly ../correlated-state/inputs32.json, SHA-256 9a5fc857d47870c1c91217adbfdd70370ea8d120f4fa55c076ca2abcc1cbe40b, verified against that run's manifest before use. For each of its 2,673 boundary/random inputs, record the state after four original transitions, then reveal only its coefficients. These are 2,673 distinct coefficient tuples; no deduplication inflation occurs. The small-width control takes one representative for each of the 1,696 attainable 3-bit coefficient tuples, not all 4,096 original states.

| Width | Observations | Compatible states found | Budget exhausted | Same original pair orbit | Different compatible orbit |
|---|---:|---:|---:|---:|---:|
| 3 | 1,696 | 1,696 | 0 | 1,696 | 0 |
| 32 | 2,673 | 2,549 | 124 | 545 | 2,004 |

Every found state matched all five coefficients. Eight-step continuation checks totaled 13,568 at 3 bits and 20,392 at 32 bits, all matching. These checks are repeated steps, not independent reconstruction samples. Same-orbit means equality up to swapping the two whole pairs. The 3-bit source representatives were chosen during enumeration, so its same-orbit column must not be presented as recovery of every original small-width state.

For successful 32-bit observations, the median search cost was 264 tested assignments and the maximum was 50,991. All 124 unresolved cases reached the predefined 100,000 limit. Total 32-bit search work, including these limits, was 14,485,181 checks. Per-observation timings are saved as diagnostic data; there was one run per observation, so this is not a repeated performance comparison. A timeout/budget result is not a security lower bound.

## Decision

Do not adopt this standalone coefficient representation as an effective novel obfuscator. In this defined, strong observation model, most tested states admit inexpensive reconstruction of a continuation-equivalent representative. The many-to-one representation often loses history, but that loss does not prevent understanding or continuing its calculation. This addresses a substantive failure of the proposed protection rationale, not a parser limitation or an unsupported opcode.

This does not prove every future transformation using correlated invariants is weak, nor that every detail of the trial appeared in prior software. Algebraic novelty and effectiveness remain different questions. The prior mathematical context already prevents treating the invariant representation alone as a new idea; the current experiment adds negative protection evidence. Do not increase lane count or add a familiar outer encoding and report that as a new algorithm without a new transformation rule and new evidence.

No Wasm backend or runtime-overhead benchmark is added for this rejected standalone mechanism. Future research stays focused on the requested novel algorithm; these negative results are supporting records, not a replacement goal or a completed paper.

## Reproduction and artifacts

Python3.12.14, standard library only. In a fresh directory containing experiment.py and observer.py, run:

```
python experiment.py C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/correlated-state
```

The harness refuses existing observations.json and the observer refuses existing output. The parent gives the observer a 180-second process timeout; this did not fire. The experiment completed normally, with no live process remaining.

- observations.json: every coefficient-only input.
- verifier-only.json: original states and future inputs, outside the observer's input interface.
- recovered.jsonl: recovered states, statuses, costs, raw diagnostic timings.
- results.json: summaries, source and observation SHA-256.
- experiment.py / observer.py: generator/verifier and recovery procedure.

The existing correlated-state files and CSEC files were not modified. No external service, mining, security-setting changes, or third-party execution was involved.
