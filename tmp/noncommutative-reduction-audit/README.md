# Noncanonical group representations: a prior-art boundary

2026-10-12, Asia/Tokyo. Bounded literature screen; no new algorithm adopted.

## 1. State

Inconclusive. The invention goal remains active. The preceding turn only confirmed repository access and made no research progress. This turn adds a prior-art constraint on a possible escape from the canonical-group rejection.

## 2. Established result

`experiments/group-order-gate/README.md` was inspected. Its rejection assumes a single canonical encoding E with E(x+y)=E(x)E(y). It does **not** reject a redundant representation with correction operations. However, removing those assumptions is not by itself an independent new principle: there is directly relevant earlier work on noncanonical group arithmetic.

## 3. Unmet requirements

No independent rule, reusable new transformer, full SHA application, comparative resistance result, or successful improvement cycle was obtained. Existing baseline correctness is not evidence of any of these.

## 4. Design direction screened

Before: `z = (x + y) mod 2^w`.

Contemplated After: represent a value by several group-related pieces, concatenate pieces for addition, and periodically reduce them while carrying auxiliary representation state. This is only a direction, not an invented or implemented transformation. No valid i32 rule covering XOR, rotations, traps and memory has been supplied. No executable After or Wasm result is claimed.

## 5. Prior art and comparison

Leandro Marin, *White Box Implementations Using Non-Commutative Cryptography*, Sensors 19(5), 1122 (2019), [publisher](https://www.mdpi.com/1424-8220/19/5/1122), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6427245/), DOI 10.3390/s19051122.

Primary-page excerpts supplied by search exposed §§2.7–2.8 and 3.2, surrounding head/link reduction text, and Algorithm A2. The representation uses heads and links; addition juxtaposes pieces. Reduction shortens them with a hidden modifier. A2 has the form g R(g^-1 w). Section 2.7 gives h pi_Y(r(x)) = pi_X(x)+b and composes reduction types as (b+hc, hl). Section 3.2 also discusses maps outside that affine reduction condition. These are prior-art mechanisms, not our inventions. Their security claims have not been independently verified here.

| Comparison | Consequence for this direction |
|---|---|
| Mathematical rule | Group action plus a reduction map is already described. |
| Representation | Multiple pieces and auxiliary modifiers are already described. |
| State update | Concatenation followed by reduction is not an independent new rule. |
| Dependencies | A changing modifier alone does not establish novelty. |
| Analysis difficulty | No resistance evidence was obtained for our direction. |
| Generalization | A correct and efficient SHA bitvector implementation remains unspecified. |

This rules out claiming novelty merely for those ingredients. It neither proves equivalence of every possible group-based construction nor refutes the cited scheme.

## 6. Reused work

The canonical-group experiment is category C for this decision: its proof clarifies excluded assumptions. Its archived numerical results were not rerun or aggregated. Existing SHA/Wasm infrastructure remains available but was not used to fabricate a candidate evaluation.

## 7. Implementation and verification

None in this cycle. The early novelty screen did not justify a new group arithmetic implementation. No author's implementation was executed.

## 8. Attack comparison

None. In particular, the power-of-two discrete-log attack from the canonical experiment cannot simply be transferred to a head/link representation lacking its exact homomorphism condition.

## 9. Costs and optimization

Not measured. No extrapolation from small examples to 32-bit SHA is made.

## 10. Design decision

Do not repair the rejected exponent representation merely by adding redundant pieces, noncommutativity, hidden modifiers, or periodic reductions and call it new. A future candidate must give the exact operation that differs from the cited reduction mechanism and a concrete reason it changes a target-dependent recovery problem. No such operation was established this cycle.

## 11. Before/After status

Section 4 records the ordinary source operation and unimplemented intended replacement. It is deliberately not presented as a completed generated sample. No prior source or experiment was modified.

## 12. Search provenance and reproduction

Search date: 2026-10-12. Queries:

- `program obfuscation cocycle skew product state encoding`
- `white box cryptography noncommutative group program obfuscation conjugation`
- `"White Box Implementations Using Non-Commutative Cryptography" "Reduction"`
- `"White Box Implementations Using Non-Commutative Cryptography" attack cryptanalysis`

Local `rg` searched Markdown records for `Marin`, `6427245`, and the paper title; it found no existing specific audit. A separate cocycle search found the earlier sandpile search, which was not treated as a new discovery.

Access limits: direct PMC open returned a browser challenge; direct publisher open returned HTTP 429; Europe PMC page and fullTextXML opens failed through the web tool. No challenge was bypassed. Search returned substantial primary-page excerpts with the equations and named sections above, but this is **not a claim of downloading or reading the entire paper**. No source archive/hash exists for this audit. Reproduction means checking the cited sections, not running a nonexistent experiment.

## 13. Limits and remaining work

This is a bounded exclusion of a broad design direction, not achievement of the requested invention. It does not establish that every future concrete redundant-group rule is known or insecure. Full-paper review would be necessary before relying on details outside the inspected excerpts. No technical blocker prevents other design work; lack of a viable invention is not a blocked status.
