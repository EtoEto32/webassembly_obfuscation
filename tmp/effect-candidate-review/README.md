# Effect candidate: separate novelty from effectiveness

2026-10-12. This is a review of existing evidence, not an additional Wasm experiment or an adopted algorithm. Original trial reports are preserved. CSEC files unchanged.

## Verified saved evidence

audit.py checked all 26 input binary SHA-256 values against trap-prefix-recovery/artifacts-v3/results.json, and counted 5,824 successful ordered-log recoveries in those saved results. This confirms artifact consistency, not an independent re-execution. All 13 original programs contain a load after every store. The existing family-informed recovery heuristic explicitly exploits a forwarding group covering those stores. It is not a result for programs without such a load, inlined helpers, arbitrary optimizers, or source-expression recovery.

## Decision corrected in precision, not reversed

The earlier report already distinguished novelty from strength, so no erratum to its code or results is necessary. The current candidate remains rejected for its chosen protection objective. The successful recovery is evidence against hiding the ordered store trace under the defined observer; it is not proof that every rule in the implementation appeared previously. Likewise, familiar buffering, forwarding and commit ideas do not by themselves prove equivalence of complete algorithms. Neither fact licenses a claim of an effective novel obfuscator.

| Question | Evidence | Conclusion |
|---|---|---|
| Does this implementation preserve its specified behavior? | Earlier finite tests include return, trap class and all memory bytes | Supported for tested cases only |
| Does it hide the original valid store sequence in this corpus? | Saved 5,824 exact recoveries using family-specific instrumentation | No, under that observer and corpus |
| Is the complete rule identical to a prior algorithm? | Prior buffering/forwarding/exception ideas, but distinct conditions | Not established |
| Is there a demonstrated new protection mechanism? | Physical commit changes do not remove the retained logical trace | Not established |
| Should the same implementation be promoted as novel because the prior work differs? | No positive effectiveness evidence | No |

## Additional primary-source comparison

Rane, Lin, Tiwari, **Raccoon: Closing Digital Side-Channels through Obfuscated Execution**, USENIX Security 2015. https://www.usenix.org/system/files/conference/usenixsecurity15/sec15-paper-rane.pdf . Read section 3, Figure 4, sections 4.7 and 5.1/5.3 relevant passages. Raccoon buffers decoy effects; real-path writes are immediately visible. Its model assumes a sealed processor, encrypted off-chip values with integrity, and a trusted OS. It mitigates crashes introduced on decoy paths. This differs from arbitrary instrumentation of Wasm locals and from preserving externally visible memory after an original Wasm trap. It is a related mechanism, not a directly interchangeable security/performance baseline. No author implementation was executed.

LLVM current DSE source was inspected at https://www.llvm.org/doxygen/DeadStoreElimination_8cpp_source.html , including partial overlapping stores and mayThrow/unwind-visible objects. This confirms that exception visibility is a known compiler issue, not that LLVM DSE is identical to the candidate. Live document, commit not pinned; no compiler comparison executed here.

Searches: obfuscation precise exceptions; obfuscation store buffer; obfuscation memory transactional compiler; dead store elimination exceptions WebAssembly; Raccoon Closing Digital Side-Channels through Obfuscated Execution pdf. Negative search results are not evidence of no prior art.

## Consequences for a successor

Do not revive the same scheme by renaming helpers, inlining them, adding a familiar encoding, or exploiting a parser's unsupported case. Conversely, do not reject a future concrete algorithm solely because it uses an established abstraction. Require a new transformation rule, an explicit explanation of which dependency it removes or changes, correctness including observable faults, and comparable recovery experiments. Publicly observable trap-prefix values cannot be promised hidden while preserving them. Protecting the internal expression or dependency structure remains a legitimate goal, but must have a specified success criterion before measurements.

Current status: no newly adopted algorithm. The evidence distinguishes a failed protection objective from an unproven novelty judgment. audit.py can reproduce this review's counts and hashes using the preserved sibling candidate directories; evidence-audit.json contains exact sources and per-program details.
