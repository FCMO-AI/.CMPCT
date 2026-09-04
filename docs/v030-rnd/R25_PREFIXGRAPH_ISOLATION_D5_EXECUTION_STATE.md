# PrefixGraph process isolation — D5 execution state

Status: **ACTIVE D5 CONVERGENCE / S6 BUILDER SUPPORTED / RELEASE LOCKED**

This is the zero-history execution pointer for the supported Shifted PrefixGraph process-lifetime mechanism. It does not supersede frozen preregistrations or result receipts.

## Supported mechanism

Frozen S6 v2 authority: `docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_V2_PREREG.md`.

Durable terminal result: `docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_V2_RESULT.md`.

Exact S6 source `ee7fb2bb5ca7eb685c1f8c11be37cc04d354720a`, run `33727694904`, job `100560378734`, artifact `9882714798` proved:

- terminal decision **`PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED`**;
- robust whole-process-tree RSS **368,110 -> 259,418 KiB** (**29.5270435468% lower**);
- wall **48.6507572035 -> 52.0816314795 s** (**1.07052047025x**);
- selected PrefixGraph size **1,700,531 -> 1,700,594 B** (**+63 B / +0.00370472517%**);
- mtime-stable genuine-r24 identity **29,883,488 B**, SHA-256 `a3192a1462e37282e5128e50c3b20a039ca26821d5ceb2508958d6e3918bbc22`;
- deterministic bytes/tree, one bounded level-15 child, child dead before G0-G4 and hostile failure fail-closed.

Forge state is therefore D5 `CONVERGENCE`, not rehabilitation. Do not retune or reopen the supported memory mechanism unless broader productization produces new causal debt.

## Product-boundary correction landed after S6

Audit found that `PrefixGraphProcessExecutor` launched its child from the repository root while passing caller paths unchanged. A relative source or archive path could therefore be reinterpreted relative to the repository rather than the caller's working directory. S6 used absolute temporary paths and could not detect this.

Landed fixes:

- `13f9d87ebbe536ec36babdb8ffa7b98be459349c`: freeze caller-relative source/archive meaning to absolute parent paths before switching child cwd; preserve symlink spelling by using `abspath`, not `resolve`;
- `a114ba8b6bc0c12c1352011df75ba4759c97e5d0`: focused regression proving relative source/output paths retain caller meaning while the child runs under a different cwd;
- the focused regression passed inside the promoted runtime gate prerequisites on exact product fingerprint `eebe3621e50f32cccb3cf7d934e0093ba437babb` before its long paired measurement began.

This is a portability/correctness repair only. PrefixGraph bytes, level, candidate grammar, locality, tie law, integrity and S6 thresholds are unchanged.

## Runtime-authority custody correction

The expensive runtime workflow used `cancel-in-progress: true` together with a latest-head classifier. Observed behavior proved that cancellation happens before that classifier can decide a superseding commit is product-neutral: a follow-up test commit canceled a result-bearing run, then its replacement skipped. That can starve authority indefinitely on an active integration branch.

Landed custody fixes:

- `eebe3621e50f32cccb3cf7d934e0093ba437babb`: bind the PrefixGraph process-boundary regression to runtime admission and execute it as a fast prerequisite;
- `93d838a69864b1253ef7ccd4c7adbd955f54807a`: serialize the expensive runtime concurrency group (`cancel-in-progress: false`) so neutral queued runs cannot kill an active receipt before classification. Every material run remains bound to its own immutable `EVIDENCE_HEAD`; no older result is promoted as exact-head truth.

## Broad-product RSS truth boundary

The promoted canonical runtime worker still reports parent `RUSAGE_SELF` RSS. That is insufficient as decisive memory authority once PrefixGraph deliberately uses a child process: descendant memory would be gifted away.

The repository already contains a stronger immutable-threshold companion:

- `benchmarks/v030_release_performance_tree_rss.py`;
- `benchmarks/v030_perf_worker_tree_rss.py`;
- accounting: `whole-process-tree-vmrss-10ms-with-parent-rumaxrss-floor`;
- same three frozen runtime targets, same balanced order and same `1.10 / 1.25 / 1.25 RSS` limits;
- `child_memory_gifted = false`;
- explicit **zero release credit**.

`b4a51362b5da4d519793b62827a5e4327f171f21` registered `.github/workflows/v030-release-performance-tree-rss.yml` to execute that pre-existing companion independently. This does not rewrite the older promoted runtime instrument or turn a diagnostic into release authority. Its result is D5 decision evidence about the real broad-product memory gap.

## Current running/pending evidence

At creation of this state file:

- legacy promoted-product runtime run `33732765108`, substantive job `100576315973`, on product fingerprint `eebe3621e50f32cccb3cf7d934e0093ba437babb` had passed compile/front-door/path/fast prerequisites and was in the paired product runtime measurement;
- its timing/identity result remains useful if terminal, but its parent-only RSS must not be treated as decisive process-isolated memory evidence;
- the whole-tree companion workflow is registered and must be consumed on the next exact eligible run; it grants no release credit even if green.

## Remaining D5 vector

1. consume broad whole-process-tree product RSS and identify the exact remaining Shifted/Logs/ML owner, if any;
2. consume current product create/extract timing without gifting child RSS;
3. run recovery/integrity/resource/path authority after the process-boundary repair;
4. prove Python concurrency/profile isolation under multiple independent product builds;
5. prove Windows/macOS subprocess/path/temp cleanup semantics; Android/constrained-host feasibility remains explicit under existing release law;
6. retain native/reader/platform authority where the resulting archive surface is implicated;
7. regenerate exact current-fingerprint competitor and final strict release authority.

No merge, tag, version bump or v0.30 publication is authorized until the repository's strict release authority reports `UNLOCKED` on one exact frozen candidate.
