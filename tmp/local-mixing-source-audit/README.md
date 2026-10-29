# Local mixing: concrete prior implementation audit

Date: 2026-10-12. This is prior-art verification, not a new obfuscator.

## Sources and scope

1. Canetti, Chamon, Mucciolo, Ruckenstein, *Towards general-purpose program obfuscation via local mixing*, 2024, https://eprint.iacr.org/2024/006 . Read the abstract and metadata (last revision 2024-01-27). The general circuit construction relies on assumptions. Full paper/proofs were not inspected in this audit; do not claim its conjectures are established.
2. https://github.com/phantomzone-org/obfustopia . Read README only. Its limited O1 implementation and probabilistic correctness checks are not a complete implementation of all theoretical claims. No code from this repository was executed.
3. Vitalik Buterin, *Obfuscation (Part III): Local Mixing*, 2026-08-21, https://vitalik.eth.limo/general/2026/08/21/obfuscation_part_iii_local_mixing.html . Saved HTML and extracted text. Inspected generation mixing and gadgetization discussion, including correlations, XOR sharing and computation without instantiating original wires. This is an explanatory source; implementations and original papers must substantiate algorithm claims independently.
4. Article-linked implementation https://github.com/Local-Mixing/local_mixing at **5ce6daab669f50665f0c9aecf958f4066f407d01**. Retrieved recursive tree and selected files. Do not conflate this project with obfustopia or attribute all its later algorithms to the 2024 paper.

## Concrete overlap

Read docs/gadgetization.md through the start of optional preprocessing shuffling. Its embedded masking maintains logical values as carrier XOR sums of quadratic masks, expands masked operands without first decoding them, and refreshes masks while tracking dependencies. Random choices occur at circuit generation; evaluation uses the gate list, not a hidden runtime key. The document explicitly distinguishes balanced Boolean masks from independence of input-derived band variables.

Separately inspected the nonlinear193/nonlinear291 Python reference headers, imports, and nonlinear291 emitter entry points, and the complete selected unit-test file. These references implement a five-bit representation x0 XOR x1 XOR majority(x2,x3,x4), with two encoded shares per logical value. A canonical r57 update is decomposed into 291 gates of physical fan-in at most two. This is a concrete prior instance of nonlinear representation with encoded updates. **It is distinct from the current embedded-masking pipeline described in the document.** We did not run the full Rust pipeline or show equivalence between these two implementations.

Therefore reject these as standalone novelty claims for our project:

- nonlinear encoding by itself;
- never materializing a logical intermediate as a single physical value;
- jointly arranging masked updates and restored helper values;
- porting these gates to Wasm.

This does not reject all future transform rules in the area. A concrete rule with a demonstrable advantage could still contribute. The recent observation-frontier pruning rule is not established as novel by this audit, and the existing one-versus-two-operation Wasm example remains too weak to adopt.

## Local reproduction

Python 3.12.14, NumPy 2.5.3. Command, from this directory:

    C:/Users/ettotto/Documents/webassembly_obfuscation/.tools/runtime-analysis-py312/Scripts/python.exe run_author_tests.py

Harness loads only the two selected reference modules and the unmodified test file, using empty synthetic package containers instead of repository startup hooks. Source files retain their original content; filenames are flattened. The harness is ours, tests are upstream's. No network, mining or Wasm execution is involved in this reproduction.

**7 tests passed**, logged in author-tests.txt. Coverage: seeded sampled r57 output correctness, canonical gate count and fan-in, helper restoration, observed coverage of all eight logical truth-table rows, two-gadget composition, dirty-scratch bookkeeping and rejection of invalid scratch arguments. Seeds/sample sizes are in the preserved test code (including 512/17, 256/29 and 512/43). This is not exhaustive over physical encodings, an independent correctness proof, or evidence of security. Test wall time is not an obfuscator performance benchmark.

## Decision and next experiment

The previous plan to avoid decoded intermediates now has a concrete implemented comparator; an own trivial sharing variant should not be built as a purported new algorithm. Before selecting any new rule, compare it against the selected upstream representation under the same observer: complete public code, chosen inputs and all recorded intermediate values, with no secret runtime randomness. Decoding with a provided wire mapping is only a diagnostic upper bound; identifying that mapping without source annotations is a separate experiment. Preserve this distinction.

Next useful step: inspect upstream trace/security tests and establish their observer and attack success conditions, then identify a specific limitation a new transformation could address. Do not infer resistance from the seven functional tests. No new candidate was adopted, no performance advantage measured, and the overall goal remains incomplete.

CSEC paper and existing experiments were not modified.
