# Timing qualification

These 80 processes completed successfully, but the recovered core did not receive O3 while the other cores did. Thus the generic protocol description "O3 cores" was too broad. Preserve these pilot results and the original performance.py. Runtime-v3 applies one O3 pass to every raw core, including recovered, and rechecks the benchmark binaries before measuring. Both protocols vary only the first input word; remaining input words are fixed pseudorandom values. Neither is a whole-application or uniformly random per-call benchmark.
