# Common-step execution: expressiveness and iteration-cost gate

2026-10-12. **Inconclusive; the invention goal is active and unmet.** A bounded exploration of replacing different operations by repetitions of the same autonomous state update. Neither variant is adopted as a new obfuscation algorithm. This record supplies concrete feasibility evidence rather than another working Wasm obfuscator.

## Exact candidate and relation to earlier work

Let S have N=2^w states. A fixed shared bijection E represents the source word throughout the program. One total map U:S->S updates the encoded data state. Operation T_i is implemented by

    Before: x <- T_i(x)
    After:  z <- U^tau_i(z); z initially equals E(x)

The required result is E(T_i(x)). The encoding is not changed per instruction, U receives no opcode or auxiliary operand, and its data carrier has exactly N states. A counter and operation-specific stopping rule may control how often U runs, but cannot affect an individual U transition. Thus this is a restriction on the data transition, not a claim that an implementation needs literally no loop counter. There is no additional encoded scratch state, history or reset between operations.

Variant A uses a constant count per operation. Variant B allows a count depending on the operation and starting data state. The concrete target operations are A(x)=x+1 mod N and X(x)=x XOR 1. A general integer transformation should be able to express these basic operations; this test does not assume that the exact pair appears together in every SHA implementation.

The intended protection was to remove distinguishable arithmetic handlers by making the local update identical. An analyst is allowed the full implementation, inputs and arbitrary execution traces. No limitation on observing iteration counts is assumed. Representation and cost must be valid before that protection hypothesis warrants an attack experiment.

Earlier `../../tmp/shared-transition-gate` considered one update under separate boundary bijections; `../../tmp/overlapping-transition-gate` considered fixed overlapping representations. This experiment tests their explicitly untested variable-duration alternative under a shared, persistent encoding. Those records are reused as design references (C), not added to the new counts. The available Python3.12.14 runtime is reused (A); no new dependencies. CSEC and prior experiments remain unchanged.

## Variant A: fixed repetition counts

All fixed powers of a single map commute, including noninvertible maps and zero repetitions:

    U^a U^b = U^(a+b) = U^b U^a.

Conjugating by the same E preserves commutativity. But for w>=2, A(X(0))=2 and X(A(0))=0. Thus no such common U and counts implement both operations. This is an elementary algebraic obstruction, not a newly claimed theorem about all virtualization.

`check.py` enumerates all 256 maps on four states, computes each entire power sequence until repetition, and then classifies all 65,536 ordered pairs of maps. It finds 2,824 commuting pairs, of which 1,296 share a power generator. For each represented pair, direct repeated application checks its saved witness. The gap also verifies that commutation alone is not sufficient. An example of commuting maps with no common generator is retained in `results.json`. A+1 and A+2 provide a successful fixed-count control.

## Variant B: state-dependent stopping

This repair removes the commutation obstruction. Given a full directed cycle U and its position map p, **any** finite map T is represented by

    tau_T(x) = (p(E(T(x))) - p(E(x))) mod N.

This formula is an existence construction, not an efficient novel compiler: finding the target or storing this table can carry the original operation's semantics. It must be counted as part of a real transformation.

There is also a stronger cost obstruction for the stated pair:

1. Realizing A requires that each encoded x can reach the encoded x+1 through U. Concatenating these paths shows every state can reach every other state.
2. A finite strongly connected functional graph is one full directed cycle. Hence allowing U initially to be any total map does not escape the cycle constraint.
3. X is a fixed-point-free involution. For each pair {x,X(x)}, the two minimum forward distances along a full cycle sum to N. There are N/2 pairs.
4. Therefore the mean **minimum** number of U applications for X, over uniform x, is N/2. Any additional revolutions only increase the mean. This is invariant under E and cycle choice.

For w=32 this yields a lower bound of 2^31=2,147,483,648 applications per XOR 1 on average under uniform inputs. This is an analytic count of U transitions, **not a measured runtime, hardware-instruction count, or tested 32-bit enumeration**. If a shortcut computes U^t directly, it changes the stipulated repeated-step evaluator; its implementation, semantics and protection would need separate analysis. Nonuniform reachable-state restrictions also require a different statement.

## Executed finite checks and improvement result

`protocol.json` was written before implementation/execution: two variants of one design, 40-minute cycle cap, 60-second command bound, no random search, host-default memory. Early failures rule out Wasm/SHA expansion in this cycle.

Every labeled full directed cycle was enumerated for N=2,4,8, with rotation removed by placing label 0 first. Reversal is not identified. Counts were generated from positions, while correctness was checked by walking U one step at a time.

| N | Cycles checked | Mean minimum XOR steps in every cycle | Best joint worst-case steps for A and X |
|---:|---:|---:|---:|
| 2 | 1 | 1 | 1 |
| 4 | 6 | 2 | 3 |
| 8 | 5,040 | 4 | 4 |

