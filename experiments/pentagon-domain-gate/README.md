# Pentagon recurrence: no modular-inverse execution domain

## 1. State

2026-10-12. **Inconclusive; invention goal active.** The preceding turn was no progress. This turn checked a concrete alternative to scalar encoding, then rejected its literal machine-word realization. No new obfuscator was invented.

## 2. Established result

The proposed five-step identity insertion has no valid starting pair over Z/(2^w), for any w≥1, when division means multiplication by a modular inverse. Every execution becomes undefined by step three. This is a correctness gate, not a security result.

## 3. Unmet requirements

Independent novelty, reusable Wasm transformation, full SHA application, comparative attack superiority, costs and a successful improvement cycle remain unmet.

## 4. Rule and proof

Before: leave the pair (x,y) unchanged. Intended After: execute F five times, where F(x,y)=(y,(1+y)/x). Over rational functions, the scalar recurrence is

    x, y, (1+y)/x, (1+x+y)/(xy), (1+x)/y, x, y.

Thus F^5=id where all successive divisions are defined. The contemplated hiding mechanism was inserting and overlapping these relations to change intermediate computations. Neither a protected gate-generation procedure nor a resistance argument was supplied.

For a literal modular-inverse realization, the first step needs x odd. The second needs y odd. If both are odd, z=(1+y)*inverse(x) is even, and the third step needs inverse(z), which does not exist. If either was even, failure occurred earlier. Therefore there is no five-step execution domain, including at w=32. This proof covers every word pair, not only the tested widths. An even denominator with an even numerator may admit multiple solutions to a division equation; selecting one is a different rule, not a modular inverse and not justified by this rational identity.

## 5. Prior art and comparison

Primary text read: Robert Marsh, *Lecture Notes on Cluster Algebras*, [publisher introduction](https://ems.press/content/book-chapter-files/23023), §1.2, printed pp.7–8, PDF pp.3–4. It gives the k=1 sequence above, its five-periodicity and its name as the pentagon recurrence attributed to Lyness or Abel. This identity is established mathematics, not our contribution. An alternative Kent-hosted PDF fetch timed out and was not read.

The previously inspected local-mixing records (`../../tmp/local-mixing-source-audit/identity-generator-followup.md` and `../word-rewrite-audit/README.md`) already document identity-based gate generation and equivalent local replacements. They were re-read for scope; author experiments were not rerun. Merely supplying another known identity is insufficient to establish an independent obfuscation mechanism.

| Item | Assessment |
|---|---|
| Mathematics | Known rational periodicity |
| Representation | Two rational coordinates; no valid repeated modular-inverse carrier |
| Updates | Periodic local replacement, not an independently justified generation method |
| Dependencies | Intermediate expressions change, but no novel protection follows |
| Difficulty | Not measured; correctness fails first |
| Generalization | Literal inverse-based form fails for all power-of-two word widths |

Searches on 2026-10-12: `program obfuscation cluster algebra mutation pentagon relation`; `software obfuscation reversible circuit local rewriting nonlinear gates relations`; `Lyness 5 periodic map (1+y)/x Fomin Zelevinsky cluster algebra pentagon`; `Lyness map finite rings modulo powers of two periodicity`. Local Markdown search found no prior Lyness/pentagon/birational/cluster-algebra record. Neither a missing local record nor lack of an exact search match establishes novelty. No claim is made about every possible cluster-based construction.

## 6. Reuse

Reused Python 3.12.14, standard library, and existing local-rewrite design exclusions. No SHA baseline was rebuilt because this candidate cannot pass its domain condition.

## 7. Executed checks

`protocol.json` preceded execution. `check.py` tested every pair at widths 1..8: **87,380 pairs**, **zero completed five-step modular executions**. For each width with N=2^w, the first failures were step 1 for N²/2 pairs, step 2 for N²/4, and step 3 for N²/4. Modular inverse was actually attempted with Python `pow(a,-1,N)`; the code did not merely predict failure from parity. The first trace for each failure class is saved.

Three positive rational controls, using exact fractions and initial pairs (1,1), (2,3), (17,29), returned to their starting pairs after five updates. These are limited implementation checks, not the proof of rational periodicity. No SMT, Wasm or full-hash run occurred.

## 8. Attack comparison

None. Undefined arithmetic is not resistance, and this execution failure is not an attack-tool timeout.

## 9. Costs and optimization

Unmeasured; no candidate binary exists.

## 10. Decision

Reject the literal modular-inverse form. Do not widen the exhaustive test or integrate it into SHA. Changing the field, adding exceptional branches or keeping rational numerator/denominator state would require a different specification and novelty analysis; no such repair is claimed here. Algebraically simplifying all five steps to identity does not supply an obscured implementation. This rejection is not the goal's successful improvement cycle.

## 11. Before/After evidence

The intended identity-to-five-step rewrite is given in §4. `check.py` executes the attempted After only up to its first undefined inverse. `results.json` preserves those partial traces; no partial trace is described as a completed generated program. No WAT or optimizer diff was generated.

## 12. Reproduction

Executed from the repository root:

```powershell
& .\.tools\runtime-analysis-py312\Scripts\python.exe experiments/pentagon-domain-gate/check.py
```

The script refuses to overwrite `results.json`. Copy `check.py` and `protocol.json` into a fresh directory to repeat. Results include all counts, selected complete failure traces, rational control traces, Python version and source/protocol hashes. `manifest.json` identifies the four final files. Existing experiments and CSEC work were not changed.

## 13. Limits

This result excludes one literal arithmetic realization. It does not prove that all division-based representations, rationally derived polynomial identities, alternate fields, or local mixing are ineffective. It provides no new effective transformation. There is no external blocker; the task still needs an independent rule and measured superiority.
