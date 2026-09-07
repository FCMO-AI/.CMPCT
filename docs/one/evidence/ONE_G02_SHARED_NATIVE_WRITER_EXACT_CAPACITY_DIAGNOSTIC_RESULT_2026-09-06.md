# ONE-G0.2 shared native writer exact-capacity diagnostic result — 2026-09-06

Status: **terminal negative for the tested universal exact-capacity allocation shape**. This receipt is diagnostic research evidence, not promotion authority.

## Mission lock

Hypothesis: after preserving the seed writer's acceptance/resource guard and canonical ONE0 semantics, deriving the exact final wire length from already-validated Segment metadata and allocating exactly that many output bytes will materially reduce requested allocation while keeping full-writer elapsed inside the preregistered no-regression envelope.

Disproof rule: if the exact-capacity candidate materially regresses ordinary/control writer elapsed, reject it as a universal system optimization. Do not rescue it with corpus-, size-, segment-count-, or density-specific thresholds. A future reopening requires a causally different shape in which exact size is available essentially for free from already-required work, or direct evidence that allocator slack itself becomes a dominant physical-memory cost.

## Exact source / CI authority

- branch: `research/cmpct1`
- experimental version: `ONE-G0.2`
- exact source HEAD: `0e948509870bae3fd97d4c2e05f30da4a1d9b074`
- workflow: `ONE-G0.2 exact-capacity full-writer diagnostic`
- run: `34069247739`
- job: `101583425643`
- event: `push`
- conclusion: `success`
- runner: Ubuntu 24.04 hosted runner
- compiler: `cc -std=c11 -O2 -Wall -Wextra -Werror`

The timed candidate boundary includes validation, exact sizing, allocation, and canonical emission. The harness first requires seed/candidate byte parity, lengths, Surprise accounting, hierarchy depth, node count, `exact_cap == emitted_wire`, and `seed_cap >= emitted_wire`. It then warms both paths equally and alternates A/B–B/A order.

This matrix is explicitly non-promotional; it is a causal diagnostic, not a substitute for the frozen authoritative promotion matrix.

## Exact result

| Row | Wire B | Seed requested B | Exact requested B | Capacity ratio | Candidate/seed elapsed |
|---|---:|---:|---:|---:|---:|
| disabled-1k | 2,165 | 6,144 | 2,165 | 0.352376x | **1.134055x** |
| mixed-1k | 1,677 | 6,400 | 1,677 | 0.262031x | **1.150643x** |
| ref-heavy-8k | 8,349 | 20,992 | 8,349 | 0.397723x | **1.166537x** |
| fragmented-8k | 13,046 | 28,672 | 13,046 | 0.455008x | **1.483372x** |
| hierarchy-4097 | 24,586 | 278,721 | 24,586 | 0.088210x | **0.841398x** |

Requested output capacity fell by roughly 54.5%–91.2% depending on row. However, four of five rows became 13.4%–48.3% slower. Only the extreme 4,097-segment hierarchy row improved elapsed (~15.9%).

## Causal interpretation

The experiment separates nominal allocation size from useful system work. The seed's loose output capacity is often cheap because unused reserved bytes are not necessarily touched or resident. Exact sizing, by contrast, adds integer/varint accounting and hierarchy-span bookkeeping before emission. On ordinary and fragmented rows that added compute dominates any benefit from asking `malloc()` for fewer bytes.

The hierarchy-4097 win does not justify a dispatcher. That row combines an unusually large loose reservation with metadata-heavy hierarchy, so exact sizing can amortize. Turning this isolated win into a segment-count or workload gate would violate the preregistered universal hypothesis and add another heuristic boundary.

No RSS or physical-memory claim is made. Requested `malloc()` bytes are not peak resident memory.

## Hostile review

Strongest criticism of the negative: this is a compact diagnostic matrix rather than the historical promotion matrix. Therefore it cannot prove the exact quantitative loss distribution on every authoritative workload. It can, however, falsify the universal mechanism because several semantically valid ordinary/control shapes regress far beyond the allowed no-regression envelope while the candidate is charged honestly.

The implementation also reveals why further arithmetic micro-tuning is low-value: for normal rows, exact sizing duplicates information needed only to shrink untouchable slack. Saving that bookkeeping would require changing the representation boundary so exact size becomes a by-product of work already required for correctness/emission, not merely making `exact_uvlen()` slightly faster.

## Decision

**REJECT `exact-capacity` as the universal shared-native-writer allocation baseline in its tested shape.**

Retain:

1. the semantic/count oracle and hostile acceptance-domain tests as useful conformance instruments;
2. the fact that loose requested capacity can exceed emitted bytes substantially;
3. the hierarchy witness showing allocation size can become relevant in extreme metadata-heavy cases.

Do not retain a runtime exact-capacity dispatcher or promote exact allocation based on requested-byte accounting alone.

## Reopening predicate

Reopen only if one of these becomes true with preregistered evidence:

- exact final size is already produced as a near-zero-cost side effect of mandatory validation/emission metadata, eliminating the extra sizing work; or
- direct process-isolated memory measurements show the seed's loose allocation causes a dominant physical-memory/RSS or allocation-failure cost large enough to justify a new multi-objective experiment.

A workload/size/segment threshold derived from this result is explicitly not a reopening predicate.

## Next decisive action

Move upward in scope. Profile or fuse the next full-ingest/native-writer boundary that owns real elapsed or memory traffic while preserving byte-identical ONE0 and reader semantics. Do not spend Genesis time rehabilitating this allocator-only idea unless its reopening predicate is independently triggered.