The 5,047 cycles yield 80,692 source-transition checks, all matching. Separately, every one of the 256 source maps on four states was implemented through each of the six full cycles: 6,144 further transition checks, all matching. These are finite table checks, not independent obfuscation algorithms or attack trials. A visited-state reachability check over all 256 U maps confirms that exactly the six full cycles can reach x+1 from every x.

The N=2 control legitimately escapes Variant A's obstruction because add-one and XOR-one are the same operation. The N=8 best cycle makes XOR-one take exactly four steps, demonstrating that the average bound can be attained uniformly in this finite case. No optimality claim for joint worst-case cost at arbitrary widths is made.

The improvement from A to B succeeds in expressiveness but incurs an exponential transition count for the unrestricted word-size model. It is rejected on that explicit cost condition; no empirical timing ratio or unimplemented attack is used to justify rejection.

## Prior comparison and limits

Search/read date 2026-10-12. Queries: `obfuscation instruction iteration repeated single instruction interpreter movfuscator`; `Tigress virtualize instruction handlers superoperators official`; `functional graph iterate maps common iterative root commuting functions finite set`.

- [M/o/Vfuscator author repository](https://github.com/xoreaxeaxeax/movfuscator), README Overview, flags and build description inspected. It compiles C using MOV operations. This establishes existing single-instruction compilation, but using one mnemonic with different operands and memory is not the same as iterating one autonomous map on a single word. No author code was built or executed; no resistance result is borrowed.
- [Tigress official Virtualize documentation](https://tigress.wtf/virtualize.html), instruction-handler examples, superoperators and reentrant interpreter discussion inspected. It already supports merged instruction semantics and varied interpreter organization. The examples use virtual registers, stack and instruction stream. These exceed this gate's state restriction; our lower bound does not apply to them.
- [An Analysis of x86 Single-Instruction Compiling as an Obfuscation Technique](https://www2.compute.dtu.dk/pubdb/edoc/imm7053.pdf), §6.6.1–6.6.3 inspected via primary university-hosted text. The analysis describes ALU communication variables and memory lookup operations. This supports the difference in computational model, not an independent execution of the analyzed compiler. Other search hits on commuting functions were leads only; the algebraic arguments above are stated directly.

| Required comparison | Candidate | Assessment |
|---|---|---|
| Mathematical rule | Replace T by U^tau under one shared encoding | Concrete iteration rule; no independent new protection principle established |
| Representation | Same-size word state; instruction meaning partly moved to stopping | More restricted than ordinary interpreters |
| State update | Identical autonomous U | Fixed counts lose expressiveness; variable counts incur stated bound |
| Dependencies | Opcode influences stopping only | Count construction must still encode instruction semantics |
| Difficulty mechanism | Local instruction identity removed | No demonstrated analysis-resistance advantage |
| Generalization | Exactly the stipulated finite-state model | Not a theorem about all one-instruction, stateful or multiword virtualization |

The distinct restriction is not itself useful novelty. These sources do not establish an exact prior implementation of the candidate, and search absence does not establish novelty. No broad impossibility or blanket overlap claim is made for alternative state carriers.

## Artifacts, reproduction and completion audit

`check.py` is the executable finite-model implementation. `results.json` retains counts, counterexamples, source/protocol hashes and construction witnesses. `cycles-2.json`, `cycles-4.json`, `cycles-8.json` retain every enumerated cycle and its count arrays. `sample.json` contains the actual generated N=8 Before tables, common U, After count tables and execution pseudocode, all checked by the runner. `sample.diff` compares these generated representations. These are not WAT samples because no Wasm backend was built after failure at the initial gate.

Python3.12.14 standard library; deterministic enumeration. Copy this directory without `results.json` and run:

```powershell
python check.py
```

It refuses to overwrite an existing result. `inventory.json` fixes hashes of delivered files. No SMT proof, compiler/optimizer test, SHA application, runtime/size benchmark, or fair proposal-versus-existing-method attack comparison was executed here.

All goal §13 requirements remain unmet for an adopted new algorithm: independent principle and specification; reusable Wasm transformer; SHA application and correctness; fair comparison and superiority; proposal performance/size/optimizer resilience; successful improvement; reproducible adopted-method package and generated examples. This directory records a failed candidate and a failed cost repair only. The remaining research gap is a useful distinct transformation, not more repetitions or relabelings of this construction.

A successor would have to change the state/update rules and establish a concrete advantage over existing interpreters. Merely adding an opcode register, instruction stream or generic scratch memory escapes the mathematical premise but recreates familiar virtualization; that escape alone is not grounds for adoption.
