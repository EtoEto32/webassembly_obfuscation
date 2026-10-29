# Three representation proposals: bounded rejection gate

2026-10-12, Asia/Tokyo. **Inconclusive for the invention goal; no candidate adopted.** The goal remains active. The prior turn was progress because it created and reran the SHA comparison substrate. This turn specifies three concrete rules, checks their information/decoding properties, and implements a small Wasm probe for a repaired representation. It does not complete a new obfuscator or claim an improvement over prior obfuscation.

## Fixed scope and resource decision

`protocol.json` was saved before implementation/execution. At most three designs, complete scalar widths 2..8, 4,096 seeded i32 samples plus boundary cases, and 4,096 SHA round tuples. Only the difference-profile representation receives a small Wasm primitive check. Since all three fail their early gates, none receives full SHA integration, performance benchmarking or an enlarged parameter search. This stays within the prior cycle's upper limits; unused implementation budget is not a reason to develop a rejected scheme.

The analyst knows the family and correspondence between physical slots and logical state. It observes the whole encoded state. Decoders receive only that state; expected source values are used by verification, not recovery. This is a deliberately strong, rule-aware negative test, not automated discovery of an unknown representation from a binary. No secret external state, restricted trace observer or unsupported instruction is used as protection.

## R1: rotation selected by a preserved statistic

For an unsigned w-bit word, let h(x)=popcount(x) mod w and E(x)=rotl_w(x,h(x)). Since rotation preserves popcount,

    D(y)=rotr_w(y,popcount(y) mod w)
    D(E(x))=x.

Proposed hiding mechanism: rotation depends on the data rather than a fixed immediate, so a fixed-position bit mapping does not describe the representation. This changes that mapping but leaves a decoder consisting of popcount and rotate. i32 Wasm already supplies both instructions. Replacing T by E∘T∘D would also expose ordinary values during each update; an independently generated encoded update is not supplied here.

508 exhaustive scalar values over widths 2..8 have distinct encodings and correct recovery. Further 4,191 i32 entries (95 boundary values + 4,096 random draws, not all necessarily unique) recover correctly. The decoder uses independent bit-string rotation code. No Wasm candidate or encoded arithmetic transformer was built for R1 because its proposed protection fails directly. A different selector is not automatically a new candidate.

Before: an ordinary word x. Intended After: E(x); intended update E(T(D(y),u)). The absence of that update implementation is explicit. No complete After program or performance result is claimed.

## R2: carry information as a difference profile

Proposed representation of x without its direct value:

    P_j(x)=((x+2^j) mod 2^w) XOR x,  j=0,...,w-1.

Hypothesis: carry-dependent differences spread the word across several nonlinear observations. This initially fails to preserve information. Let H=2^(w-1). Because adding H modulo 2^w toggles only the top bit,

    P_j(x XOR H)=P_j(x) for every j.

Thus x=0 and x=H collide, whereas a legal rotation continuation maps them to 0 and 1. No function of P alone can return that continuation's original word output for both states. This rules out P as a general i32 replacement; it does not rule out a task that never needs the lost bit.

The repair retains an anchor b=bit_(w-1)(x). But for j<w-1, adding 2^j generates a carry into bit j+1 exactly when bit j of x is one. Therefore

    bit_j(x) = bit_(j+1)(P_j(x)),
    x = b*2^(w-1) OR Σ[j=0..w-2] (bit_(j+1)(P_j) * 2^j).

This is a direct O(w) bit extraction, not an expensive search. The last profile word is constant H and carries no information. Hiding the anchor's position would be an additional mechanism requiring its own analysis, not a repair established here.

Complete widths 2..8 yield exactly 2^(w-1) profile classes, each with two words. Every class's collision and distinguishing continuation are in `results.json`. All 4,191 i32 entries also satisfy the collision relation and recover with the anchor. `i32-observations.json` contains inputs, profiles and recovered values.

### Small Wasm implementation and evidence-driven repair

`probe.cjs` generates the ordinary store/load primitive and the repaired profile primitive. The repaired encoder stores P_0..P_31 at offsets 0..127 and b at offset 128. The decoder reads these slots, with no x parameter. Complete WAT, Wasm and O2 output are in `wasm/`.

| Condition | raw bytes | O2 bytes | Checks per binary | Mismatches |
|---|---:|---:|---:|---:|
| Before: store/load x | 81 | 81 | 4,191 | 0 |
| After: profile plus anchor, then recover | 1,066 | 1,056 | 4,191 | 0 |

Four binaries give 16,764 encoding/recovery comparisons. Flipping the anchor after encoding changes the decoded result by exactly H in all 4,191 cases for each repaired binary. These additional mutation checks are not additional independent source inputs. The memory is a deliberately exported snapshot of the representation; the encode boundary takes x, so the whole trace would reveal at least as much. This is not a claim of hiding a public input.

The improvement cycle is: unanchored representation → explicit collision → add one bit to preserve information → direct full recovery still defeats the protection hypothesis. It is a rejected-candidate repair, not the goal's required successful new-algorithm improvement cycle. No performance advantage or resistance metric is claimed. The larger binary is not evidence of protection. Formal all-word reasoning above and finite runtime checks are distinguished; SMT was not run.

The original unanchored rule is implemented in `check.py:profile`, and its failed condition is preserved with collision witnesses; it has no correct decoder or complete transformed program. The repaired After is an actual generated primitive, not a manually presented successful full obfuscator.

## R3: eliminate SHA's shared T1 at the round boundary

