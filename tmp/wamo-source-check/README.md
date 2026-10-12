# WAMO primary-source availability check

2026-10-12. This updates the earlier bibliography-only status; it does not establish the transformation's novelty or technical details.

## Verified

The official WWW 2026 accepted-paper list includes WAMO and its six authors:
https://www2026.thewebconf.org/accepted/research-tracks.html

Author Hao Han's public website also lists it:
https://hhannuaa.github.io/

The public website repository is https://github.com/hhannuaa/hhannuaa.github.io . Its complete recursive tree was obtained through GitHub's public API and saved as public-tree.json. Tree identifier: 9a3b6eee5e3f7cc357d0099415ae267cdcfeb6bb, truncated=false. Of the visible filenames, the WAMO match is awards/2025-wamo.pdf, not a file in papers/. The 27 papers/ paths contain no identifiable WAMO filename. This is not proof no paper exists elsewhere or under an unrelated filename.

The matching PDF was fetched and inspected using pypdf text extraction and Poppler page rendering. It is a one-page award certificate, not the WWW research paper. SHA-256: a73a7042221de56cfdde7c38b3075d21e13c3f8ca8bd78405d3256ea820bc428. Therefore it provides no transformation rules or experimental protocol, and is not used as algorithmic evidence. The copy is retained solely to make this identification auditable.

## Still unavailable

Publisher DOI page https://dl.acm.org/doi/10.1145/3774904.3792297 failed through the web tool. Secondary abstract aggregators were found but not used to infer exact rules. In particular, a replication-package URL appearing in a ResearchGate search snippet was not accepted as WAMO's artifact: snippets can include text from referenced publications.

No author was contacted; no account login or access-control workaround was attempted. No technical overlap/non-overlap claim is justified until the paper or verified author implementation is available. This local source gap does not block the broader algorithm-design goal.

## Related unresolved source

asmMBA (SAC 2025) author-lab publication index was located at https://protocol.korea.ac.kr/publication . Search indexing exposes a PDF label, but direct retrieval redirected to a Google login page; the direct public Google Sites URL also failed. The existing abstract-only status remains. Do not repeat the same retrieval attempts without new evidence of availability.

## Research consequence

Mark WAMO as primary bibliographic confirmation, technical contents unread. It cannot be used either to reject every model-state transformation or to claim a candidate is distinct. Further implementation should rely on concrete rules and accessible comparisons already audited, rather than treating an inaccessible paper as evidence that an idea is new.

Searches: WAMO WebAssembly obfuscation 2026 Wang Yang Han; 3774904.3792297; WAMO obfuscation github; WAMO Pengfei Yu; WAMO Wang obfuscation pdf; asmMBA github; asmMBA pdf; asmMBA authors. No new algorithm or runtime experiment is claimed in this check.
