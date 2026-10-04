# v0.30 Office adaptive-effort Builder — mission lock

Date: 2026-09-13
Status: preregistered Builder gate; **research only**.

## Input evidence

The same-geometry effort referee showed that level-19 cold audition on the exact current Office pack boundaries recovers `484,719 B` of `484,476 B` B-regret versus the exact frozen Genesis-v0.29 surface. Four non-stream packs account for `480,110 B` of that opportunity. Hot inverse-view stream roots need no extra compression layer to reach the mature density floor.

## Builder mechanism

`experiments/entropygraph_v030_federated_adaptive_effort_candidate_v8.py` must:

- build the unchanged EG07 graph/control/recovery/locality representation first;
- keep every raw pack byte, pack boundary, membership edge and stream offset fixed;
- derive hot stream roots from authenticated `inflate_stream` recipes;
- never re-compress hot roots;
- for each other pack, start from the current level-1 storage choice and evaluate the fixed ladder `3,6,12,19`;
- retain the best storage choice seen;
- continue to the next rung after an improvement or exact tie and stop at the first strictly worse next rung;
- use no path, workload, extension or Office-derived numeric threshold;
- rebuild the same pack table and preserve existing metadata/recovery copies.

The first implementation may perform a post-build repack. That exported work counts against creation CPU/wall/RSS; it cannot be excused as prototype overhead when reporting evidence.

## Falsifiable hypothesis H-EG08-1

The threshold-free ladder can materialize most of the same-geometry oracle saving as a real, strongly verified archive while preserving the existing locality geometry and a large creation-compute advantage over frozen v0.29.

## Disproof / blockers

The Builder is rejected for Office if any of these occur:

1. reconstructed user-tree identity, physical pack authentication, primary/tail recovery, filesystem fidelity or reader operation fails;
2. maximum decoded unit, member amplification or member count changes from EG07;
3. the actual archive does not recover at least `80%` of the preregistered `484,719 B` same-geometry oracle saving versus the same-run EG07 artifact;
4. the actual Office artifact is not strictly smaller than the same-run exact frozen Genesis-v0.29 product surface;
5. fresh-process creation CPU is not at least `10x` faster than frozen v0.29 on the same Office tree.

The 80% rule is a mechanism-realization test against an already frozen oracle, not a selector threshold. The 10x rule protects the defining v0.30 compute advantage rather than optimizing a benchmark score.

Passing Office does **not** promote the mechanism. It only authorizes unchanged transfer to Analytics and held-out/hostile structured workloads.

## Required evidence

Same generated Office tree, fresh process per contender:

- EG07 stored bytes, creation CPU/wall/RSS;
- EG08 stored bytes, creation CPU/wall/RSS;
- exact frozen v0.29 stored bytes and creation CPU/wall;
- actual EG08 byte recovery versus EG07 and oracle-realization fraction;
- strong verify and exact filesystem identity;
- primary-corruption tail recovery;
- max/mean selective amplification, maximum decode unit and reconstruction membership count;
- EG08 effort attempts, early stops, selected effort levels and per-pack byte deltas.

## Preservation

No canonical version, format revision, locality limit, recovery rule, comparator setting, Genesis score or ONE evidence changes. `research/cmpct1` remains untouched.
