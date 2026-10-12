# SHA-224 final-round erasure: correctness prototype

2026-10-12. The implemented final-round rule is not adopted: its concrete
generation recipe is a Level 3 algebraic rewrite. See [novelty-decision.md](novelty-decision.md).
This experiment closes the real-hash implementation gap for the
provisional construction in [the research note](../../tmp/sha224-erasure-gate.md).

## Construction and domain

In round 63 (zero based) of the **last padded block only**, replace the incoming
working state by executing these assignments in order:

```
h = h + ((~e) & g)   // modulo 2^32, using the old g
g = 0
```

All padding, message expansion, rounds, chaining and digest serialization run
inside Wasm. SHA-224 uses the distinct IV in FIPS 180-4 section 5.3.2 and emits
only the first seven words, as specified in section 6.3.
Source: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf

Domain D: byte strings of length 0 through 1,048,576, written at offset 1024
in exported nonshared memory. Call `hash(length)` and read 28 bytes at the returned
offset 512. Calls are sequential and nonreentrant; the caller must retain the
round constants at offsets 768..1023. The module resets its chaining state on
every call. Lengths outside D trap before writing memory. Scratch uses offsets
0..415; digest uses 512..539; memory is fixed at 17 pages.

There is always a padding block. Data blocks get `last=0`. The first padding
block gets `last=(tail==256)`; if a second padding block is required, it alone
gets `last=1`. In particular lengths congruent to 56..63 modulo 64 must not
erase the state in the first padding block.

## Algebraic proof (all inputs in D, relative to the standard SHA computation)

For 32-bit words, let u=(e AND f), v=((NOT e) AND g). Their set bits are disjoint,
so Ch(e,f,g)=u OR v=u+v, including modulo 2^32. After the assignments,

```
h_new + Ch(e,f,0) = h + v + u = h + Ch(e,f,g).
```

Consequently T1 is unchanged; T2 uses only a,b,c and is also unchanged.
The final round outputs a..g are unchanged, whereas its h becomes zero
(the usual assignment is h_next=g). Wordwise feedforward preserves equality
of the first seven words. SHA-224 serializes exactly those words and no later
block reads the changed eighth word. All preceding blocks and rounds are
identical; induction over those steps followed by this final-step argument
establishes equality to standard SHA-224 for every byte string in D.

This is an algebraic proof of the transformation, not a mechanically verified
proof of the generator, baseline SHA implementation, runtime or full standard.
The tests below check the implementation against an independent implementation.
After feedforward the eighth chaining word equals the incoming B[7], not zero.
An input whose original final-round g is already zero need not change that word.
For fixed e and combined h+((~e)&g), many original (g,h) pairs map to the same
state. Thus information is actually erased; this observation does not establish
novelty or security.

## Reproduction and provenance

From the repository root, with Node and the existing WABT installation:

```
node experiments/sha224-erasure/build.cjs <fresh-output-directory>
node experiments/sha224-erasure/verify.cjs <same-output-directory>
```

Both scripts refuse to overwrite their results. `build.cjs` requires the exact
SHA-256 baseline WAT identified by SHA-256
`73149cec6f2d3505113cfed1e6c9d29e346006beaf5ed06edd4758cbdf806101`.
Each textual patch must match exactly once. It changes the IV, output length,
last-block parameter and final-round assignments. Original round expressions
derive from sha.js 2.4.11; see `../sha256-research-baseline/vendor/LICENSE`.
Baseline files, input corpus and prior results are not modified.

Four modules are compiled and WABT-validated: ordinary SHA-224, the erasure
candidate, and two deliberately incorrect controls. No optimization or attack
benchmark is part of this experiment. Generated source/binary hashes and tool
versions are in `artifacts/manifest.json`.

## Observed results

Node v24.15.0, V8 13.6.233.17-node.48, OpenSSL 3.5.5, WABT 1.0.42.
The existing 531-message byte corpus is reused, but SHA-224 expectations are
freshly computed using Node crypto/OpenSSL; no SHA-256 result is reused.
It includes empty, abc, the long standard message, million-a, all lengths
0..256, larger boundaries through 1 MiB, and 256 seeded random messages.
Empty and abc additionally have fixed expected SHA-224 strings in the verifier.

| Module | Bytes | Inputs | Digest mismatches |
|---|---:|---:|---:|
| plain | 3124 | 531 | 0 |
| erasure | 3152 | 531 | 0 |
| bad-no-compensation | 3139 | 531 | 531 (expected failures) |
| bad-every-block | 3149 | 531 | 473 (expected failures) |

The two correct modules made 1,062 full-digest comparisons. Their final internal
eighth chaining words differed on all 531 inputs. For the empty message these
words were 3184756683 (plain) and 3204075428 (erasure). This is a witness of
changed internal computation with the same complete 224-bit output.

The verifier also checks input preservation, a 64-byte post-input canary,
absence of a spurious eighth digest word, four rejected lengths with no writes,
and a valid call after rejected calls. The every-block control agrees on abc
(one padded block) but fails at lengths 56,63,64,65, checking the last-block guard.
Finite tests do not prove equality for all D. Full observations are saved in
`artifacts/verification.json`.

## Novelty and conclusion

Subsequent decision: [novelty-decision.md](novelty-decision.md) supplies the
complete operation-by-operation reduction and rejects this implemented rule
under the user's novelty criteria. The general transported formula is a
correctness description, not an independently established new generator.
The following paragraphs preserve the initial evaluation and review scope.

Correctness and real-Wasm applicability now have concrete evidence. The current
rewrite is explained by the elementary Ch decomposition, compensating h before
clearing g, and the fact that the last output word is discarded. A separate
nontrivial construction beyond known algebraic rewriting and observability-based
changes has not been established. The general transported projection
`R_i^-1 P R_i` has not been implemented at earlier boundaries here.

The prior-source comparison and its limitations remain in the research note.
Neither successful tests nor noninjectivity promote this experiment to a novel
algorithm. The overall research goal remains unmet.

The authorized independent reviewer read the generated WAT, block selection,
verification code and saved report. No concrete correctness gap was found;
novelty adoption remains unsupported. That review did not independently rerun
the experiment or perform SMT/optimizer checks.
