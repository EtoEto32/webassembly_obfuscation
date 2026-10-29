# Scope check: finite rewriting of reversible bit circuits

2026-10-12. **Inconclusive for the invention goal; no candidate adopted.**

The preceding goal turn made progress by rejecting the literal modular-inverse pentagon rule. This follow-up investigated whether changing the generator presentation and applying relation chains supplies an independent generation mechanism. No such mechanism was established. The result below is a source-scope constraint, not a new experiment or a new rejection theorem for SHA.

Primary source: Miroslava Sotakova, *The normal form of reversible circuits consisting of CNOT and NOT gates*, ECCC TR05-128 (2005), [full PDF](https://eccc.weizmann.ac.il/report/2005/128/download/). Inspected the abstract, introduction, definitions, §3 and §4 through Theorem 4.1 and Lemma 4.3 in extracted PDF text. Later proofs were not independently audited; no author's implementation was run.

The paper studies unary and binary **bit** gates and explicitly distinguishes this nonuniversal family from ternary universal gates. Section 4 relates linear circuits to invertible matrices over F2. Theorem 4.1 gives finite defining relations for the CNOT/swap family. Thus finite relation-based rewriting and normal representations already exist for that family. This does not supply a normalization algorithm for arbitrary nonlinear i32 word programs or a complexity bound for recovering their source structure.

| Required comparison | Current judgment |
|---|---|
| Mathematical rule | Merely using group defining relations is not a new rule. |
| Representation | Changing names or presentations still needs an executable semantic representation. None was designed here. |
| State transition | The inspected normal-form result covers its stated bit-gate family. |
| Dependencies | Relation chains can change a circuit's intermediate wiring; that fact alone does not establish novelty. |
| Source of difficulty | No concrete protected recovery problem or increased recovery cost was demonstrated. |
| Generalization | Two i32 operands are not two input bits. Word addition includes nonlinear carry effects over F2 and is not covered just because it is a binary operator. |

Searches: `program obfuscation Tietze transformations group presentation`; `program obfuscation Knuth Bendix completion rewriting group relations`; `obfuscation reversible circuit global rewriting presentation relations`. Other returned papers, manuals and lecture notes were leads, not sources inspected sufficiently for a novelty decision. No absence-of-prior-art claim is made.

Reusable evidence: the existing local-mixing and braid records are design references (category C). This source provides an additional scope boundary; no previous numerical results were rerun or aggregated. The original `README.md` and all experiments were preserved.

Decision: do not implement a generator merely consisting of renaming generators and applying known relation chains and call it independent. Equally, do not cite this paper as an attack on word-level SHA or use it to exclude every nonlinear word rewrite. A specific differing rule and its executable semantics are still missing. No testable candidate was advanced.

Report status: (1) Inconclusive; (2) primary-source scope checked; (3) novelty, transformer, SHA application and superiority unmet; (4) no invented algorithm; (5) comparison above; (6) existing records reused as references; (7) no implementation or correctness run; (8) no attack experiment; (9) no cost, size or optimizer measurement; (10) no successful improvement cycle; (11) no completed Before/After because no rule was defined; (12) this note and cited PDF identify the evidence; (13) nonlinear word programs and concrete independent generation rules remain unresolved. No external blocker or completion is claimed.
