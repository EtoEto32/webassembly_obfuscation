# Independent review: the grammar is decided by its first operation

2026-10-12. Review requested by the user and performed by one sub-agent, then checked against the source by the parent agent. This is a source-level algebraic argument, not a new experiment, obfuscator, or security result. The invention goal remains unmet.

## Evidence and exact scope

`check.py` defines `u=op0(a,b)`, `v=op1(u,b)`, `w=op2(u,v)`, and exposes `O=(u,v,w,b)`. All pairs `(a,b)` are allowed. The decoder grammar includes every binary operation over every pair of observed components.

Read-only source identities at review time:

- check.py SHA-256: `8C94252D47DCE0B0FB60AEEA612DBA7A7386FAF5E80DAB561BC6138D1971FD73`
- results.json SHA-256: `70DF516A2FAE0EE383F8059DE179D2B4B882B7CAE6BA198060C8AD61F89493B3`

The stored run used 3-bit words. The argument below holds over all widths n>=1 with modulus 2^n, and does not require another enumeration.

## Factorization argument

For fixed grammar choices, every observation is a deterministic function of `(u,b)`. Conversely, `(u,b)` is a projection of the observations. Thus two inputs have equal observations exactly when they have equal `(u,b)`. Later computations cannot distinguish inputs already collapsed by this pair. Additional observations also cannot conceal the pair that is already exposed.

| First operation | Consequence, regardless of op1/op2 |
|---|---|
| u=a+b | a=u-b mod 2^n, one decoder operation |
| u=a-b | a=u+b mod 2^n, one decoder operation |
| u=a XOR b | a=u XOR b, one decoder operation |
| u=a*b | At b=0, a=0 and a=1 produce the same pair (0,0) |
| u=a AND b | At b=0, a=0 and a=1 produce the same pair (0,0) |
| u=a OR b | At b=2^n-1, a=0 and a=1 produce the same pair (2^n-1,2^n-1) |

The first three cases have decoders already contained in `DECODERS`, using observation indices 0 and 3. The last three cannot represent all possible a values without loss, because the stated distinct inputs have identical complete observations. Hence the 6^3 grammar has exactly 3*6^2 immediately recoverable choices and 3*6^2 information-losing choices. This explains, rather than remeasures, the stored 108/108 split.

More generally, increasing the number or complexity of deterministic downstream operations on `(u,b)` cannot repair either branch of this dichotomy while `(u,b)` remains observed. Increasing the word width also cannot repair it. This is stronger than a failure to find a decoder within one finite search, but applies only to the stated architecture and first-operation set.

It does not exclude other first-stage representations, restricted reachable domains, stateful encodings, or downstream access to additional a-dependent information. For example, restricting a multiplier operand to odd values changes the collision premise and needs a different analysis. It does not establish an attack on an unknown Wasm binary or hide the cost of identifying the representation.

## Consequence for the next action

Do not extend this grammar's width or downstream depth to seek protection, or treat faster pruning of this grammar as progress toward a protective construction. A replacement search domain must first demonstrate that its valid candidates are not all eliminated by an analogous architecture-level argument. That check is necessary, not a novelty or security certificate.

The old README sentence said: “The concrete contribution needed for the original goal remains a different useful transformation/update rule, not this generic pruning component.” Its intent concerning this generic pruning component is valid, but a reading that requires only a new state-update rule is narrower than objective section 2. That section also admits an independently new transformation-generation principle. The README now explicitly retains both routes. Ordinary implicant generalization, CEGIS, or a larger grammar alone does not establish such independence.

No source/result file was modified or rerun. No SHA, Wasm, optimizer, performance or attack comparison result is added. A concrete novel construction remains unresolved; the review does not claim that fixing this search limitation supplies one.
