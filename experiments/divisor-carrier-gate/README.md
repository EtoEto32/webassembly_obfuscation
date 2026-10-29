# Divisor carrier: known algebra and chosen-input recovery

2026-10-12. **Inconclusive; the original invention goal remains active and unmet.** No new algorithm is adopted. This is a bounded examination of an integer-factor representation, including a nuisance-factor repair, not a new name for the earlier tensor or iterative representations.

## Rule and mathematical scope

Choose pairwise coprime integers a_i>1 and P=product_i a_i. Encode a w-bit word as

    E(x) = product_{bit i of x is 1} a_i.

On legal subset products A,B, with g=gcd(A,B), the operations are:

    AND: g
    OR:  A*B/g
    XOR: A*B/g^2
    NOT: P/A

Each operation selects the intersection, union, symmetric difference or complement of the atom sets. Exact division is valid on this invariant. The atoms need not themselves be prime, but must be pairwise coprime. For composite atoms the carrier contains whole-atom products, not all divisors of P.

The contemplated protection was that Boolean operations become integer GCD/division and that recovering the word might appear to require factoring large numbers. This is not an established independent principle: divisor representations of Boolean algebra and prime-exponent state encodings are existing ideas.

The small repair uses V=E(x)*r with gcd(r,P)=1, then normalizes an operand with gcd(V,P) before each operation and remasks its output. The executable tests select r=P*t+1, t a positive seeded 32-bit integer. This gives many representations of the same word, but public normalization removes them exactly. The proof applies to any coprime r, not just this sampler.

Arithmetic is over positive unbounded integers. Source words have width4 or32, but the representation is **not** native i32 arithmetic: the 32-bit case's P has 417 bits, before masking. No silently wrapping integer implementation is claimed. Addition, rotation, memory effects, traps, source loops and complete SHA are not implemented by this prototype.

## Public recovery, without factoring

The observer is allowed to select inputs at an identifiable encoder boundary and observe the encoded values, with the same atom mapping across queries and later values. P and width are public. It does not receive atom identities, prime factors, generator seed, challenge plaintexts or operator results. This is a strong and explicit boundary-observation model, not automatic location discovery in unknown Wasm, and not a SHA-digest-only oracle. Arbitrary full tracing is permitted in the intended larger threat model.

For query j, set input bit i iff bit j of the position number i is 1. For width32 these five patterns label every position uniquely. Start with one block P. For each observation V_j, split each current block b into gcd(b,V_j) and b/gcd(b,V_j), keeping the query-bit labels. Coprime masks cannot affect these GCDs. After five observations, the 32 labeled blocks are exactly the 32 complete atoms. This procedure uses no prime factorization and does not need to split a composite atom into its prime factors.

For powers-of-two widths w, there are log2(w) queries and w-1 splitting GCDs. These count only the splitting algorithm, not consistency checks, challenge decoding or bit-complexity of big-integer arithmetic. This algebraic argument holds for arbitrarily sized pairwise coprime atoms; the experiment below does not claim to benchmark hard RSA-sized factors.

`recover.py` runs as a separate child process and reads only the public JSON transcript. Private mappings are in separate files read by the verifier only through its own construction state. This is information separation in the implementation, not OS filesystem sandboxing. It recovers representation correspondence; it does not reconstruct arbitrary control flow or all source code.

## Preregistered run and results

`protocol.json` was saved before implementation/execution: one carrier with one nuisance-factor repair, two widths, fixed seed5221, 30-minute cycle cap and 20-second attack subprocess timeout. No dedicated memory cap or follow-up parameter tuning. Stop before Wasm/SHA expansion if reconstruction succeeds or an independent principle is absent.

The atoms are products of pairs from the first 2w primes, shuffled with seed5221+w. They are composite, pairwise coprime atoms, with no presumption of cryptographic hardness. Input/mask draws follow the single seeded generator as specified in `check.py`.

| Width | Input pairs | Output comparisons (AND/OR/XOR/NOT) | Queries | Splitting GCDs | Atoms recovered |
|---:|---:|---:|---:|---:|---:|
| 4 | all 256 | 1,024 | 2 | 3 | 4/4 |
| 32 | 64 boundary + 256 random | 1,280 | 5 | 31 | 32/32 |

All 2,304 output comparisons match direct Python bitwise reference operations. The masked operands also decode correctly in 1,152 operand checks. The verifier separately compares each unmasked encoded result with a direct encoding of the expected word. These overlapping checks are not independent trial populations. Width4 tests all input pairs; width32 is a finite sample. NOT is tested once per pair, so repeated x values are not additional unique unary inputs. Input sets are not asserted disjoint from the encoder query patterns; the attack never sees the validation outputs.

