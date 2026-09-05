# ONE-G0.2 native shared authenticated-family transfer — 2026-09-05

Status: **ADVANCE (native research transfer; not product/release authority)**

## Frozen question

Does the shared authenticated ONE temporal-family architecture retain its setup advantage and bounded selective-read cost when transferred out of CPython/hashlib into an independent native C/OpenSSL implementation and an independently generated deterministic corpus?

Freeze: `docs/one/prereg/ONE_G02_NATIVE_SHARED_AUTH_FAMILY_FREEZE_2026-09-05.md`.

## Exact execution

- source: `6b9194c755120cc7d7d8cc91407cbf69e8115835`
- workflow: `33957658377`
- result-bearing job: `101283808777`
- artifact: `9966911391`
- artifact ZIP SHA-256: `07970a0bc49b796aafa5bd6a9d48968e96430441a4f206ee1ff1ea8d7fb69b62`
- `tests/one`: **76/76 passed**
- checked schema: `cmpct-one-g02-native-shared-auth-family-checked-v1`
- exact failures: **0**
- corruption failures: **0**
- terminal decision: `advance_native_shared_auth_family`

The checked result is fail-closed against the preregistered thresholds. Hostile review before result acceptance found that the raw C prototype charged only the two q4 level-1 parent hashes rather than all ten V=8 non-root descriptor-auth hashes. The authoritative checker therefore adds the missing **256 B** per family, charges the full **320 B** q4 non-root hash set, recomputes persistence ratios, and only then applies the frozen gate. No corpus, timing threshold, leaf size, request size, version count or interpretation was changed.

## Results

### Persistent representation

After the accounting correction, shared persisted bytes remained about **11.14–11.22%** of nine independently authenticated roots on every family:

- 64 KiB families: independent `1,062,720 B`; shared `119,230–119,235 B`; worst ratio **0.112198x**.
- 256 KiB families: independent `4,248,000 B`; shared `473,180–473,183 B`; ratio about **0.111389x**.

The shared ONE representation therefore retains roughly an **88.8% persistent-byte reduction** in this V=8 transfer regime even after the descriptor-tree accounting defect is corrected.

### Authentication setup / creation-side carrying cost

Every row passed the frozen <=0.20x setup gate. The worst measured ratio was **0.115656x**.

Representative medians:

- 64 KiB family 0: independent `5,784,761 ns`; shared `669,045 ns` = **0.115656x**.
- 64 KiB family 2: independent `5,490,163 ns`; shared `628,129 ns` = **0.114410x**.
- 256 KiB family 0: independent `22,918,432 ns`; shared `2,578,616 ns` = **0.112513x**.
- 256 KiB family 1: independent `21,907,362 ns`; shared `2,441,091 ns` = **0.111428x**.

Thus the approximately nine-fold setup advantage observed in CPython transfers independently into native C/OpenSSL.

### Authenticated selective reads

Every row passed the frozen <=1.20x read gate. The worst measured shared/independent ratio was **1.084357x**.

- 64 KiB rows: **1.07186x–1.08436x**.
- 256 KiB rows: **1.06565x–1.07043x**.

The native transfer therefore pays only about a **6.6–8.4%** selective-read elapsed premium while preserving the large temporal persistence/setup advantage. The premium did not grow with root size in the tested regime.

## Causal interpretation

The shared-authentication result is not a Python benchmark artifact. On a separate corpus and execution surface, authentication can follow the stored ONE information rather than every logical reconstructed output:

`authenticated basis + authenticated generic Law/Surprise -> exact authenticated requested range`.

This preserves the central temporal/version sharing advantage while bounding the authentication work needed for a selective read. The previous architecture in which every reconstructed version receives a full independent output AuthTree should remain retired for this regime unless a hard integrity/recovery requirement supplies new causal evidence for reopening it.

## Strongest surviving criticism

This still starts **after discovery**. It does not charge the writer for identifying the basis/version relation, and therefore is not an end-to-end creation-speed result. The C harness also models in-memory authenticated cones, not physical storage layout or I/O scheduling, and only exercises shallow translation Laws rather than arbitrary deep/multi-parent graphs. Memory traffic, update invalidation, failure blast radius, physical addressability and canonical wire accounting remain product debt.

There is also an implementation-quality warning: the research C profiler emits two `-Wmisleading-indentation` warnings. They do not alter the executed statements or result semantics and did not affect the frozen measurements, so this exact result remains authoritative; they should not be used as an excuse to mutate/re-run the frozen instrument for a prettier log.

## Decision

**ADVANCE** shared representation authentication. Native transfer removes a major uncertainty: the CPython selective-read premium did not disappear, but it remained bounded and small enough under the frozen falsifier while the storage and setup gains survived nearly intact.

Next scientific work should return to the Engineering Grid's current writer-side marginal-information-yield question: fuse the promoted tail-return selection path with the surviving suffix/minimizer observation path under a strict-union equality test, so these discovery signals share one traversal rather than accumulating another full input pass. Authentication should now be treated as a surviving ONE substrate with explicit remaining physical-layout/deep-graph debt, not as the highest-value blocker for the next activation unit.
