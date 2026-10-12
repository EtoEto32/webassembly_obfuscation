# Occupancy-preserving residue-state candidate

2026-10-12. Implemented arithmetic model and Wasm generator. Meaning preservation supported by recorded tests; novelty/security not established. This is a new, explicitly specified sample source program, not a claim to have transformed an existing hashing function or arbitrary Wasm.

## Source and transformation

The source accepts12 arbitrary i32 values, u and a loop count. It first computes x_i=(input_i*4 + floor(i/3)) modulo2^32. This operation is part of the original source semantics: the generator does NOT add it to an unrelated program and call that semantics preserving. The source thereby has exactly3 lanes in each residue class mod4 for every input; it does not filter out unfavorable inputs. Upper input bits discarded by source preparation are not protected information.

In every iteration g=(sum(x_i)>>2)&1 and each lane becomes2*x_i²+(1+2g)*x_i+u+2*(x_i&1), modulo2^32. g varies with input and is shared across lanes; the parity term is lane-specific. The exposed outputs are the first3 elementary symmetric sums of all12 final lanes. The Wasm sample uses n&31 rounds, consistently in both forms and the BigInt oracle.

The transformed state has4 triples of coefficients, one per residue, each representing exactly3 values. The residue map is r -> r+u mod4 when g=0, and r -> -r+u mod4 when g=1. Both are permutations. results.json enumerates all8 combinations of g and u mod4. Initial occupancy and congruence preservation then show by induction that no singleton/empty class arises. This removes the concrete singleton-class exposure of residue-state for THIS source class. It is not an automatic eligibility detector for arbitrary source regions.

Wasm updates coefficient triples using the degree3 formulas, routes whole triples through a private two-buffer memory, and computes aggregate outputs by coefficient convolution. No root extraction occurs in transformed iterations. It uses one non-exported64KiB memory page, a real extra resource cost relative to the ordinary sample. Input values are necessarily available during initialization. Non-exported memory is not a security boundary against the stated analyst, who may instrument the binary.

## Validation

experiment.py:1,294 boundary/random cases,18,096 complete coefficient-state comparisons, zero mismatch; both selector values observed; zero occupancy failures. Source states in representative traces are for verification only. Its push/merge dependency is the preserved candidates/residue-state/experiment.py, with SHA-256 recorded in results.json. Source reference uses actual individual values and combinatorial coefficient construction. New formulas have not been checked in a proof assistant.

generate.py: four binary artifacts, normal/quotient raw/O2. WABT1.0.42, Binaryen133 with -O2 --enable-multivalue. SHA-256 and size in manifest.json. O2 sizes860bytes normal,1,140bytes quotient. No runtime-overhead claim yet.

verify.cjs: Node24.15.0 and V8 version recorded.1,318 cases per binary, including extra n=32 and0xffffffff, total5,272 comparisons, zero failure. Calls reuse each instance so private buffers must be reinitialized correctly between calls. The independent BigInt oracle updates individual lanes and calculates outputs with explicit combinations, without using coefficient update formulas. wasm-inputs.json and wasm-observations.json preserve every input/output. Arithmetic model seed1729.

Reproduce: Python3.12.14 experiment.py; Python generate.py; Node verify.cjs. Tools use existing C:/Users/ettotto/Documents/webassembly_obfuscation/.tools. Copy results directory before rerunning. No external libraries installed in this step.

## What remains unproven

The residue partition, symmetric polynomial identities and class-size invariant do not establish novelty. The candidate still needs a direct comparison with known representation/refinement techniques and proof that its specific transformation rules add more than a combination of known machinery. Current generator supports this source template, not general extraction, certification and rewriting of an existing module.

Removing singleton exposure is not equivalent to making recovery hard. Unordered values may be obtained from cubic polynomial coefficients, repeated values may be especially easy, and previous/current buffers can reveal temporal relations. Test these using only coefficient observations and public inputs; do not supply original roots to recovery. Also consider reconstruction of an equivalent computation, which need not recover source labels. Public-API learnability of the simpler prior kernel is preserved as negative evidence, not erased.

Next actions: attempt root/multiset reconstruction with explicit query/work budgets and recorded ambiguities; inspect raw/O2 intermediate values; compare with the no-quotient and simpler symmetric-state variants under matching source semantics; assess applicability beyond this deliberately structured source; only then judge protective value and benchmark costs. No adoption or completion claim.

Goal remains active; stopping threshold25% allowance remaining. CSEC files untouched; no paper, pool, external attack, or security-setting change.
