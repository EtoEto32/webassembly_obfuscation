# Candidate extension: residue-partitioned polynomial state

2026-10-12. Proposed transformation rules, no implementation/results yet. Intended to move beyond a uniform update selected by a single global predicate, not just raise polynomial degree.

## State and eligibility

For a bounded tuple of i32 lane values, partition by r=x mod2^k (initially k=2). Each class stores its count and the coefficients of the monic product P_r(z)=product(z-x_i) for lanes in that class. The transformed loop holds these coefficients instead of individual values. Boundary initialization sees public input lanes. Only symmetric exits are supported.

Source update can branch on low-k residue. For each class use a polynomial f_r(t,u,E), where E contains permitted global symmetric aggregates. Require a proof that f_r(t,u,E) modulo2^k depends only on r,u,E, not on which representative t in the class was used. Integer polynomials satisfy congruence preservation once coefficients are fixed; predicates depending on high bits need separate proof/representation and are unsupported. No division, float or trap movement is implied.

## Transformation rule

1. Derive the polynomial with roots f_r(x_i,u,E) from the class coefficient tuple. Use division-free integer symmetric reduction separately for each possible class count.
2. Compute destination residue s=f_r(r,u,E) mod2^k.
3. When several source classes route to s, multiply their monic polynomials and add counts. No individual roots are reconstructed. Empty class contributes polynomial1.
4. Combine class polynomials for permitted symmetric output or global aggregate calculations. Loop invariant is equality with the product of the actual source factors in each residue class.

The proof is an induction on iterations using coefficient identities and congruence preservation. Correctness can hold despite additional coefficient collisions over Z/(2^32), since it needs the forward product invariant, not unique factorization. A field-based root uniqueness theorem is therefore not applicable.

Concrete nonlinear, lane-specific branch example:

    f_even(t,u) = t + 2*t*t + u
    f_odd(t,u)  = t + 2*t*t + u + 2

For k=2 both route class r to (r+u) mod4. The branch outcome varies across lanes, but class updates need no per-lane branch during iteration. Class counts rotate; no fake roots may be used for padding unless degree/count logic excludes them. Another polynomial family can produce merges; splitting one class into multiple destinations is ineligible without refining the partition first.

## What is and is not potentially new

Symmetric-polynomial rewriting, polynomial-root transformation, coefficient convolution, quotient representations and residue classification are known mathematical/program-analysis tools. They are NOT claimed new. The potential contribution must be a concrete automatic, certified region transformation that handles these variable-specific branches without representing individual values, and a demonstrated protection benefit at acceptable cost compared with known methods. If this is only established bag representation or symmetry reduction with a different target language, reject the novelty claim.

Protecting arbitrary function I/O or the public low residues is not a goal. Future analyst must receive all binary instructions, public inputs, initialization and full traces; assess structural recovery and an equivalent recurrence without assuming labeled-source-state recovery is necessary. Small coefficient domains or known family can make the recurrence learnable from I/O as the preceding experiment shows. No positive resilience claim until a suitable benchmark and analysis comparison exist.

## Literature checks still needed

Search2026-10-12: polynomial roots multiset mapping resultant polynomial f roots computation; obfuscation resultant polynomial; symmetric data representation multiset polynomial. Primary leads include CGAL's resultant documentation and Mathlib's resultant/root-product identities; search extracts only, not audited code or theorem applicability. Need also inspect compiler bag representation, predicate partitioning, symmetric program abstraction, data refinement and non-injective obfuscation. No claim that absence of an exact search hit proves novelty.

https://doc.cgal.org/latest/Polynomial/classPolynomialTraits__d_1_1Resultant.html
https://teorth.github.io/analysis/docs/Mathlib/RingTheory/Polynomial/Resultant/Basic.html

Next executable milestone: implement class-count-aware transform for <=3 lanes, independently verify varying residues/empty classes, merge and wraparound, then produce actual Wasm. Preserve this simple symmetric-state experiment and its public-API recovery result as baselines. Do not count implementation alone as new research.
