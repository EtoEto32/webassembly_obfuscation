# Redundant hash-state encodings: a concrete prior boundary

2026-10-12. Technical prior-disclosure check only. No legal assessment,
new algorithm, implementation, or test is claimed.

The next design question was whether many representations of the same hash
state, with a changing choice of representative, could by itself escape the
already reviewed bijective state-encoding family. It cannot serve as a new
principle merely on that basis: an inspected hash-specific source explicitly
allows it.

## Inspected primary disclosure

[US20200366496A1, Whitebox computation of keyed message authentication codes](https://patents.google.com/patent/US20200366496A1/en),
published 2020-11-19. The description's fully/partially encoded constructions
define a surjection E from t encoded bits to s state bits, t>=s, and require

```
E(h_E(x,m)) = f(E(x),m).
```

It also defines an encoded-input/plain-output g_E(x,m)=f(E(x),m), describes
combining encoded and ordinary compression calls, and explicitly names SHA-256.
The implementation discussion permits integrating E into the compression code
without materializing E(x). These are description-body passages, not merely
claims inferred from the title or a search snippet. They do not supply every
possible concrete h_E or prove every redundant representation to be known.

## Concrete tempting construction and its reduction

For an s-bit word-vector state, choose two equal-sized vectors u,v and decode
coordinatewise by D(u,v)=u+v modulo the word modulus. For an arbitrary
deterministic representative selector R, define

```
z = f(u+v,m)
U(u,v,m) = (R(u,v,m), z-R(u,v,m)).
```

Then D(U(u,v,m))=f(D(u,v),m) immediately. This is an explicit instance of the
source's h_E equation with E=D. Data-dependent changes of R, adding more shares,
or emitting plain output at a selected block do not by themselves identify an
independent transformation principle. This simple wrapper is not an adopted
candidate and will not be implemented as another hash prototype.

This reduction is specific: it accounts for the selector, pair update and
decoder of the displayed rule. It does not justify declaring every new
algorithm satisfying a simulation relation unoriginal. A more concrete
construction could still have an independent mechanism; that mechanism must
be shown in its generated operations, not solely in a non-injective decoder.

## Additional inspected source and limits

[US20140019771A1, Method and System for Protecting Execution of Cryptographic Hash Functions](https://patents.google.com/patent/US20140019771A1/en),
description under Robust Hashing, discloses encoded message/state/digest values
and replacing portions of SHA computations with tables operating between
encoded domains. Its title, relevant description and coefficient/table passages
were read. The entire patent was not audited. It adds hash-specific evidence
against claiming novelty from moving an existing encoding into padding,
schedule or compression operations alone.

Neither source settles the separate finite-ring residual generator's novelty:
showing a simulation equation is not a construction-level identification of
that evaluator. Its recorded hold decision remains unchanged.
