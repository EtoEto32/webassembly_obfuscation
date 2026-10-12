# BinMirror artifact applicability audit

2026-10-12. Budget: one archive download, at most 20 minutes of static inspection; no author code execution, model calls, or malware execution. This is a baseline applicability check, not a new obfuscation algorithm or resistance experiment.

Question: does the artifact linked by arXiv:2608.20628v1 expose a reproducible path for the existing standalone SHA-256 Wasm, and what implementation/evidence assumptions would adapting it require?

Before inspection, require: published archive checksum match; enumerate members without extracting executable content; read relevant documentation and source as data. Record actual frontend, evidence format, model configuration, validation implementation, and missing dependencies. An unsupported frontend is not an attack failure. A paper description alone is not proof that the artifact implements the procedure. Do not infer absence across uninspected files.

Sources: https://arxiv.org/html/2608.20628v1 sections IV and appendix D; linked https://zenodo.org/records/19067406 . The record identifies Project_BinMirror.zip and MD5 ca648d22980449425282530d771b3387. MD5 is used only to match the publisher's artifact, not as a security guarantee; record SHA-256 locally as well.

Existing result to reuse: tmp/contextual-invariant-recovery/README.md already cites the introduction. Do not repeat that as a new finding. No changes to CSEC paper, corpus, or previous experimental results.
