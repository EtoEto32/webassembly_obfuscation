# Independent update synthesis: feasibility result

2026-10-12. Status: synthesis infrastructure works; **not an adopted novel obfuscation algorithm**.

Unlike encoding-cosynthesis-gate, update coefficients were independent SMT unknowns; no algebraically expanded update coefficients were supplied. Both fixed encoding and joint encoding/update synthesis converged after eight solver calls. Each final model passed a separate Python integer check of all 4,096 states/inputs. Intermediate models and counterexamples are in fixed.json and joint.json.

Fixed case: k=1,l=0. Joint case: k=5,l=8. Basis and branch ordering are specified in protocol.md and source (branch0 even u, branch1 odd u). The extra freedom did not establish any advantage over the fixed control. D remains the explicitly selected quadratic family a+k*b²+l*b. Independently selecting its update does not make this a new representation family or demonstrate resistance to recovery.

Literal unsigned coefficient lifting to i32 failed for both models, including at (a,b,u)=(0,0,0): expected0, observed16. Each lift check ran1,536 boundary/random cases and retained up to16 counterexamples. This rejects that literal lift only; it does not imply no correct i32 coefficients exist. Arithmetic identities over Z/16 need not be identities over Z/(2^32).

No Wasm artifact, performance claim, arbitrary-Wasm transformer, or new-algorithm claim is made from this gate. No CSEC source or existing experiment was edited. Next development must define a genuinely different transformation rule and recovery objective, then synthesize/prove at the intended width. Merely running this same quadratic family at32bits would address correctness but not the novelty deficit.

## Reproduction

Python3.12.14, z3-solver4.13.3.0, SMT random seed1729; lift input seed1729. requirements.txt pins the Windows wheel hash. Dependency lives in C:/Users/ettotto/Documents/webassembly_obfuscation/.tools/encoding-synthesis-python. The script uses that local dependency location when staged under webassembly_obfuscation/tmp; from this independent repository, set WASM_SYNTH_DEPENDENCIES to that absolute directory. Run synthesize.py using the existing runtime-analysis-py312 Python. Outputs overwrite fixed.json and joint.json, so copy the experiment directory before reproduction to preserve these records.

The initial sandboxed launch could not read the installed package directory and raised AttributeError on z3.Solver. The approved elevated local launch succeeded. No protection settings were changed.

This is standard counterexample-guided synthesis, not a novelty result. Previously verified prior-art discussions remain in candidates/encoding-cosynthesis/sources.md. No new literature claim is inferred here.