For SHA-256's ordinary one-round updates a'=T1+T2 and e'=d+T1 (mod 2^32), define physical A=a' and R=d-T2. Then e'=A+R. Preserve the other six shifted words normally:

    Before state after a round: (a',a,b,c,e',e,f,g)
    Intended After state:      (A, a,b,c,R, e,f,g).

The shared T1 cancels in e'-a'; it is unnecessary to calculate e' explicitly at this cut. However, one addition recovers it. The mapping is the ordinary invertible linear coordinate change (a',e')→(a',e'-a'); the fact that R can be calculated early from d and T2 adds a scheduling difference, not an independent protection principle.

`check.py` compares 4,096 full 32-bit random states, round constants and message words with an independently expressed SHA round (different equivalent Ch/Maj formulas). All eight output words agree after decoding, with zero errors. These are arbitrary one-round inputs, not a full hash or SHA test vectors. `round-observations.json` preserves every input/physical/decoded/expected state. The candidate stops before Wasm and encoded-next-round implementation because its proposed state concealment is directly reversible.

## Prior-art comparison and limits

Primary documents checked on 2026-10-12:

1. D'Anna et al., *Self-Protecting Mobile Agents Obfuscation Report*, NAI #03-015, June 30, 2003, author-hosted [PDF](https://www.multicians.org/thvv/mirror/obfreport.pdf), title page and §3.1 (printed p.18). It explicitly lists value rotation among implemented data representations. The separate search result mentioning §7.1.6 is a different indexed document/version; that section was not found in this final report and is not attributed to it. No author tool executed. This does not establish that its selector equals popcount.
2. Stephen Drape, *Obfuscation of Abstract Data-Types*, Oxford thesis, [PDF](https://www.cs.ox.ac.uk/files/2892/thesis.pdf), §3.2, printed pp.48–49. It supplies abstraction functions, state invariants and a simulation/refinement framework. This is the correctness framework for a valid representation; it does not by itself make every future concrete representation non-novel. Here each particular candidate fails for the explicit reasons above.
3. NIST [FIPS 180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf), §6.2.2. The SHA round identities used in R3 are standard. Their cancellation here is our elementary derivation from those equations, not a quoted new theorem or an attack on SHA's cryptographic security.
4. GMU [ATHENa tutorial v0.6.1](https://cryptography.gmu.edu/athena/download/ATHENa_Tutorial_v0.6.1.pdf), Part 7, PDF p.17. It identifies its `sha256_rs` example with rescheduling attributed to Chaves et al., CHES 2006. No code or circuit experiment run. This confirms an existing rescheduling line, not identity with R3. Direct access to the Chaves paper through CiteSeer failed; exact operation-level comparison to that paper remains unverified.

| Comparison item | R1 | R2 | R3 |
|---|---|---|---|
| Mathematical operation | Input-dependent rotation, explicit inverse | Known addition/XOR differences plus bit extraction | Subtraction of shared round terms |
| Representation | Bijective scalar encoding | Two-to-one without anchor; redundant with anchor | Bijective two-word linear encoding |
| Transition mechanism | Only generic E∘T∘D specified | General encoded updates not defined | Only one-round boundary formula defined |
| Dependency change | Data chooses bit mapping | Carry profile distributes bits but exposes each bit | Shared T1 removed from R, restored by A+R |
| Claimed source of difficulty | Variable bit alignment | Carry dependencies | Round-term cancellation |
| Defeating condition | popcount+rotate decoder | Collision or O(w) decoder | One-add decoder |
| Generalization | Scalar words, no proven protected update | Invalid for general continuations unless repaired | Shared-addend updates, not a general compiler |
| Novelty status | Not supported beyond rotated data encoding | Exact prior match unresolved; rejection does not depend on it | Reduces to existing linear encoding/rescheduling |

Searches included `software obfuscation carry rotation encoding`, `SHA256 rescheduling T1 T2 hardware optimization`, `obfuscation finite differences program`, `software obfuscation graph cover`, `obfuscation divided differences`, `SHA-256 rescheduling Chaves`, `obfuscation carry automaton`, `obfuscation residue mixed radix`, `program obfuscation Newton interpolation`, `software obfuscation matrix factorization`, `Self-Protecting Mobile Agents Hohl pdf rotation obfuscation`, `data encoding finite differences obfuscation`, and `software obfuscation differential encoding`. Unrelated search results and absent exact matches are not novelty evidence. Search metadata crawl dates were not used as publication dates. This is a bounded screen, not a complete literature survey of three accepted algorithms.

## Reuse, reproduction and next decision

Reused WABT 1.0.42, Binaryen 133, Node v24.15.0 and Python 3.12.14. Prior failed representation gates and the previous SHA harness informed the stop conditions; neither previous results nor these counts are combined into a general security score. No old files were changed.

Copy `check.py`, `protocol.json` and `probe.cjs` to a fresh directory; set `WASM_TOOLS_ROOT` to the existing tools directory if outside this repository. Run:

```powershell
python check.py
node probe.cjs
```

Both refuse to overwrite their outputs. Python standard library only, no package installation. Source/binary/input hashes and versions appear in `results.json`, `wasm/results.json` and `inventory.json`. `samples.diff` compares actual generated Before/After, and optimizer diffs preserve what changed at O2.

All §13 success conditions concerning an independent new principle, reusable new transformer, its SHA application, fair superiority evidence and final research package remain unfulfilled. These failed probes do not satisfy them. No global blocker is established: further design work is possible. The next cycle must supply an encoded **update** with an explicit protection argument beyond a self-describing scalar representation or a cancellable linear boundary relation. Do not merely vary popcount selectors, retain more carry-profile slots, or rename the SHA coordinate change.
