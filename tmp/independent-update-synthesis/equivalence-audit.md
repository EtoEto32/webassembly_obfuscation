# Update freedom audit

2026-10-12. Previous turn classified as progress: executable independent synthesis and complete finite-state evidence were saved. This follow-up checks whether its apparent coefficient diversity is a new update mechanism.

## Algebraic restriction

Let arithmetic be modulo2^w, f(b)=k*b²+l*b, D(a,b)=a+f(b), b'=b+1. Correctness requires

    a' + f(b+1) = T(a+f(b),u).

Consequently a' is uniquely determined as a function by subtraction:

    a' = T(a+f(b),u)-f(b+1).

This is an elementary consequence of the specified decode and mask update, not a new theorem of obfuscation. Independent synthesis may choose different expressions implementing that function; it cannot create an independently different state-transition function under these constraints. Semantic equivalence alone does NOT imply equal practical analysis difficulty: different expression forms can matter, but an additional measured benefit is necessary.

For T(x,u)=x²+c*x+u, expanding gives coefficients in basis(1,a,b,a²,ab,b²,ab²,b³,b⁴,u):

    (-k-l,c,-2k+(c-1)l,1,2l,l²+(c-1)k,2k,2kl,k²,1).

audit_equivalence.py independently compares saved synthesized coefficients to these coefficients modulo16. All four branch polynomials differ syntactically, yet their differences evaluate to zero on all4,096 triples each (16,384 checks total, no mismatch). This audit even checks all u for each branch polynomial, not just its parity-selected inputs. Detailed coefficient vectors and deltas are saved in equivalence.json.

Decision: reject this fixed-family co-synthesis instance as a new transformation mechanism. Do not extend it to32bits simply to manufacture more passing results. Preserve the solver as infrastructure. This does not reject all possible synthesis-based obfuscation, different representation relations, or improvements in implementation search.

## Direct related research

Gamez-Montolio, Florit, Brain, Howe, Efficient Normalized Reduction and Generation of Equivalent Multivariate Binary Polynomials, BAR2024, DOI10.14722/bar.2024.23014.
https://www.ndss-symposium.org/wp-content/uploads/bar2024-14-paper.pdf

Read scope: abstract and introduction I.A–I.E, pp1–3; not a full proof audit or author implementation replication. The introduction discusses polynomial encodings and equivalent expressions; the paper studies null polynomials and normalization. Its stated normalization result addresses precisely why unequal coefficient vectors need not represent different functions. Thus coefficient diversity is not a novelty argument here. No claim is made that our code implements its normalizer or that its full tool has been run on these artifacts.

## Next candidate screening

Move from fixed pointwise state representations toward a concrete transformation across loop iterations, where logical state pieces are scheduled at different logical times. Candidate question: can a dependency-preserving temporal schedule prevent the single-boundary state-recovery attacks while preserving exits and nonlinear recurrences, beyond known retiming and loop transformations?

This is only a candidate direction; ordinary retiming is NOT new. Before implementing: inspect retiming/resynthesis-based obfuscation, define explicit finite recurrence transformation and treatment of prologue/epilogue, then reject if it is ordinary loop scheduling with renamed stages. Analyst must observe all lowered intermediate values, and successful recovery can span multiple boundaries. Do not compare only against the old snapshot decoder.

Search log2026-10-12: software obfuscation retiming loop state pipeline temporal encoding; program obfuscation retiming; obfuscation wavefront computation. Relevant primary hit requiring full inspection: https://users.ece.northwestern.edu/~haizhou/publications/host13li.pdf . Search excerpt mentions retiming/resynthesis after state re-encoding; body not yet inspected, so no claim about exact overlap. Searches are not exhaustive novelty proof.
