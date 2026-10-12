# Packed-product candidate: carry interference and information loss

2026-10-12. **Inconclusive; no adopted new obfuscation algorithm.** This bounded cycle examined an arithmetic-packing rule, rather than another tensor-basis or scalar-multiplier variation. The proposed no-spacing, product-only rule fails semantic preservation. Its straightforward carry-free fallback is established arithmetic packing. The overall invention goal remains active and unmet.

## Candidate, threat model and budget

The source operation is a Boolean inner product, `F(x,y)=XOR_i(a_i AND b_i)`, where a_i and b_i are bits i of n-bit unsigned x and y. Such XOR/AND fragments can occur in Boolean arithmetic circuits, but no full SHA mapping is claimed here. A future matcher would need to recognize this fragment and its exact bit dependencies; no existing-Wasm matcher was implemented.

Proposed rewrite, with radix R=2^k:

    A = sum_i a_i R^i
    B = sum_i b_i R^(n-1-i)
    P = A*B
    output = (P >> (k*(n-1))) AND 1

The proposed representation after multiplication retains **only P**. The motivation was to combine many Boolean products into one integer operation and let cross-term carries obscure local gates. The intended attacker may inspect the whole implementation, arbitrary inputs, and execution traces, with no hidden hardware or key. Before claiming difficulty of reconstructing the original circuit, the representation must support its required output at all. This experiment tests that necessary condition; it is not an attack-time experiment.

The protocol was saved before execution: one design, n=2..8, all input pairs, k=1..ceil(log2(n+1)), 40-minute cycle cap, 60-second enumeration command bound, no random parameter search. Allocations are in `protocol.json`. The carry-free setting is a positive mathematical control, not a claimed competitive obfuscator. No dedicated memory cap was enforced.

## Mathematics and explicit counterexample

The coefficient of R^(n-1) in the formal convolution is c_(n-1)=sum_i a_i*b_i; its parity equals F. If R>n, every coefficient is smaller than R, so integer multiplication has no cross-coefficient carry and the selected bit is correct. This is the elementary correctness argument for the control, not a newly discovered rule.

For k=1 and n=4, compare:

| Inputs (x,y) | A | B (reversed bits of y) | P | Required F |
|---|---:|---:|---:|---:|
| (1,9) | 1 | 9 | 9 | 1 |
| (3,12) | 3 | 3 | 9 | 0 |

The same retained P requires different outputs. **No deterministic decoder of P alone can implement F on all inputs.** This is stronger than a failure of the proposed shift/mask expression, and is a correctness obstruction, not a security result. Zero-padding x and y at higher bit positions preserves the differing outputs and multiplies both packed products by 2^(n-4). Thus it applies for every n>=4 at k=1. The script checks the witnesses at n=4,8,16,32 in addition to the symbolic argument.

This does not exclude retaining operands, additional carry information, multiple products, other encodings, or input restrictions. Those are different rules requiring their own cost, correctness and novelty analysis. Availability of the original x,y elsewhere in a whole program does not repair the stipulated product-only representation; using them would change that rule. Conversely, no claim of whole-program impossibility follows.

## Executed results

Python3.12.14, standard library, deterministic exhaustive enumeration. Twenty (n,k) configurations cover 327,584 configuration/input cases; these are not 327,584 independent programs. Reference outputs use `popcount(x AND y) mod 2`, independently of packing. Saved collision witnesses are additionally checked by a separately written Horner encoder.

| n | k=1 extraction errors / cases | Products with conflicting outputs at k=1 | k=2 extraction errors / cases |
|---:|---:|---:|---:|
| 2 | 0 / 16 | 0 | 0 / 16 |
| 3 | 4 / 64 | 0 | 0 / 64 |
| 4 | 40 / 256 | 4 | 0 / 256 |
| 5 | 272 / 1,024 | 17 | 4 / 1,024 |
| 6 | 1,456 / 4,096 | 114 | 68 / 4,096 |
| 7 | 6,848 / 16,384 | 561 | 696 / 16,384 |
| 8 | 30,064 / 65,536 | 2,568 | 5,456 / 65,536 |

At k=2, no equal-product/different-parity witness occurs within n<=8, despite the listed extraction errors. Likewise n=3,k=1 has extraction errors but no such collision. These cases establish that the particular bit extraction fails, **not** that every product-only decoder fails. Their finite lookup consistency is not evidence of an efficient decoder at unrestricted size, a novel algorithm, or obfuscation resistance. They have not been silently counted as impossible or secure.

The seven carry-free controls cover 87,376 input pairs, with zero extraction errors or conflicting products. All additional tested k=3 or k=4 cases also extract correctly; full rows are in `results.json`. The sufficient R>n bound is not claimed necessary for parity extraction: e.g. n=4,k=2 passes although a middle coefficient may equal R.

