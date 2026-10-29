# SHA-256 eight-word trajectory steering

2026-10-12. **Rejected for novelty: Level 3.** No new execution test or Wasm
implementation was performed. The overall research goal remains unmet.

## Candidate

Replace a round segment by a different trajectory that rejoins its original
endpoint. Treat eight consecutive expanded words as independently selectable
controls. Convert the desired endpoint into eight consecutive A-history words,
then choose each control to force the next required A value.

## Direct prior correspondence

Indesteege, Mendel, Preneel and Rechberger,
*Collisions and other Non-Random Properties for Step-Reduced SHA-256*,
section 4.1, PDF pages 9–10, equations (12)–(14):
https://tugraz.elsevierpure.com/ws/portalfiles/portal/87150451/131.pdf

The inspected passage supplies all three operations:

| Proposed operation | Existing construction |
|---|---|
| Convert state to eight A-history words | Equation (12), bidirectional conversion |
| Express the next A from the history and W | Equation (13) |
| Solve W to preserve a chosen A trajectory and endpoint | Equation (14) and the eight-word control discussion |

Thus the central steering rule is already explicit. Using it for obfuscation
instead of collision construction would change its application, not its principle.

## Scope and decision

Independent expanded words need not satisfy the original message schedule.
Consequently steering alone does not establish a collision of full SHA-256.
An obfuscator could retain the original later schedule and rejoin the original
working state, but this does not add an independent generation mechanism.
Obtaining that target state also remains part of the required computation.

No attack was run. The rejection concerns identical construction steps, not
decoding difficulty. Existing history helpers were inspected only to align
notation; their historical test counts are not new evidence for this candidate.
Do not implement this steering rule under a new algorithm name or retry it
with a different segment length as a novelty claim.
