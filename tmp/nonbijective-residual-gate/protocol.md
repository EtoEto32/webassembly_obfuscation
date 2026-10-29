# Non-bijective residual map: candidate gate

2026-10-12. Goal remains novel Wasm obfuscation; this is an arithmetic feasibility/attack gate, not a completed transformer.

For outputs f,g let a=z-f and b=t-g modulo 2^w. Replace a=b=0 by Q(a,b)=0 where Q=(a+a(a+1)b, b+b(b+1)a). Q is not a permutation for w>=2: (1,0) and (1,2^(w-1)) collide. It still has exactly one zero. Modulo 2 its values equal (a,b), so a zero has even a,b; then factors 1+(a+1)b and 1+(b+1)a are odd and invertible, forcing a=b=0. This is an algebraic argument, not a security proof.

Compared with implicit-equation-gate, there is no global Q inverse. However zero-set simplification may remove it. Test residual pairs exhaustively at widths 1..8 and the collision witness at widths 2..32. Then provide an independent factorization observer only fully expanded output equations (integer coefficient dictionaries), input/output variable names and width. Do not pass f,g or a,b. Try integer factorization after signed modular coefficient normalization. Compare small and large coefficients rather than selecting the favorable group. This attack is limited to integer factorization, not general modular decomposition.

No novelty claim follows from a failed factorization. If the layer is immediately removed for the concrete generated condition, reject that condition. Preserve unresolved modular cases separately. All examples are pure polynomial computations; branches, traps, Wasm lowering and performance evaluation remain unimplemented.
