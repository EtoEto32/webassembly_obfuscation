# GC dispatcher candidate B2: experiment plan

This is a falsification-oriented prototype of a candidate, not an adopted novel algorithm. The previous screening did not justify a novelty claim. This bounded experiment tests the stronger dynamic-state variant before investing in a general transformer; it relaxes the earlier plan's implement-only-after-novelty gate for a small rejection experiment, not for adoption.

## Claim under test

Replace the integer dispatcher state of control-flow flattening with a reference whose Wasm GC type identifies the state. Optionally change the state-to-type correspondence after each completed iteration. Does that representation materially change the information needed to reconstruct transitions, and at what execution cost?

Closest baseline: conventional dispatcher-based flattening with integer state. [O-MVLL's official documentation](https://obfuscator.re/omvll/passes/control-flow-flattening/) describes state-variable encoding. Our integer variants are restricted self-written controls, not O-MVLL or its exact encoding. Merely replacing integer states with GC types or applying a changing XOR encoding does NOT establish algorithmic novelty.

## Conditions, fixed before execution

- structured: original structured loop and data-dependent if.
- int-static: integer state dispatcher.
- int-rotating: state encoded as s XOR e; e flips between 0 and 3 after an iteration.
- gc-static: state represented by one of four preallocated, distinct struct types.
- gc-rotating: same four types, with state-to-type index s XOR e.

This 2x2 representation/rotation comparison prevents attributing effects of rotating the encoding to GC. gc-static removes rotation; int-rotating removes GC. All conditions compute the same kernel and cap loop count at n AND 63. No imports, networking, memory, or per-iteration allocations. GC tokens are immutable module globals; instantiation is outside steady-state timing and must be reported separately.

Two kernels: nonlinear integer mixing; bounded subtractive GCD step (both operands exposed in the packed i64 result). These are dedicated WAT generation templates, NOT an arbitrary-Wasm rewriter or a practical hash implementation.

## Meaning preservation

Invariant at dispatcher head: reference/type or integer pc decodes to logical state s, and x,y,n equal the corresponding structured execution point. State 0 tests termination and selects state 1 or 2 using the same data predicate. State 1/2 executes the original branch, decrements n, optionally changes e, and encodes state 0. A dispatcher cycle therefore simulates one structured iteration. Arithmetic is i32 modular; GCD uses unsigned comparisons/subtraction. All runs terminate because at most 63 work iterations occur. Generated code still needs testing; this argument is not a machine-checked proof.

## Predeclared analysis and rejection gates

Analyst receives Wasm bytes including type definitions and executable code, no generator labels/mapping/expected results. Success means reconstructing the state representation mapping and encoded dispatcher predicates, not recovering original source or all input/output functions. First inspect whether type allocation sites and the XOR epoch are plainly recoverable; do not claim strength from tool incompatibility. A formal static decoder or a documented manual derivation is needed before claiming recovery, and they must be distinguished.

Reject as a new algorithm if its only difference is a tagged representation of existing state encoding. Reject the local protection claim if type canonicalization and ordinary value flow reduce it to the integer control with no hidden information. Performance is not a substitute for this analysis. No source novelty conclusion from absence in search results.

## Measurement protocol

All five conditions, both kernels, before/after Binaryen -O2; same assembler feature flags and runtime. Independent JS reference with unsigned arithmetic checks boundary and seeded random inputs. Timed calls use an internal Wasm batch wrapper with identical input schedule to reduce host-call overhead; wrapper results checked outside timing. Warm up, randomize balanced condition order, retain seven rounds, report median/min/max and paired baseline ratios. Sizes and instruction counts refer to the whole module, including wrapper and helpers; separate raw/O2 conditions. Measurements are local and exploratory, not universal engine performance.

Source code and binary SHA-256, tool versions, failed builds and raw timing arrays must be preserved. No CSEC or LaTeX changes.