Maximum exact product length across the enumerated configurations is 57 bits. This makes the small arithmetic representable in unsigned i64; it does not establish a general i64 implementation for larger n/k or report a Wasm runtime test. No Wasm, SMT, SHA, optimizer, timing-overhead or code-size experiment was justified after the early failure. There is no measured advantage over existing obfuscation.

## Primary-source comparison

Search/read date 2026-10-12. Queries included `obfuscation Kronecker substitution`, `obfuscation SWAR`, `obfuscation carry packing`, `Kronecker substitution bounded coefficients polynomial multiplication integer packing Harvey paper`, and `software obfuscation packing variable lanes cross carry polynomial multiplication`.

- David Harvey, [Faster polynomial multiplication via multipoint Kronecker substitution](https://arxiv.org/pdf/0712.4046), preprint 2007; published J. Symbolic Computation 44(10), 2009, 1502–1510. Read introduction, §3.1 and opening of §3.2, plus related §2 passages. Standard packing uses coefficient bounds; the reciprocal variant uses multiple evaluations and manages overlaps/carries during reconstruction. We did not run the author implementation or reproduce its full reconstruction algorithm. Therefore merely reducing padding and adding another evaluation is not an independent new principle. The author's [publication list](https://web.maths.unsw.edu.au/~davidharvey/index.php?page=research) supplies publication metadata and an implementation pointer.
- [US10944545B2, Obfuscated performance of a predetermined function](https://patents.google.com/patent/US10944545B2/en), description of input distribution, spacer bits, and §2.5 FIR example inspected. It explicitly discusses packing parts of multiple inputs, applying functions, separating results and combining that with bijections. We use this technical disclosure only to reject a broad claim that packed evaluation plus encoding is unprecedented. It is not verified identical to the proposed one-product GF(2) rule; no legal scope or effectiveness conclusion is drawn.

| Required comparison | Proposed rule | Assessment |
|---|---|---|
| Mathematical transformation | Evaluate bit polynomials at 2^k, multiply, extract a coefficient parity | Carry-free rule is classical Kronecker substitution |
| Representation | One integer product replaces local products | Concrete dependency regrouping, not established independent protection |
| State transition | Preserve only P after multiplication | Loses required information in the no-spacing case |
| Dependencies | Cross terms and integer carries couple bits | Coupling alone does not ensure correctness or difficulty |
| Difficulty mechanism | Analyst must separate products/carries | No resistance measured; a valid general decoder is missing for the proposed rule |
| Generality | XOR-of-AND Boolean fragment | Not an arbitrary-Wasm transformer or complete SHA implementation |

Search absence is not novelty evidence. These sources establish close existing principles; they do not prove every carry-aware packing design is known. The concrete no-spacing candidate is rejected by its counterexample, while the elementary repair lacks an independent-principle argument.

## Reuse, artifacts and reproduction

The existing Python runtime is reused directly (A). Previous tensor-quotient, shared-transition, phase-demand and semantic-fusion records were reread as design constraints (C), not rerun or added to the new counts. `tmp/demand-refinement-gate/README.md` was unavailable at the attempted path; no contents of that file were used. No prior SHA correctness count is presented as a new run. Existing CSEC, baseline, and earlier failed candidates remain unchanged.

`check.py` implements the candidate arithmetic and exhaustive classification. `sample.json` contains the actual evaluated Before/After rule and the saved counterexample; its After is explicitly an incorrect candidate, not a completed transformer. `results.json` retains all configuration metrics, first extraction errors, first semantic collisions and the zero-padding witness checks. Script and protocol hashes are included, and `inventory.json` records this directory's artifacts.

Reproduce in a copy without `results.json`:

```powershell
python check.py
```

The script refuses to overwrite results. No external dependencies or random seed are needed. No unmeasured performance or attack result is filled in.

## Decision, improvement and remaining goal

Reject the general k=1, product-only rule. The examined elementary repair increases spacing to prevent carries; it passes the stated correctness tests but returns to known Kronecker packing. Neither version meets the required novelty-and-effectiveness combination. Do not continue by merely changing radix or adding familiar multipoint reconstruction and naming it a new algorithm.

Goal §13 remains incomplete: independent new principle and definition; reusable new Wasm transformer; SHA application and complete correctness; fair baseline/proposal comparison; measured superiority; proposal costs/optimizer resilience; successful improvement; and a complete adopted-method reproduction package with generated examples. This directory is a bounded rejection record, not a replacement for those deliverables.

The useful new constraint is to distinguish **wrong extraction** from **irrecoverable sufficient information**. Future rules that deliberately combine carries must identify what retained state determines the required result, before claiming that ambiguity protects computation. This record does not establish the next useful novel rule; that is still the substantive research gap.
