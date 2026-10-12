# Symmetric-state candidate: executable prototype

2026-10-12. Status: semantic validation completed for generated samples; novelty and protective effect **unproven**, adoption pending. No paper produced.

## Concrete rule

For two lanes let s=x+y, p=x*y. Uniform update f(t)=t²+c*t+u induces

    s' = s² - 2p + c*s + 2u
    p' = p² + c*p*s + u*(s²-2p) + c²*p + c*u*s + u².

The transformed loop computes these updates without extracting x or y. Three lanes use e1=x+y+z, e2=xy+xz+yz, e3=xyz; generate.py derives all three updates, recorded in identities-3.json. The code calls them e0,e1,e2 (zero-based local names). Each iteration chooses c=3 for odd e1 and5 otherwise. The branch is permutation-invariant. Loop count is the supplied i32 n AND31; this bound is part of both samples' semantics, not an unnoticed validation shortcut.

The integer reducer uses the leading monomial of a symmetric polynomial and products of elementary symmetric polynomials. It verifies each result by expanding back and comparing exact integer coefficients before emitting Wasm. That is an algebraic identity check within the generator's polynomial implementation, not an independent proof assistant. It justifies modular arithmetic at any width if implementation is correct; the separate BigInt runtime oracle checks the actual compiled artifacts.

## Executed validation

Python3.12.14; WABT1.0.42; Binaryen133 with -O2 --enable-multivalue; Node24.15.0/V8 version in verification.json. Generator/tool paths fixed to the existing workspace .tools directory. Run generate.py using the existing Python, then verify.cjs using Node. Save a copy of this directory before rerunning because generated outputs are overwritten.

- Two lanes:1,888 inputs per binary, four variants.
- Three lanes:6,208 inputs per binary, four variants.
- Total32,384 executed comparisons, zero mismatches. Boundary inputs include wraparound/sign boundary and n=0,1,31,32,0xffffffff. Random seed0x3719b021,1,024 random inputs per arity.
- Outputs are all elementary symmetric coefficients after the loop, matching the specified original program. The independent oracle updates individual lanes using BigInt and calculates symmetric coefficients via a descending dynamic program; it does not import the generated symbolic expressions.
- Eight binary sizes/hashes in manifest.json. O2 normal/quotient:125/187bytes for two lanes and170/386bytes for three. No execution-time comparison yet.

Artifact types: dedicated polynomial-region generator, WAT samples, Wasm binaries, integer identity records, all input/output observations. This does not transform arbitrary existing Wasm or a practical hashing algorithm.

## Novelty audit and remaining work

The underlying mathematical rewriting is known. SymPy1.14.0 official symmetrize documentation explicitly describes conversion to elementary symmetric polynomials and shows x²+y² -> s1²-2s2. Read this function section; no SymPy implementation was run in the experiment.
https://docs.sympy.org/latest/modules/polys/reference.html#sympy.polys.polyfuncs.symmetrize

Other potentially relevant primary work: Hubert/Labahn, Computation of Invariants of Finite Abelian Groups, author PDF https://cs.uwaterloo.ca/~glabahn/Papers/MathCompV2.pdf . Search extract/INRIA project description only so far, not full technical audit. Its reported nonmodular group setting must not be assumed identical to arithmetic over Z/(2^32). Also compare existing data refinement and quotient minimization records before claiming any new mechanism.

Potential distinguishing issue is a compiler-region transformation that eliminates individually represented state while preserving invariant branches and modular semantics. This is a question to investigate, **not sufficient evidence of a new algorithm**. Classical math translated to Wasm is not the requested novelty by itself.

Next: enumerate inverse fibers at small width, attempt state/recurrence recovery with the binary and public inputs, inspect optimized intermediates, compare closest existing method and ablations, benchmark only after assessing whether protection is meaningful. Losing variable labels alone is not meaningful protection when labels are irrelevant to outputs. No secrecy claim from public inputs; no lower bound on root solving; no general cryptographic obfuscation claim. Current source remains easy to describe; a capable analyst may reconstruct an equivalent recurrence without recovering labeled values. Test that possibility explicitly.

Research scope stays independent from CSEC. No external pool/attack or protection changes. Account stopping threshold remains25% remaining.
