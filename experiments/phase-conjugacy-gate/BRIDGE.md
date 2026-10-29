# Why an additive wordwise bridge cannot lift the toy result

2026-10-12. Follow-up to the reduced-width phase-conjugacy gate.

## 1. State

Inconclusive for the invention goal; goal remains active. The preceding turn was progress: it established and independently checked a finite-model obstruction. This follow-up excludes one proposed route for transferring that obstruction to real SHA-256, without claiming the transfer itself.

## 2. Established result

For every 1≤w<32, there is neither an additive embedding from w-bit modular words into 32-bit modular words nor an additive quotient in the opposite direction that also intertwines SHA-256's Sigma0 with any zero-preserving unary operation on the smaller words. Consequently the previous toy result cannot be promoted by such a primitive-preserving wordwise bridge.

## 3. Unmet requirements

The full 32-bit common-update question remains open here. No novel obfuscator, SHA application, resistance comparison or successful improvement cycle was obtained.

## 4. Precise assumptions and proof

Let G=Z/(2^32) with modular addition, and let

    S(x) = ROTR32(x,2) XOR ROTR32(x,13) XOR ROTR32(x,22).

Its additive subgroups are exactly H_t={x:2^t divides x}, 0≤t≤32. To see this without relying on an uninspected classification reference, take a nonzero subgroup and an element with minimal power-of-two valuation t. Write that element as 2^t c for odd c. Since c is invertible modulo 2^(32-t), its multiples generate all of H_t; minimality of t puts every subgroup element in H_t. The zero subgroup is H_32.

For any proper nonzero H_t, take b=max(22,t) and v=2^b. Then v belongs to H_t. Since 22≤b≤31, none of the three right rotations wraps the set bit, and

    S(v) = 2^(b-2) + 2^(b-13) + 2^(b-22).

The three bit positions are distinct. The lowest is b-22<t, so S(v) does not belong to H_t. Thus **no nonzero proper additive subgroup is invariant under S**.

### Embedding

Suppose E:Z/(2^w)→G is an injective additive map. Its image has 2^w elements and equals H_(32-w). If E f = S E for any unary f on the small domain, that image must be S-invariant, contradicting the witness above. This argument does not even require f(0)=0.

### Quotient

Suppose p:G→Z/(2^w) is a surjective additive map and p S = f p. Its kernel has 2^(32-w) elements and is H_w. Also f(0)=p(S(0))=0. For v in that kernel, p(S(v))=f(p(v))=0 would require S(v) to remain in the kernel, again a contradiction.

These results allow nonstandard additive maps, not only low-bit truncation. They require preservation of addition and Sigma0 **separately**; they do not rule out a representation that changes the operations with corrections or mixes all eight state words.

## 5. Source and novelty boundary

[NIST FIPS 180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf), §4.1.2, equation (4.4), was re-read from primary PDF text on 2026-10-12 to fix the actual 32-bit Sigma0. The subgroup/witness reasoning above is a direct elementary derivation, not a new obfuscation principle or a theorem attributed to NIST. This was a follow-up proof check, not a broad novelty search.

| Comparison item | Finding |
|---|---|
| Mathematical mechanism | Additive homomorphism plus operator intertwining |
| Representation | A wordwise subgroup or quotient |
| State update | Primitive preservation already fails at Sigma0 |
| Dependencies | Combined rotations cross the subgroup boundary |
| Analysis difficulty | None measured; this is a correctness condition |
| Generalization | All smaller modular widths under stated assumptions only |

## 6. Reuse

Read the current preceding README and scalar-verification result. Reused `sha-history-gate/check.py:q(x,0,0)`, which equals the actual 32-bit Sigma0 because Maj(x,0,0)=0. The recorded dependency hash identifies that source. Existing toy data and the old manifest were preserved.

## 7. Executed verification

`bridge-protocol.json` was written before execution. `check_bridge.py` generated exactly 31 specified witnesses, with no parameter search. All satisfied v∈H_t and S(v)∉H_t. Values from the reused rotation implementation matched the independently stated sum of three powers of two. Endpoint checks covered S(0)=0 and the computed outputs being in the 32-bit domain; the universal conclusions come from the proof, not those finite endpoint checks.

For a 2-bit quotient, t=2: v=4,194,304 is in the kernel but S(v)=1,049,089 has residue 1 modulo 4. For a 2-bit embedding, t=30: v=1,073,741,824 is in the image but S(v)=268,566,784 is not a multiple of 2^30. Python 3.12.14; standard library only. No SMT or proof assistant was used.

## 8. Attack comparison

Not performed. This does not imply any obfuscated real SHA binary is easy or hard to recover.

## 9. Cost and optimizer results

Not measured. No new Wasm binary was generated, and the number of witnesses is not an overhead or security metric.

## 10. Design decision

Do not spend resources increasing toy widths or searching for a wordwise additive lift of the old counterexample. The analytical bridge tested here is impossible. A real-width obstruction would need direct 32-bit reasoning or a materially different relation; none is supplied by these witnesses. No claim is made that this negative result establishes the desired new algorithm.

## 11. Before/After status

Before: actual 32-bit addition and Sigma0. Intended bridge: commute a wordwise additive E or p through both primitives. Section 4 shows why that rule cannot produce a valid After. There is no completed transformed program or optimized sample. The 31 primitive counterexamples are saved without being represented as full-hash inputs.

## 12. Reproduction and artifacts

Executed from repository root:

```powershell
& .\.tools\runtime-analysis-py312\Scripts\python.exe experiments/phase-conjugacy-gate/check_bridge.py
```

The command creates `bridge-results.json` and refuses to overwrite it. For another run, copy `check_bridge.py` and `bridge-protocol.json` into a fresh experiment directory directly under `experiments` so the existing sibling helper resolves; run the copied script. No earlier result needs removal. Results contain every witness, Python version and hashes of both source and protocol plus the reused helper. `bridge-manifest.json` covers this separate follow-up; the previous experiment's manifest is not rewritten.

## 13. Limitations

Failure of a transfer mechanism is not a proof that 32-bit common updates are impossible. Arbitrary joint-state maps, non-additive maps, affine offsets not preserving zero, corrected operators and redundant carriers are outside this lemma. Even a primitive-preserving quotient would require an additional argument connecting arbitrary E_i to the quotient before transporting the conjugacy obstruction. That argument is also absent. Independent novelty and comparative advantage remain the central unresolved goal requirements; this is not an external blocker.
