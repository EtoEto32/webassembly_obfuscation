# Permutation-graph carrier: expressiveness gate

2026-10-12. Rejected simple candidate; no novel obfuscator or Wasm implementation claimed. CSEC unchanged.

## Proposed rule and target

Represent a bit by the parity of a permutation stored as a graph with one successor per node. Many concrete graphs encode the same bit. Compose, invert and conjugate graphs to operate without an explicit numeric bit. Target: hide intermediate Boolean computations from value/alias tracing. Observer may inspect the entire implementation and graph; no private hardware or hidden key is assumed.

The first required operation set is XOR and AND, sufficient to build bit-vector arithmetic. The candidate must be closed under these operations without quietly decoding the bit, running the original operation, and re-encoding. Merely storing an integer in a graph is not claimed new.

## Why this rule fails

Let p be permutation parity in GF(2). p(ab)=p(a)+p(b), p(a^-1)=p(a), and conjugation preserves p. Therefore the parity of any fixed straight-line word in input permutations, their inverses and constants is an affine Boolean function of the input parities. Input variables may occur any finite number of times; their occurrence counts reduce modulo two. AND is not affine, so this rule cannot implement it. This argument holds at any permutation size. It excludes only this parity representation and operation grammar: data-dependent word selection, other graph observations, or another decoder lie outside the argument.

check.py exhaustively checks all 14,400 ordered pairs of the 120 permutations of five elements. Composition obeys parity XOR and every commutator is even. An abstract closure of the two-input truth tables reaches exactly the eight affine functions, excluding AND. These are finite sanity checks supporting the algebraic argument, not a general impossibility theorem about graph obfuscation.

## An alternative is already known

Using identity for false and a designated five-cycle for true changes the decoder. The script finds two five-cycles whose commutator is another five-cycle, and checks the four input combinations: identity unless both inputs are true. All four outputs are even, illustrating why this different representation escapes the parity restriction. This small construction is a known permutation branching-program idea, not a newly designed algorithm, and does not itself establish security. No full circuit compiler, round randomization, Wasm backend or recovery benchmark was implemented.

## Primary literature and confirmation limits

- Barrington, **Bounded Width Branching Programs**, MIT-LCS-TR-361, June 1986. Official author/report record and abstract read: https://dspace.mit.edu/entities/publication/7b16f29b-5ef5-4614-95c8-3546518e4ece . It establishes the existing width-five branching-program direction. Full PDF retrieval returned 405, so detailed proof is not claimed read from that PDF. The script's example was constructed directly by enumeration.
- Asghar, Galbraith, Russello, **Obfuscation through simplicity**, author manuscript, July 2016. Section 4.2 previously read: https://www.math.auckland.ac.nz/~sgal018/simplicity.pdf . Discusses permutation/matrix branching programs and randomization for obfuscation. This rules out claiming that compiling Boolean computation into such a representation is a new general principle; it does not prove every possible graph transformation known.
- **Practical Data Location Obfuscation**, Microsoft Research publication page: https://www.microsoft.com/en-us/research/publication/practical-data-location-obfuscation/ . Abstract-level inspection only. Location hiding differs from evaluating over a graph-valued carrier; do not equate them.
- Dynamic graph watermarking author PDF located at https://www2.cs.arizona.edu/~gmt/pdf/dynamark.pdf ; direct fetch timed out. Search evidence only, not a reviewed algorithmic comparison.

Queries: obfuscation data encoding graph representation arithmetic pointer alias actual computation; obfuscation permutation parity graph; obfuscation data structure encoding Collberg; Barrington width five branching programs commutator 5 cycle pdf; obfuscation dynamic graph watermark constant encoding arithmetic Collberg.

## Decision and next condition

Reject parity-only graph arithmetic before building an expensive backend: the required nonlinear operation is absent. Do not patch it by claiming the known five-cycle construction is new. A successor needs a precise decoder and operations with proven closure, followed by a specific difference from branching programs and data-structure encodings. New graph layout or allocation patterns alone are insufficient. Overall goal remains active and unmet.

Reproduce with Python 3.12.14: run check.py. Standard library only, exhaustive enumeration, no random seed. results.json contains all reachable truth tables and the concrete five-cycle example. These are mathematical objects, not Wasm binaries; binary size/performance tests are inapplicable at this rejected design stage.
