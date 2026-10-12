# Observer audit and supervised quadratic recovery

2026-10-12. Progress: a concrete comparison gate for candidate selection, not a newly invented obfuscation algorithm or attack.

## Primary implementation inspected

Local-Mixing/local_mixing, fixed commit **5ce6daab669f50665f0c9aecf958f4066f407d01**.

- https://github.com/Local-Mixing/local_mixing/blob/5ce6daab669f50665f0c9aecf958f4066f407d01/security_tests/README.md : read prefix, affine/statistical, cumulative trace, gauntlet, and demixing descriptions.
- security_tests/gauntlet/gauntlet.py: downloaded, inspected function index and relevant argument/report plumbing, not fully read or executed.
- nonlinear193.py and nonlinear291.py: reused the hash-verified files from ../local-mixing-source-audit. Read the run_gate initialization, output contract and Circuit gate semantics before implementing the diagnostic.

Upstream already documents affine state recovery, degree-two feature expansion, cumulative gate-delta traces, direct matches, weight-one/two/three correlations, and feature-budget skips. Its embedded-masking gauntlet uses off-trace logical encoding/decoding and randomized bands, unlike its full TDP generator's slice contract. Thus neither degree-two recovery nor the distinction between trace and snapshot observers is a new contribution here. We did not execute the Rust gauntlet, mixer or complete TDP pipeline.

## Question and observation contract

Does a canonical **unmixed, single nonlinear291 r57 gadget** resist the tested affine feature family while remaining recoverable using quadratic features?

The supervised fitter receives arrays of numbered physical observations and the desired logical target values for training. It receives no encoding-to-wire mapping. This is stronger assistance than a blind attack: those target labels come from the reference generator. It is a representation diagnostic, not reconstruction of unknown source code. The public source and input initialization are available for independent verification. Targets a, b and c_in are logical gate inputs; gate_ab is the update; c_out is the logical output and is not itself a secret.

Feature families:

1. Plain positive control: logical a, b, c_in and c_out, plus constant one. The gate update is c_in XOR c_out.
2. Encoded final state: all 71 physical values, plus one, affine combinations only.
3. Encoded complete trace: 71 initial values plus all 291 gate-flip values and one, affine combinations only. Every intermediate wire value is a linear combination of these observations, so this is not a downsampled trace.
4. Encoded final state with all distinct pairwise AND products: 2,557 features, including one and the 71 values. Squares add nothing for Boolean variables.

Exact GF(2) elimination fits on **4,096** samples. Witnesses are frozen before evaluating **8,192** held-out samples per seed. Seeds 71 and 193 change input samples, not the circuit construction: the gate tapes are identical. There is only one protected gadget construction. Independent random labels are a negative control, not another protected secret. The complete arrays, learned expressions and ranks are saved.

## Results

Both input seeds gave the same pattern for all five logical targets:

| Condition | Training fit | Held-out errors per target |
|---|---|---|
| Plain affine | yes | 0 / 8,192 |
| Encoded final affine | no exact fit | not applicable |
| Encoded full-trace affine | no exact fit | not applicable |
| Encoded final quadratic | yes | 0 / 8,192 |

The quadratic feature matrix has rank 859. Independent noise has no exact training fit in every condition. Non-fit is a statement about the supplied finite training vectors and feature family, not resistance to unrestricted analysis. Fit times in results.json are single-run diagnostics, not comparative performance measurements.

The five learned quadratic witnesses from each run were independently replayed using Boolean polynomials represented as sets of monomials. The verifier translates the **emitted gate tape**, uses XOR as symmetric difference and multiplication with x*x=x, and compares each witness with the logical formula from the input representation. All ten differences are exactly zero. This establishes these witnesses for all **2^39** valid initial assignments of this canonical gadget with its specified 32 zero scratch wires; it does not enumerate them. Both runs' witnesses are duplicates in mathematical content, not ten different protected constructions.

The proof explicitly fixes clean wires 35..39 and 44..70. Free wires are 0..34 and 40..43. It does not infer cleanliness from sampled zeroes. It makes no claim for dirty-scratch variants, mixed circuits, alternate gadgets or Wasm JIT code.

## Implications for our new algorithm search

- A candidate that merely avoids exact intermediate matches or affine recovery has not demonstrated strong protection. The canonical reference supplies a concrete example.
- These results do **not** establish a previously unknown flaw in the original research. Upstream already includes quadratic-feature diagnostics, and we evaluated a component before mixing.
- Increasing polynomial degree alone is not a new algorithm and incurs an unmeasured cost. Do not declare a superior candidate by disabling quadratic features or withholding trace values.
- Any new rule must be compared against the same target/label access, snapshots and full trace, with positive controls and held-out tests. If training labels are unavailable in a claimed real attacker model, report the supervised diagnostic separately from blind reconstruction.
- Novelty still requires a concrete transform rule beyond the existing masking, encoded gate decomposition and mixing. No candidate is adopted by this experiment. The current goal remains incomplete.

## Reproduction

Python 3.12.14; NumPy 2.5.3. Keep sibling directory ../local-mixing-source-audit intact. In a fresh copy without results.json:

    C:/Users/ettotto/Documents/webassembly_obfuscation/.tools/runtime-analysis-py312/Scripts/python.exe probe.py
    C:/Users/ettotto/Documents/webassembly_obfuscation/.tools/runtime-analysis-py312/Scripts/python.exe verify_witnesses.py

probe.py verifies upstream module SHA-256 before loading. It refuses to overwrite existing results.json. verify_witnesses.py regenerates the symbolic proof and gate tape. Saved files include results.json, two observations-*.npz archives, gate-tape.json and proofs.json. No network, mining, AV changes or CSEC edits were performed.
