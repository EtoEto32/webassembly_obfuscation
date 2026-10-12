# Residue-partitioned coefficient-state prototype

2026-10-12. Implemented arithmetic prototype; no Wasm artifact yet, no novel-algorithm/adoption claim. Previous turn was progress: public-API recovery experiment and concrete residue routing design saved.

## Implemented rules

Four classes for x mod4, at most3 values total. Each stores(count,e1,e2,e3), with unused coefficients zero. push() computes coefficients of a*t²+b*t+d from class coefficients without extracting roots. merge() convolves elementary coefficients; counts are essential to avoid treating padded zeros as extra roots. Integer formulas are then reduced modulo2^w. Code raises an error if merged capacity exceeds3.

Two source kernels were implemented, not substituted for a real hash:

- permute: t'=2t²+(1+2*(global_sum mod2))*t+u+2*(t mod2). This includes global-state dependence and lane-specific parity branches. Residue routing is a permutation, independently checked in executions.
- merge: t'=t²+(1+2*(t mod2))*t+u+2*(t mod2). Distinct occupied source classes can merge.

Initialization explicitly processes public input values. Iterations receive only coefficient groups. The independent reference updates actual lane values using branch statements, then recomputes coefficient products. This compares complete class state each iteration, not merely a final aggregate. Reference/initial encoding shares one coefficient-construction function; it does not use push/merge algebra. Full integer symbolic identity proofs for the new degree3 formulas are still pending; finite tests are not reported as such proofs.

## Executed results

Python3.12.14, standard library only. Run experiment.py; creates results.json, inputs32.json and samples.json. Random seed1729. Existing results should be copied before reproduction. All4bit triples and u values:65,536 one-step cases per kernel.32bit:4,669 boundary/random cases per kernel with0,1,2,3,15,31 iterations cycled over the input list;40,456 transitions each. Total211,984 class-state comparisons, zero failures. Counts0..3 all observed. Merge kernel exercised36,864 source-class merges at4bit and2,215 at32bit. These counts are event totals, not independent attack samples.

All32bit inputs are saved. Small-width inputs are completely specified by lexicographic product(range(16),repeat=4). Representative traces are saved; hashes of deterministic full trace streams are recorded for reproduction. These hashes do not replace raw failure evidence; no failures occurred in the recorded run.

## Structural exposure that prevents adoption

For a singleton class P(z)=z-x, e1=x. The prototype explicitly carries that value.32bit runs observed64,552 singleton class occurrences for permute and28,000 for merge. Thus the previous informal aspiration 'no individual values in transformed state' is false for this implementation. There is no need to claim a sophisticated attack: reading e1 of a class whose count is1 suffices. This is a mathematical property of the representation, not an inference from unusual test data.

No positive resistance claim or runtime benchmark follows from correct outputs. Increasing minimum occupancy would restrict applicability and cannot be done by cherry-picking favorable inputs. Any guarded fallback would need to report coverage and the unprotected cases. Padding with public dummy roots is insufficient by itself, because known linear factors can be removed. Wider groups also require root/set recovery analysis rather than claiming irreversibility solely from loss of labels.

Status: the current <=3-lane implementation is not adopted as a protective algorithm. Preserve it as a concrete branch-aware state-transform prototype. Next design must either remove singleton exposure by a substantive representation rule or explicitly justify a narrower protected region with useful practical coverage. Known affine mixing of these coefficients alone is not a new mechanism. Existing-Wasm transformation, all-constraint proof, fair security/performance comparisons and novelty determination remain incomplete.

## Primary-source check

CGAL6.2.1 resultant concept documentation, definition section read2026-10-12, describes the Sylvester determinant over a commutative ring. The prototype uses explicit symmetric coefficient formulas, not CGAL's code. Its root-factor prose is not used as a theorem over Z/(2^32); in particular, the page's displayed nonzero/common-factor wording is not relied on.
https://doc.cgal.org/latest/Polynomial/classPolynomialTraits__d_1_1Resultant.html

Hubert and Labahn, Computation of Invariants of Finite Abelian Groups, author PDF datedApril29,2015. Abstract, introduction and beginning of2.1 read. It concerns rational invariants and reduction in a nonmodular finite-abelian-group setting; it is relevant background, not an exact modular software transformation comparison. Remaining sections/implementation not audited here. This narrows the earlier search-only record without assuming that a field result applies unchanged to our ring.
https://cs.uwaterloo.ca/~glabahn/Papers/MathCompV2.pdf

CSEC files untouched. No attacks, mining, external execution or security-setting changes. Goal still active and latest user stopping threshold remains25% allowance remaining.
