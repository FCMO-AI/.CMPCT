# v0.30 Shifted small-global-anchor expansion — terminal negative

## Decision

**RETIRE_FAMILY** for the small-global-anchor PrefixGraph expansion family on the frozen Shifted structural red. Do not spend another activation adding a fourth/fifth global anchor or shaving metadata around this representation unless new exact evidence invalidates the capacity result below.

This is research evidence only. It changes no product selector, archive grammar, benchmark threshold, release authority, locality rule, or platform requirement.

## Exact evidence

Source commit: `e2333ccb6a19d961d82def690860e29bc6c87e99`

Workflow: `CMPCT v0.30 PrefixGraph three-anchor representation`

Run: `33429454655`

Job: `99611625144`

Frozen Shifted comparator and candidate measurements:

| Representation | Complete bytes | Gap vs solid Zstd-19 |
| --- | ---: | ---: |
| solid Zstd-19 | 1,694,674 | 0 |
| shipping PrefixGraph | 1,701,398 | +6,724 |
| exact best three-anchor PrefixGraph | 1,702,346 | +7,672 |

The exact three-anchor candidate SHA-256 was `36e5c655ba45c62a0daa022f4fe193b816e7e0440844439506992509a9262d55`. Its selected payload was 1,676,823 bytes and its reconstructed semantic tree was `5ebe713182e8e59b28bc277b58c0770ce5e36ece0a85f8d3a734fad4d8962a1`.

The exhaustive three-anchor result is therefore not merely still red against the external frontier: it is **948 bytes larger than the existing shipping PrefixGraph candidate**. Adding global anchors did not close the representation gap.

## Domination audit

- Strict target: **15/15 workloads strictly smaller AND strictly faster to create than ZIP/Deflate and solid Zstd-19**, with accepted-v0.29 and all integrity/locality/platform laws preserved.
- Diagnosis: **D4 — representation-capacity red**.
- Radicality: **R4**.
- Saturation: **S2 + S3 + S4**. Repeated small-global-anchor expansion failed to close the exact Zstd gap; a stronger three-anchor representation regressed against the shipping representation; continued anchor-count search has low expected information gain.
- RPS at the decisive experiment: **>=80** (high-impact structural red, exact decisive falsifier).
- Measured gap change: **-948 bytes versus shipping PrefixGraph** (worse), and **-7,672 bytes versus the required Zstd-19 boundary**.
- Strongest surviving self-critique: the failure retires *small global anchor-count expansion*, not all relation-aware representations. A representation that changes ownership or jointly codes edit structure can still alter the payload floor.
- Terminal decision: **RETIRE_FAMILY**.
- Next decisive test: change the ownership/representation law rather than the number of global anchors. In particular, test whether a structurally chosen anchor plus exact bounded edit programs, compressed jointly as one locality-safe decode unit, can beat the external payload floor without hiding construction cost.

## Why this is terminal

The point of the three-anchor experiment was to answer whether the two-anchor miss was simply insufficient global reference capacity. It answered that question negatively. Continuing to four or five anchors would be search-count escalation inside the same failed ownership model, not a new representation insight.

Any future reopening must carry new evidence showing that the measured three-anchor capacity result is inapplicable—for example, a different exact ownership grammar or a proof that a new anchor interaction changes the payload floor. Merely trying more anchors is not sufficient.
