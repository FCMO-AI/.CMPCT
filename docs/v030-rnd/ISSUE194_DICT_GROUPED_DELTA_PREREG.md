# Issue #194 grouped historical-dict reuse — integrated A/B preregistration

Status: **frozen next-rung research plan / no product or release credit**

Authority: `agent/v030-authoritative-integration@496c96b40e09b6cd9a4eb81af2ec52db1caed354`.

Mechanism lineage:
- original owner: `agent/phased2-issue194-delta-index-reuse@ad74e628c4197bb1274a481d9c08daffc7a0c0fa`;
- lookup-hostile correction: `docs/v030-rnd/ISSUE194_DELTA_BASE_LOOKUP_HOSTILE.md`.

## Question

Can v0.28 and the current discovery-neutral attempt-5 child preserve exact candidate/final bytes while moving inherited delta-base index ownership from **per edge** to **per immutable base**, using the historical dict lookup unchanged?

The experiment does **not** test a new delta representation. It tests only ownership/lifetime of the exact historical lookup.

## Baseline

Current inherited delta audition does, for each candidate edge:

1. build the fixed-block weak-checksum dict for the base;
2. roll over the target and perform historical `dict.get(weak_key)` lookup;
3. emit the exact historical COPY/LITERAL program;
4. compress/price the program under inherited settings.

When one base has many target edges, step 1 repeats.

The v0.30 discovery-neutral attempt-5 worker disables position-independent candidate discovery. Its Placement child therefore still contains the inherited LSH/delta-audition family also paid by v0.28.

## Candidate

Within each child independently:

1. preserve candidate discovery and all candidate rows unchanged;
2. group auditions by base id;
3. build the historical weak-key -> ordered-offset dict once for the base;
4. run every target audition for that base with the unchanged rolling scan and first-offset tie law;
5. release the dict before the next base;
6. feed measured rows into the existing central-base / Placement policy unchanged.

Do not retain every base index simultaneously. Do not replace dict lookup with sorted arrays/bisection.

## Frozen product controls

Run paired baseline/candidate on identical generated source trees for at least:

- `resemblance_hostile_v1/01_shifted_versions` — high base fanout, positive mechanism case;
- `resemblance_hostile_v1/03_boundary_churn` — held-out structured transfer;
- `resemblance_hostile_v1/02_false_neighbors` — mandatory lookup-miss hostile;
- `resemblance_hostile_v1/05_incompressible` — zero-edge control.

For both v0.28 and current discovery-neutral attempt-5 child, require:

- exact candidate archive byte count and SHA-256 identity;
- exact tree identity / strong verification;
- exact inherited candidate count, accepted measured-edge facts, central-base assignment and pack-plan/locality facts;
- child wall and CPU with raw repeated samples;
- peak process-tree RSS;
- temporary/output I/O where available;
- no change to LSH bounds, delta block size, compression level, admission threshold, read-amplification ceiling, grammar or reader.

Then run the normal current shared/G0-G4 complete-product path on the same sources and record complete create wall plus final archive identity. Child-level wins earn no product claim unless the complete boundary improves or at minimum does not regress outside measurement noise.

## Preregistered decision

**Advance** only if all exactness/semantic controls are identical and at least one exposed structured workload shows a material same-run child CPU/wall reduction without a meaningful held-out wall or RSS regression.

**Narrow** if CPU improves but complete-product wall is hidden by another current owner; retain as efficiency debt only if carrying cost remains justified.

**Retire** this implementation if:
- False Neighbors or another held-out exposed row has a confirmed child wall regression;
- archive/candidate bytes, assignment, or locality semantics drift;
- peak RSS/materialization cost erases the useful wall/CPU gain;
- the integrated delta slice is too small to change current child economics.

A packed-array lookup result cannot satisfy this preregistration; that representation is separately falsified.

No benchmark, comparator, threshold, format, reader or release-law change is permitted.
