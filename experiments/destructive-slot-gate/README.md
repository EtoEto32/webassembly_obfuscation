# Destructive slot reuse: bounded rejection probe

## 1. Status

2026-10-12. Inconclusive; the invention goal remains active. No new obfuscator adopted. This is a small rejection probe following a prior-art check, not an interaction-net implementation or a novel graph rewriting system.

## 2. Completed

Implemented a reusable finite pure-SSA scheduler with destructive storage reuse and a trace-to-SSA recovery function. Four generated schedules for a SHA-256 round all recover the same output expressions. 285 inputs per schedule give 1,140 matching reference/physical/recovered comparisons.

## 3. Outstanding

An independent protection principle, new Wasm transformer, complete SHA application, fair superiority comparison and performance/optimizer evidence remain absent. This probe does not fulfill those requirements.

## 4. Proposed mechanism and conditions

Before: finite acyclic SSA nodes v_i=op_i(v_a,...), with pure total i32 operations. After: choose any ready node, read its operand slots, decrement outstanding use counts, release last-use slots, then overwrite one free slot with the result. Pin final outputs by counting them as outstanding uses. A slot may represent many different nodes over time. There is no retained runtime table of every intermediate value.

Invariant: for every live SSA value, its assigned slot contains its value. Operand reads happen before releasing/overwriting their slots. Induction over the generated schedule preserves outputs. Applicable operations here are add modulo 2^32, XOR, AND, NOT and fixed rotates. This argument excludes traps, public-memory aliasing, host effects, concurrency and allocation failure semantics.

Hypothesis under examination: destroying earlier values and reusing storage prevents recovery of the earlier dependency graph. It fails under the stipulated full instruction observation. Recovery maintains current[slot]=SSA version; it resolves sources before assigning a new destination version. That is ordinary dynamic SSA, not an invented attack. One final snapshot and a complete execution trace provide different information.

## 5. Prior art and novelty

Read/search date 2026-10-12. Queries: `software obfuscation "interaction nets"`; `software obfuscation "term graph" rewriting sharing`; `"obfuscation" "reversible pebble"`; `dynamic symbolic execution devirtualization temporary register reuse trace SSA Yadegari generic approach automatic deobfuscation 2015`; `"obfuscation" "destructive" "graph"`.

Primary source: [Symbolic Deobfuscation: From Virtualized Code Back to the Original, DIMVA 2018](https://binsec.github.io/assets/publications/papers/2018-dimva.pdf), related-work passage on printed p.19 / PDF p.19 (zero-based 18), and §5.2. The passage explicitly discusses handling reuse of one location for different variables by representing traces in SSA. This directly undermines the proposed protection argument. Authors' software and benchmarks were not run.

[Inpla author repository](https://github.com/inpla/inpla), README description and increment example, shows an existing interaction-net interpreter. Merely choosing graph rewriting as an execution model is not enough novelty evidence. Its implementation is not reproduced by this probe. [Term Graph Rewriting and Parallel Term Rewriting](https://arxiv.org/abs/1102.2651) was inspected at abstract level only; it is not used to claim an obfuscation result. Searches without exact matches do not establish novelty.

| Item | Assessment |
| --- | --- |
| Mathematical rule | Topological rescheduling plus last-use allocation; no independent new rule |
| Representation | Reused physical slots for SSA values |
| State transitions | Ordinary read-before-write execution |
| Dependency structure | Original operation dependencies preserved, temporal labels changed |
| Difficulty mechanism | Old values disappear from current storage, but observed writes remain versionable |
| Generalization | Finite pure DAGs; not arbitrary Wasm or dynamic graph rewrite semantics |

## 6. Reuse

`../sha-history-gate/check.py:reference` is reused as the numerical reference (A for this limited round test): it uses different equivalent Ch/Maj spellings. Its file hash is recorded. The deferred-graph audit (C, design evidence) already ruled out a persistent, labelled DAG as protection; this probe separately checks destroying/reusing its value storage. Existing full-SHA and Wasm results are not added to these counts.

## 7. Implementation and verification

Python 3.12.14 standard library. The SHA round has nine input words (eight state words and u=K+W modulo 2^32), 25 operation nodes and eight outputs. Test inputs are zero, all ones, 27 one-coordinate boundary cases and 256 deterministic random tuples. All 1,140 comparisons pass. Output-expression equality is checked by exact nested immutable expressions, including operand order. This establishes equality for the generated pure expressions; it does not require trusting finite numeric tests alone. No SMT run occurred.

Mutating the first recovered output to input zero's *position* (the first symbolic input, not the constant zero) produces mismatches on 271/285 inputs in each schedule. These controls test error detection, not security. The scheduler chooses among ready nodes from sorted IDs and seeds 619738..619741. Input seed: 619742.

## 8. Attack comparison

The recovery function receives only emitted physical opcodes, source/destination slots and output slots, with input slots 0..8 known. It does not receive the private source-to-slot mapping, original node IDs or expected output expressions. Evaluator code separately compares the result. Both functions run in one process; this is not a process-isolated blind attack.

Primary metric: output-expression recovery, 4/4 schedules. Each includes 14–16 slot reuses. Opcode recognition, binary instrumentation and unseen paths are outside this model. This is not a fair plain/MBA/new-Wasm benchmark or reproduction of DIMVA's tool.

## 9. Costs and optimization

The schedules use 19, 19, 20 and 18 slots respectively, versus 34 input-and-operation values without reuse. This is a storage count, not a measured runtime or protection improvement. Each command finished in under one second; no performance inference is made from it. Wasm sizes and optimizer survival were not measured because novelty and protection gates failed.

## 10. Improvement and decision

Persistent graph -> proposed destruction/reuse of value storage -> recovery by per-write SSA versioning -> rejection. The mechanism cannot defeat the stated observer. Changing only allocation seeds or increasing graph size is not a useful next experiment. A later graph-based design would need actual new semantic rewrite rules, not a renamed allocator.

The first check used SHA-256 expression fingerprints. To avoid relying on digest equality for structural identity, the checker was changed to exact expression comparison and rerun. Both results are retained; counts refer only to the final run and are not doubled.

## 11. Actual Before/After

`exact-artifacts/results.json` contains `before_nodes`/`before_outputs`, every generated `program.code`/`program.outputs`, and recovered SSA. The physical instruction triple is [opcode, source-slots, destination-slot]. These are complete executable IR programs interpreted by `execute`, not illustrative invented WAT. No Wasm After or optimized sample is claimed. `check.py:circuit`, `schedule`, `execute` and `recover` connect the generated examples to the rule and evaluation.

## 12. Artifacts and reproduction

Authoritative final result: `exact-artifacts/results.json`; per-input numerical evidence: `exact-artifacts/*-samples.json`. Initial fingerprint-based results remain under `artifacts/`. The final script refuses to overwrite an output directory.

```powershell
.\.tools\runtime-analysis-py312\Scripts\python.exe experiments/destructive-slot-gate/check.py experiments/destructive-slot-gate/reproduction
```

Run from repository root with a new output path. Source/protocol/reference hashes are in each result. No dependency installation or existing corpus modification is needed.

## 13. Limits and next gate

The exact expression comparison does not prove that original graph sharing, labels or source code were recovered. It proves the same ordered output expressions for these straight-line schedules. The result rejects only storage destruction/reuse as the protection mechanism under complete, decoded instruction observation. It does not refute general graph rewriting, partially observed execution or all virtualization. Further work must define a distinct update rule and an explicit recovery obstacle before scaling to SHA/Wasm.
