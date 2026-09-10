# ONE-G0.2 trusted prior-root reuse — exact hosted result

Date: 2026-09-10  
Experimental version: **ONE-G0.2**  
Decision: **ADVANCE_TRUSTED_PRIOR_ROOT_REUSE**

## Claim boundary

This result concerns a persistent adjacent-version research writer. The candidate reuses an independently established and verified SHA-256 identity for the prior root rather than recomputing that prior-root hash on every subsequent ingest. Both compared arms still charge source/target ctypes conversion, current-root SHA-256, relation admission, lazy Segment scheduling, segmentation, bounded generic Program construction, validation, and direct canonical emission.

Establishing/authenticating the prior trusted state initially, filesystem traversal, authenticated placement, and decode timing remain outside this experiment. This does not weaken integrity: reuse is permitted only for an already-authenticated immutable prior-root identity.

## Exact authority

- branch: `research/cmpct1`
- exact source: `070d4f803c7b4441f517fc5c0b90f19214f5b05f`
- workflow run: `34432051667`
- job: `102729416324`
- artifact: `10134862524`
- artifact digest: `sha256:043d36801dfaebc5306f15c85676ce170cb16736b400e9ac6b44fb0f2e29dfe5`
- schema: `cmpct-one-g02-trusted-prior-root-reuse-v1`
- frozen decision size: `1 MiB`
- frozen repetitions: `15`
- exact-source semantic suite: **12 passed**

The frozen decision law and writer semantics were checked before the falsifier. All semantic gates passed.

## Measured result

At the 1 MiB decision size, trusted-prior / rehash-both median CPU ratios were:

| case | relation admitted | ratio |
|---|---:|---:|
| shift_plus1 | yes | **0.774645x** |
| shift_plus1_damage_quarter | yes | **0.942957x** |
| fragmented_every96 | yes | **1.000857x** |
| fragmented_every32 | no | **0.656554x** |
| independent_random | no | **0.638805x** |

The frozen target required at least four 1 MiB rows at or below `0.95x` and every 1 MiB row at or below `1.02x`; both conditions pass. Small-transfer guard rows at 64 KiB also pass their `<=1.05x` ceiling.

Representative 64 KiB ratios:

- shift_plus1: **0.813039x**;
- quarter-damaged shift: **0.947673x**;
- fragmented/96: **0.988690x**;
- rejected fragmented/32: **0.661123x**;
- rejected independent random: **0.640869x**.

Canonical wire, Surprise bytes, relation decisions, Program construction, reader work, and exact reconstruction remain unchanged between arms. This is purely removal of redundant hashing work when the prior immutable root identity is already legitimate state.

## Why this advances ONE

Adjacent-version ingest is naturally incremental. Re-reading and hashing an unchanged prior root during every new version creation wastes memory traffic and CPU if its authenticated identity has already been established and retained. Reusing that identity is an instance of ONE's broader changed-cone/incremental-work doctrine: redo only work invalidated by the new information.

The gain is especially clean on rejected controls, where no Law is emitted: eliminating redundant prior-root hashing reduces CPU to roughly 0.64–0.66x at 1 MiB without changing admission behavior. On the most segmentation-heavy productive case, relation work dominates so prior-hash removal is appropriately almost neutral rather than being advertised as a universal speedup.

## Hostile review

This promotion must not be misread as permission to trust caller-supplied hashes or stale mutable state. The prior identity must come from an independently authenticated immutable generation/state record. Mutation, identity mismatch, missing provenance, or uncertain state must force re-establishment rather than reuse.

The experiment also does not prove full-ingest economics because authenticated placement, filesystem traversal and initial trusted-state establishment are outside its measured envelope. Those costs remain debt for the full system gate.

## Next decisive action

Carry this incremental identity rule into the complete writer measurement adapter: when the prior generation is already authenticated, charge current-root identity and changed work, not redundant historical hashing. Preserve a separately measured cold/open path where prior trust must first be established. This distinction should be explicit in the September 11 access/resource accounting rather than silently mixing cold and warm lifecycle semantics.
