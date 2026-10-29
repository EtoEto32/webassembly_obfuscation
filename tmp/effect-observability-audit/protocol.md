# Effect observability gate, 2026-10-12

Before executing: test a semantic limitation of log-free follow-up designs. Reuse prefix-div and all eight generated programs from trap-prefix-fusion/artifacts-v2. These nine have a valid first store followed by a division with input d. Supply a=b=0, d=0, e=1. Fourteen boundary x values and 50 deterministic xorshift32 values (seed 0x70ba3921); y=0x81234567. Native/deferred-coalesced, raw/O2, all existing artifacts.

An independent child process gets only binary, public input tuples and initial memory. It invokes run, catches the trap, and reads the exported memory at offset0. No debug hooks, function instrumentation, original IR, or encoding map. The verifier separately compares the observed word with independent BigInt calculation of the first source store. Save all observations and hashes.

Success means recovering this one committed store value for these chosen inputs. It does NOT mean recovering every store, the source formula, a secret, or execution order. Each case is one query. A trap whose memory is part of the required observable behavior must expose the same value under any semantics-preserving transformation. This limits the protection target; it is not an impossibility result for obfuscation generally. Do not falsely claim to have tested a new log-free implementation.
