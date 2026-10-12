# Source audit — 2026-10-12

1. John Hopcroft, An n log n Algorithm for Minimizing States in a Finite Automaton, STAN-CS-71-190, January 1971. Primary technical report, CMU-hosted PDF. Read Introduction, Formal description, Correctness (printed pp1–3; PDF pp5–7). Introduction explicitly describes the older output partition / successor refinement procedure used for this gate. Our straightforward implementation is not his optimized O(n log n) implementation. Known minimization is sufficient to reject the bare quotient rule as a new algorithm.

https://www.cs.cmu.edu/~cdm/resources/Hopcroft1971.pdf

2. Roberto Bruni, Roberto Giacobazzi, Roberta Gori, Code Obfuscation Against Abstract Model Checking Attacks, VMCAI 2018. Primary author/institution PDF. Read Introduction, §3 example and §5 statements/assumptions. The transformation preserves an isomorphic reachable copy and complicates partition-refinement analysis using model deformation and opaque values. This is NOT the lossy quotient proposed here. Do not claim it anticipates every non-injective state transformation or that all CEGAR implementations are defeated.

https://arpi.unipi.it/retrieve/e0d6c92c-4ce1-fcf8-e053-d805fe0aa794/paper-VMCAI.pdf

Year confirmed by institution metadata: https://iris.univr.it/handle/11562/975619

3. Johannes Schneider, Thomas Locher, Obfuscation using Encryption, arXiv:1612.03345, December 2016 preprint. Read abstract and beginning of model on PDF p2. Its non-injectivity statement concerns the relationship between programs and encrypted obfuscations, not evidence of this specific runtime-state quotient. Its cryptographic/selector construction has not been reproduced; no security claim is adopted here.

https://arxiv.org/pdf/1612.03345

Searches: "obfuscation" "state merging" abstract interpretation; "obfuscation" "non-injective" transformation; "obfuscation" "bisimulation" minimization; "Obfuscation using Encryption" 2016 pdf; "Code Obfuscation Against Abstract Model Checking Attacks" 2018; Hopcroft 1971 n log n algorithm minimizing states finite automaton Stanford pdf.

USENIX legacy sec10/mobi search lead failed to open; not evidence. Search snippets about hardware-state merging, vendor tools, or cryptographic obfuscation are not verified proof of equivalent prior art. The rejection rests on the concrete known quotient construction and measured gate, not an exhaustive proof of absence/presence of all related work.
