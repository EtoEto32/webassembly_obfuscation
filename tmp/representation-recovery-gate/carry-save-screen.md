# Carry-save proposal screen

2026-10-12. Inconclusive for the invention goal. No new transform was adopted.

Specific proposal: keep a word as two exposed summands p,c with
x=(p+c) mod 2^32, and defer normalization across additions. This preserves
the represented value but provides a one-add decoder whenever p,c and their
correspondence are known. Lowering bitwise operations directly on this
representation could avoid an explicit decoded temporary, but does not
remove that decoder. Unknown slot identification would require a separate
experiment; no blind binary-recovery result is claimed here.

Primary technical disclosure inspected:
[US8935539B2](https://patents.google.com/patent/US8935539B2/en), description
around Figures 3–4 and the carry-save discussion. It describes arithmetic/
Boolean substitutions for obfuscation, including XOR/AND addition, and
explicitly discusses carry-save partial-sum/carry outputs and parallelism.
This supports rejecting mere carry-save substitution as an independent
obfuscation principle. It does not establish equivalence to every possible
future persistent redundant-state construction. Its resistance assertions
were not experimentally verified here.

Additional lead: Dinu, Groszschädl, Le Corre, *Efficient Masking of ARX-Based
Block Ciphers Using Carry-Save Addition on Boolean Shares*, ISC 2017,
https://orbilu.uni.lu/handle/10993/37499 . Primary repository search metadata
and abstract excerpts were available, but the PDF timed out and the landing
page returned 502. Full-text mechanism and author implementation remain
uninspected. No side-channel guarantee is transferred to a full-state
software observer.

Queries: `SHA256 carry save representation boolean functions redundant arithmetic`;
`obfuscation "carry save"`; `"Efficient Masking of ARX-Based" "pdf"`;
`"Efficient Masking of ARX-Based" authors`.

The current sandpile-carrier and representation-recovery records were searched
before this screen. No new SHA run, optimizer measurement, Wasm After,
attack score, or comparative advantage was produced. The simple proposal is
rejected before implementation; enlarging its number of summands alone would
retain a direct summation decoder and would not address the stated defect.
