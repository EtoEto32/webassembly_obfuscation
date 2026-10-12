# Phase-dependent representations under one autonomous update

## 1. State

2026-10-12. **Inconclusive; invention goal active and unmet.** No new obfuscation algorithm adopted. A concrete extension of the common-update proposal has been defined, implemented as finite tables and screened. Its intended general transformation fails for a simple two-operation period; the redundant repair recreates an explicit clock.

## 2. Completed

Derived a necessary and sufficient feasibility condition, implemented constructive witnesses and checked them against independent enumeration. All 576 ordered pairs of permutations on four states were classified; 288 were feasible. A noncommuting feasible pair is saved, so the earlier fixed-encoding commutation obstruction is correctly not applied to this relaxed design.

## 3. Unmet

No independently novel useful rule, reusable new Wasm transformer, complete SHA application, fair attack advantage, performance evaluation or optimizer evidence. These finite tables do not satisfy those goal requirements. No environment blocker has been established.

## 4. Exact candidate and proof

The source repeatedly performs T0 followed by T1 on the finite data space S. Both operations are bijective. Seek bijections E0,E1:S->S and one autonomous total U:S->S such that

```text
U E0 = E1 T0
U E1 = E0 T1
```

The first and second physical steps use exactly the same U. U receives no opcode, phase or additional scratch state. The intermediate representation may change, but after two steps the representation must return to E0. All source states, not merely a particular trajectory, must satisfy the equations. Representations and decoding are part of the proposed program, not assumed free in any eventual cost claim.

Combining the equations gives U² E0 = E0 (T1 T0). Thus V=E0^-1 U E0 must satisfy V²=P, where P=T1 T0. Since P is a permutation, any total V with V²=P is itself bijective. Conversely, if V²=P, take E0=id, U=V, E1=V T0^-1. Then both equations hold. Consequently the design exists exactly when P has a permutation square root. Choosing a different E0 cannot change existence.

An elementary known cycle criterion decides this: each even cycle length must occur an even number of times. Squaring an even-length cycle splits it into two equal-length cycles; squaring an odd-length cycle preserves its length. For construction, pair equal even cycles and interleave them, while an odd cycle of length n takes stride (n+1)/2. This is established permutation theory, not a newly claimed theorem or cryptographic primitive.

### Concrete obstruction for ordinary word operations

Let N=2^w, T0=A(x)=x+1 mod N, T1=X(x)=x XOR 1. P=X A fixes all even states and sends each odd x to x+2 mod N. Hence it consists of N/2 fixed points and one cycle of length N/2. For every w>=2 the latter is even and appears once, so P has no square root. The proposed same-size autonomous update cannot implement this two-operation period, even allowing a different representation at the halfway boundary. This analytic argument includes w=32; the script only enumerates widths 1..8.

This is not an impossibility result for arbitrary obfuscation, arbitrary SHA implementations, larger carriers, variable step counts, restricted reachable states or nonperiodic boundary representations. It also does not say every noncommuting pair fails: the saved positive control disproves that extrapolation.

### Repair with a doubled carrier

Let Z=S×{0,1}. Define

```text
U(x,0) = (x,1)
U(x,1) = (P(x),0)
E0(x)  = (x,0)
E1(y)  = (T0^-1(y),1)
```

Both simulation equations now hold for every bijective T0,T1. But the repair carries an explicit phase bit, and its second branch performs P. The halfway decoder performs T0. Computation has been moved across phase boundaries, not protected by a new mechanism. Packing or permuting this bit is an additional encoding, not an independent justification for adoption. No general lower bound on the smallest possible redundant carrier is claimed.

## 5. Prior work and comparison

Searches on 2026-10-12: `"obfuscation" "iterative root"`; `"permutation" "square root" "cycles" theorem`; `"software obfuscation" "autonomous" state`.

