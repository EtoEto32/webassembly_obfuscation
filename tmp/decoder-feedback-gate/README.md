# Decoder-feedback generalization gate

2026-10-12. **Not an adopted obfuscation algorithm.** This experiment implements a previously missing pruning rule in a finite model and exposes its limits. It is neither an arbitrary-Wasm transformer nor a reproduction of an author's tool.

Follow-up: [independent structural review](structural-review.md) shows that the first operation already forces either one-operation recovery or information loss at every word width. Increasing downstream depth cannot change that conclusion under the recorded observation model.

## Exact problem and rule

Words are 3-bit unsigned integers; all operations wrap modulo 8. Grammar choices theta=(op0,op1,op2) independently select add, sub, xor, mul, and, or:

```
u = op0(a,b)
v = op1(u,b)
w = op2(u,v)
observation = (u,v,w,b)
```

There are 216 syntax choices and 64 input pairs. The decoder grammar has four projections and 96 binary expressions over the four observations. Its target is a. This deliberately finite observation model concerns a checkpoint representation only: it excludes the incoming a value but includes all three generated values and b. It does not model a whole trace or claim to hide a public input. No update semantics are synthesized.

For a fixed decoder d, define R_d(theta) as equality d(observation(theta,a,b))=a for **all** 64 inputs. Starting from a recovered theta, greedily wildcard each grammar coordinate, retaining the wildcard only when R_d holds for **every completion** of that partial assignment. A resulting cube C therefore satisfies:

```
forall theta in C: forall a,b: d(observation(theta,a,b)) = a
```

This supplies a sufficient reason to reject all C for an objective forbidding recovery by d. Correctness of the represented computation is a separate condition. The rule is exact only over this finite grammar/domain. It is ordinary finite implicant generalization, not a claimed invention. Greedy cubes are not claimed globally minimal. Enumeration and full truth tables are an oracle implementation, not a scalable synthesis engine.

## Results from check.py

- 108 of 216 candidates are recovered by at least one of the 100 decoders.
- Four learned cubes remove exactly those 108 candidates. The cubes cover 114 candidate occurrences because some overlap.
- A separate operation evaluator checks all covered candidates on all inputs: 7,296 candidate/input checks, zero failures. This is independent evaluation code, not independent authorship or a formal proof of the implementation.
- All remaining 108 candidates have an observation collision between distinct a values with the same b. The stored collision witnesses show that these are information-losing representations, not successful protection.
- No valid unrecovered candidate was found in this grammar. It is rejected as a source of a new encoding. This does not rule out larger grammars.

The deliberately sample-only variant checks a=0 with all b when generalizing a **genuinely** recovered seed. Seed (add,sub,or), decoder v AND w, leads to the invalid cube (add,sub,*). Completion (add,sub,add) fails at a=1,b=0: expected 1, decoded 0. That completion can still be recovered by another decoder; the counterexample disproves the fixed-decoder certificate, not the assertion that this particular completion is secure or useful.

All candidate lists, learned cubes, decoder witnesses, one sample-only counterexample and survivor collisions are in results.json. No runtime overhead or decoder-search speedup is claimed. Counting four cubes instead of 108 candidates ignores the exhaustive work required to construct them.

## Closest synthesis prior art

Feng, Martins, Bastani, Dillig, **Program Synthesis using Conflict-Driven Learning**, PLDI 2018. Primary author PDF: https://trustml.github.io/docs/pldi18b.pdf ; preprint https://arxiv.org/abs/1711.08029 (2017). Inspected introduction, section 5 Definition 5.1, Theorem 5.2, Algorithm 5 and Theorem 5.4 via searchable PDF. Neo generalizes conflicts over DSL components using specifications and unsatisfiable cores. We did not run Neo, inspect its implementation, or claim that our exhaustive cube checker implements its algorithm. Generalizing a failed candidate to rule out many candidates is already established; changing the specification to decoder resistance does not by itself establish novelty.

The prior distorted-interpreter-audit covers analysis-guided obfuscation. Together, these sources prevent claiming the surrounding generic search framework as a new algorithm. The original goal permits either an independently new useful transformation/update rule or an independently new transformation-generation principle. This generic pruning component establishes neither; that is not a rejection of all possible generation principles.

## Reproduction and next step

Python 3.12.14, standard library only, deterministic complete enumeration, no random seed. Run check.py in a copy of this directory; it replaces results.json in that copy. No external service, mining, Wasm binary, or CSEC modification is involved.

Next: use a representation grammar whose invertibility is established independently, and define an update-rule change beyond the already rejected polynomial parameter families. A candidate must preserve information and program behavior before surviving a restricted decoder can be interpreted as evidence. The pruning checker is available for future experiments, but its operation does not meet the goal's algorithm-novelty requirement. Overall goal active and unmet.
