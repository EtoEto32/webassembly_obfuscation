# Source check, 2026-10-12

## New primary evidence

US8286251B2, *Obfuscating computer program code*, granted 2012. https://patents.google.com/patent/US8286251B2/en . Read the description around the paragraphs beginning “In the following, an embodiment ... varying the encoding over time”, “Furthermore, when updating the encoding”, and the worked example under “Altering the Encoding Over Time”. The description permits temporarily inconsistent encoded function addresses if the addresses actually used still decode correctly; it also describes changing redundant parameters during execution. This is concrete prior disclosure of demand-dependent partial validity, not evidence that our arithmetic quotient construction is the same algorithm. Function-address encoding is not general non-injective arithmetic-state compression. Patent existence is used as prior technical disclosure only; no legal status, validity or infringement assessment is made. No implementation or benchmark executed.

## Other search leads: do not treat as read papers

Giacobazzi, *Hiding Information in Completeness Holes*, SEFM 2008. Search returned the author's abstract and indexed PDF passages at https://profs.sci.univr.it/~giaco/download/sefm08.pdf . Direct fetch timed out; the alternate scienze.univr.it host was inaccessible. Giacobazzi et al., PEPM 2012, https://profs.sci.univr.it/~giaco/download/pepm12-giacobazzi.pdf : indexed passage available, direct fetch failed. These failures do not establish either novelty or absence of prior work. Their full technical statements were not used to reject the candidate.

## Searches and scope

- obfuscation abstract compilation completeness non injective data abstraction
- program obfuscation backward completeness abstract interpretation continuation state abstraction
- obfuscation projective coordinates integer arithmetic
- obfuscation Plucker / Plücker
- obfuscation non-injective encoding program

The last searches were exploratory alternatives, not implemented algorithms. A title mentioning projective functional encryption was not accepted as evidence about ordinary projective-coordinate obfuscation. Non-detection of relevant Plücker results proves nothing about novelty. No comprehensive literature search or author contact was performed in this check.
