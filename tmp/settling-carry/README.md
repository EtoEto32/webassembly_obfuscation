# Settling-carry feasibility gate — 2026-10-12

Status: not adopted as a novel obfuscation algorithm. Dedicated pure-i32 DAG generator, not an arbitrary-Wasm transformer. CSEC files unchanged. No network imports or mining operations.

## Rule and scope

Each sweep updates every DAG node once, starting at a state/input-dependent cyclic offset. No readiness flags. Ordinary nodes recompute from current parents. Addition nodes retain carry C and use old C in S = A xor B xor C, then C = ((A and B) or ((A xor B) and C)) << 1. Arbitrary initial states are allowed. This deliberately evaluates descendants before some inputs settle.

For stable parents, carry bit 0 becomes zero after one update; induction makes the lowest k carry bits correct after k updates. After w updates the carry is correct, and the following update produces the correct sum using that old carry. Thus w+1, not w, is a sufficient bound. For a DAG, T(root)=0 and T(node)=max T(parents)+cost, where cost is 33 for a 32-bit carry node and 1 otherwise. Each node is visited once each sweep, so this conservative induction does not depend on within-sweep ordering. This is a mathematical argument, not machine-checked verification of the generator.

Only pure i32 add, multiply, XOR, constant rotate, unsigned comparison and select are implemented. No source loops, traps, memory effects, imports, floating point or arbitrary binaries. Select evaluates already computed pure operands.

## Failure preserved

v1/ contains the initial implementation and measurements. Its bound used w rather than w+1. Independent exhaustive testing found (w=1,A=0,B=0,initial carry=1) returns 1 after one update, expected 0. Passing the initial three-program test corpus did not validate the bound. Current generator uses 33; bounds are mixed=68, cross=100, select=69. No v1 timing is used as the current result.

## Results

18 binaries: three programs, normal/scheduled/carry forms, raw and Binaryen O2. Independent direct BigInt interpreter, 243 boundary cases and 1,024 seeded random triples each: 22,806 comparisons, no mismatch. SHA-256 and commands are in manifest.json. A separate exhaustive scalar recurrence test covers widths 1 through 5, 37,448 (A,B,C) triples, no mismatch with w+1 updates. This is not an exhaustive 32-bit verification.

Exploratory O2 timing, 65,536 calls/batch, nine rotated-order rounds after warmup, median milliseconds:

| Program | Normal | Scheduled | Carry | O2 bytes normal/carry |
|---|---:|---:|---:|---:|
| mixed | 0.8531 | 4.0544 | 44.0037 | 54 / 264 |
| cross | 0.8568 | 3.9675 | 68.1512 | 54 / 294 |
| select | 0.8672 | 7.0872 | 76.6051 | 67 / 290 |

Raw timings, min/max, CPU, Node/V8 recorded in timings.json. Single host, no affinity; JS-to-Wasm overhead included. Normal batches are short, so ratios are exploratory. Even the scheduled control is much cheaper than carry. Scheduled is a self-implemented ablation, not an author's prior-art implementation.

## Novelty/effectiveness decision

The carry equations are ordinary full-adder equations, not themselves a new algorithm. Asynchronous iteration and circuit obfuscation have prior work. The particular bounded DAG schedule could differ in details, but there is no demonstrated new protection mechanism. The generator leaves the operand graph explicit; recognizing the full-adder recurrence permits replacing a settled node with addition, then topologically evaluating the DAG. This is a design-level recovery argument, NOT an implemented binary deobfuscation result. There is no measured resistance gain to justify the large overhead. Reject this version for adoption; do not claim that all asynchronous software obfuscation is impossible.

## Prior-art search and limits

- Data Flow Obfuscation: A New Paradigm for Obfuscating Circuits, 2021, DOI 10.1109/TVLSI.2021.3060345. https://par.nsf.gov/servlets/purl/10298700 — indexed primary-PDF passages read, direct fetch failed. Asynchronous circuit/control-key design is a related direction, not verified equivalent to this software schedule.
- Structural analysis attack on asynchronous obfuscated circuits, 2024, DOI 10.1587/elex.21.20240107. https://www.jstage.jst.go.jp/article/elex/21/11/21_21.20240107/_pdf — primary indexed abstract/introduction only; full direct fetch failed. Hardware findings not replicated here.
- JP6212377B2 https://patents.google.com/patent/JP6212377B2/en — search index mentions carry calculation and obfuscation parameters. Direct fetch failed. No claim its transformation is identical.
- Properties of Carry Value Transformation, 2012, DOI 10.1155/2012/174372. https://onlinelibrary.wiley.com/doi/10.1155/2012/174372 — publisher search excerpt only; a lead for iterative arithmetic, not a full-text comparison.

Queries included obfuscation carry propagation; obfuscation asynchronous circuit software; software obfuscation chaotic iteration; obfuscation self-stabilizing; carry iterative addition xor circuit convergence. Search absence is not novelty evidence.

## Reproduction

Use Python 3.12.14, Node 24.15.0 / V8 13.6.233.17-node.48, WABT 1.0.42 and Binaryen 133. generate.py accepts the existing project's .tools directory as its positional argument. Then run check_carry.py, verify.cjs, measure.cjs in that order. Scripts overwrite root reports; copy this directory before rerunning. Keep v1 untouched.

Next research must establish a concrete protection mechanism beyond replacing arithmetic by familiar gates and redundant scheduling before extending this prototype. No adopted new algorithm has resulted from this gate.