Controls: atoms6 and10 violate pairwise coprimality; encoding words1 and2 yields6 and10, whose GCD2 differs from the required encoding1 of zero. A representation containing only one prime factor of a composite atom is rejected by the decoder as outside the invariant. Neither control is described as a secure encoding.

No timing superiority, Wasm binary size, optimizer survival, SMT, fullSHA, or existing-method benchmark was measured. Correctness of these Boolean primitives does not establish a usable full obfuscator, and enlarged integers do not imply analysis difficulty.

## Prior art and inspection limits

Search/read date2026-10-12. Queries included `obfuscation prime factor encoding`, `Boolean algebra square-free divisors gcd lcm`, `FRACTRAN Conway prime exponent register machine original paper pdf`, and institution-restricted searches for divisor Boolean algebra.

- [Caltech IST4 Information and Logic lecture](https://www.paradise.caltech.edu/ist4/lectures/lect1119p.pdf): the indexed primary slide excerpt states the gcd/lcm construction on divisors and the square-free condition. Full fetch was rejected by the web tool for its approximately40MB size; the complete slides were **not** inspected. This is a limited primary excerpt supporting the established construction, not evidence of an identical obfuscator.
- [Complexity of Fractran and Productivity](https://arxiv.org/pdf/0903.4366), arXiv:0903.4366v3,2009: inspected the model introduction and located prime-exponent configuration examples. It supplies a related established arithmetic computation model, not this subset-product Boolean compiler. No FRACTRAN author implementation or universality proof was reproduced.
- [String obfuscation via Godel encodings](https://gist.github.com/josephnavarro/27613a1c2ba2bd333d5f2e687f28bd50): read the author's explanation and `convert_godel` code. It uses per-position prime powers for string representation. It is not a source claiming the same gcd update rules or measured resilience. The gist was not executed.
- A university-hosted algebra text at `math.ucv.ro/~busneag/auxiliare/books/Acadtot-1.pdf` timed out. Its full contents were not used as reviewed evidence.

| Comparison item | This candidate | Assessment |
|---|---|---|
| Mathematical principle | Subset products, GCD and exact division | Existing divisor/set algebra; no independent principle established |
| Representation | Composite coprime atoms rather than one bit per position | Grouping factors does not prevent GCD separation |
| State transformation | Normalize, apply Boolean set operation, remask | Nuisance factor is publicly removable |
| Dependencies | GCD couples large representations | Input labels expose atom membership under the stated observer |
| Difficulty mechanism | Presumed need for integer factorization | Concrete recovery avoids factorization entirely |
| Generalization | Boolean operations in the whole-atom carrier | No addition/rotation or arbitrary-Wasm support demonstrated |

These limited searches do not prove that every factor-based transformation is known or weak. The precise elementary carrier has no supported independence argument and fails its intended concealment condition. Increasing atom sizes alone would not remove the algebraic chosen-input recovery.

## Reuse, artifacts and next decision

Existing Python3.12.14 is reused directly (A). Prior common-iteration and tensor/representation rejection records are conceptual references (C), not newly rerun evidence. A corrected recursive `rg` search of README files in `tmp` and `experiments` found no matching prior factor/GCD candidate text; this limited filename/content search is not proof that every earlier artifact was checked. No prior SHA result is counted as a current run. Existing CSEC and earlier experiments remain untouched.

`check.py` implements the exact carrier operators, constructs transcripts, invokes recovery and verifies outputs. `artifacts/*.public.json` are the complete attack inputs; `*.private.json` retain construction mappings; `*.recovered.json` retain learned mappings and query/GCD counts; `*.checks.json` contain every input, masked representation, expected output and recovered output. `*.sample.json` are actual run extracts; Before is each expected Boolean operation, After is its stored encoded output evaluated by the formulas above. No fabricated WAT or successful full transform is supplied. `results.json` and `inventory.json` provide hashes and provenance.

Reproduce in a copy without `artifacts` using `python check.py`. Standard library only. Existing artifacts cause refusal rather than overwrite. Actual source/protocol hashes are saved by the runner.

**Decision:** reject this elementary carrier and its coprime-mask repair. Do not implement multiprecision Wasm or full SHA merely to measure a candidate already lacking the required novelty and concealment. A useful successor would need an operation/update rule with a different source of difficulty, not larger factors, renamed atoms or more nuisance masks.

Goal§13 is still unfulfilled for an adopted method: new independent principle and specification; reusable Wasm transformation; SHA application/correctness; fair comparison/superiority; costs/optimizer behavior; a successful improvement; reproducible adopted-method sources and examples. This is a failed-candidate record only. No global technical blocker was established.