Primary mathematical source: Herbert S. Wilf, *generatingfunctionology*, 1994 Internet edition, [university-hosted text](https://www.math.cmu.edu/~af1p/Teaching/Combinatorics/Slides/Notes/gfology.pdf), §4.8, printed pp.146–147, Theorem 4.8.1 and its construction. This supplies the standard cycle criterion and algorithm used here. The original UPenn URL returned 403; an EJC mirror lead returned 404. Neither failed fetch is treated as a read source. No absence-of-prior-art claim follows from search results.

Earlier local source audits document LOKI semantic selection and Tigress VM handlers: `../../tmp/control-fusion-source-audit/README.md` and `../../tmp/shared-transition-gate/README.md`. They are reused as prior-art context, not fresh author-code execution. Generic shared handlers or an explicit phase selector are not new principles.

| Comparison | Current rule | Assessment |
| --- | --- | --- |
| Mathematical principle | Square root of a two-step composition | Established finite-permutation construction |
| Representation | Two bijections with periodic boundary closure | Different from one fixed E in common-iteration-gate |
| Transition | Same autonomous U at both phases | Exists only under the stated root condition |
| Dependencies | Operator sequence moved into U and boundary maps | Boundary costs and intermediate decoding cannot be ignored |
| Protection | Intended removal of explicit phase argument | Not established; broad target fails, doubled repair restores phase |
| Generalization | Bijective two-operation periods | Not a compiler for arbitrary Wasm |

## 6. Reuse

Python 3.12.14 runtime: A, usable for this standard-library enumeration. Earlier common-iteration, shared-transition and overlapping-transition gates: C, reference designs and counterexamples. No past experiment counts are included in the new totals. Existing SHA and corpus artifacts remain untouched.

## 7. Executed verification

`protocol.json` was saved before execution. `check.py` directly squares each of the 24 permutations on four states to form an independent existence oracle; the oracle does not use cycle parity. It finds 12 distinct squares. Constructive cycle-based roots agree with that oracle on all 24 permutations. Across 576 ordered source pairs, 288 admit roots; generated E1/U mappings pass 2,304 phase-transition checks. Identity is accepted and a single transposition is rejected.

For A/X, widths 1..8 match the analytic result: width1 admits a root, widths2..8 do not. The doubled repair passes 1,020 phase-transition checks over those widths. A separate assertion checks each two-step composition, but is not added again to the headline count. No SMT or Wasm runtime was used. Tables are exhaustive only over the declared finite scopes.

## 8. Attack comparison

This is a feasibility gate, not a measured attack. No deobfuscation success rate, superiority over MBA, PUSHAN experiment or SHA recovery claim is made. Whole-program visibility and observation of any phase/counter remain allowed in the intended threat model; the repair's explicit phase is not hidden by assumption.

## 9. Costs and optimizer

The model repair doubles the number of carrier states, but this is not a measured runtime/memory overhead for Wasm. No table enumeration at 32 bits occurred. Root existence at small widths does not yield a compact efficient implementation at word width. Performance, size and optimizer experiments are not warranted for the rejected broad design.

## 10. Improvement cycle

Original constraint: one representation throughout shared-step execution. Change: allow an intermediate phase-specific bijection and require only periodic boundary closure. Result: some noncommuting pairs become feasible, but A/X fails by cycle parity. Second change: double the carrier. Result: correctness restored, explicit clock and original computation reintroduced. Neither revision establishes novel protection. Do not repeat the experiment with more permutations or relabeling seeds as a substitute for a new rule.

## 11. Generated Before/After

`artifacts/sample.json` is an actual generated noncommuting positive control: T0/T1 are Before tables, U/E1/D1 are After tables and intermediate decoder. `pairs.json` stores every classified pair and every constructed witness. `results.json:target` stores the A/X obstruction cycles and actual repaired U/E0/E1 tables. The repair packs (x,h) as 2*x+h; that convention is explicit. These are executable finite IR tables checked by the runner, not WAT or complete transformed SHA programs.

## 12. Reproduction and evidence

From repository root, choose a nonexistent output directory:

```powershell
.\.tools\runtime-analysis-py312\Scripts\python.exe experiments/phase-root-gate/check.py experiments/phase-root-gate/reproduction
```

No dependencies, random inputs or seeds. `artifacts/results.json` records Python version, source/protocol hashes, counts, counterexample structure and repair tables. The command completed with exit code0 in under one second; that elapsed observation is not an execution-performance benchmark. Existing output directories are refused.

## 13. Limits and research consequence

This finishes a previously untested relaxation, not the requested invention. General coupled control/data updates remain open, but must escape the specific assumptions for a stated reason and supply a useful concrete rule. Phase-specific arbitrary encodings or an explicit extra mode bit alone do not establish independence or resistance. The original full success conditions remain unchanged and unmet.
