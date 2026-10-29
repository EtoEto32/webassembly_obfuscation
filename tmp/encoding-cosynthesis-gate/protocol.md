# Finite search gate — recorded before execution

This is an executable screening prototype for the design in encoding-cosynthesis, not the full joint synthesizer and not a novel obfuscator. Search 256 existing polynomial split encodings D(a,b)=a+f(b), where f has degree<=3 and four coefficients in 0..3. The update is algebraically derived, NOT independently synthesized. Distinguish that limitation in all reports.

Source transition: x'=x*x+c*x+u modulo 2^w, c=3 for odd u and 5 otherwise. Mask b'=b+1. Derive a' by polynomial expansion of (a+f(b))^2+c*(a+f(b))+u-f(b+1). No runtime call to D in the expanded update. At w=4 exhaust every a,b,u for correctness. Correctness verification uses independent BigInt arithmetic and Horner evaluation.

Search uses a complete finite grammar of decoders a+g(b), deg(g)<=2, coefficients 0..15. Recovery success excludes all candidate encodings with the same complete 16-point f signature, not just the syntactic instance. Candidate coefficients are enumerated in fixed base4 order. Separately evaluate every survivor with held-out degree<=3 decoder grammar, coefficients0..15, also exhaustively enumerated. This stronger observer is defined before running; it is not evidence of arbitrary deobfuscation.

Generate raw/O2 i32 Wasm for the first weak-grammar survivor: plain, decode-operate-encode baseline, expanded update. Export init/step/decode for correctness only. Use WABT and Binaryen. Test boundary/random states and inputs using independent BigInt; algebraic derivation and finite tests are distinct. Semantic state at the external decode boundary is deliberately public. A later real attack evaluation must instrument intermediate instructions and omit verifier-only helpers; this gate does not satisfy that requirement.

Reject adopting this search instantiation if survivors are recovered by the held-out grammar. Do not substitute degree growth, polynomial splitting, or generic feedback search for a newly established algorithm. Save enumerated candidates, equivalence-class blocks, all recovery outcomes, polynomial updates, Wasm/WAT, hashes and mismatch counts. No performance or security claim from this gate.
