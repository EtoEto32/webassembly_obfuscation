# Symmetric-state public-API recovery

2026-10-12. Previous turn was progress: executable symmetric-state generator, eight binaries and independent correctness evidence were saved. This turn tests whether the sample recurrence is inherently learnable from the allowed public API.

## Results and interpretation

All eight binaries yield the unique model within the declared coefficient grammar: A=1, B_even=5, B_odd=3, G=1, D=0. Each uses32 chosen one-step queries. Recovered models match all32,384 held-out executions, including repeated updates and every output coefficient. Files ending .recovery.json contain every training query and model; results.json contains validation results. SHA-256 is rechecked by recovery recording, though no input-binary mutation occurs.

Important limitation: this is a family-informed black-box test, not blind program reconstruction. The analyst is told the quadratic per-lane family, parity partition, ABI and output meaning. Only coefficients are inferred. Inputs held out from fitting are the previously published validation cases, not a new independent benchmark collection. Model uniqueness is within coefficients[-8,8], not across all modular polynomial representations.

The public interface is identical for any semantics-preserving transformation. Hence this test inherently cannot distinguish obfuscators' protection against this same black-box learner. It establishes that THIS kernel/function-family pair cannot demonstrate secrecy of these coefficients against this adversary. It does not establish that symmetric-state transformation or all non-injective transformations are ineffective against structural analysis. The protocol's rejection of an advantage against this attack is fulfilled, but must not be enlarged into a universal rejection. Candidate remains unadopted with no positive novelty/security conclusion.

The no-source restriction applies to the recovery process's data use: recover.cjs receives binary path/arity/output path only; the verifier alone reads prior input lists. It is not an OS filesystem isolation claim. Prior design knowledge informed the hypothesis family. Total time in .recovery.json is enumeration timing, not program execution overhead or a carefully repeated performance measurement.

Run verify.cjs with Node24.15.0. It invokes child recovery processes and runs BigInt reconstructed recurrences. Source binaries are read from the absolute independent-repository symmetric-state folder. Copy this directory before repeating because results are overwritten. CSEC files untouched; no outside execution or network pool.

## Next design work

Extend the representation only if it gives a concrete new rule for variable-specific branches and a defensible protection target. Merely increasing polynomial degree to defeat this chosen grammar repeats the failure of encoding-cosynthesis-gate. The adjacent residue-design.md specifies a candidate update/merge rule and explicit limits for further implementation; not yet a successful or novel algorithm.
