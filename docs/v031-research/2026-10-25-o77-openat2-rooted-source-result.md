# O77 — Linux rooted source lookup: authenticated outcome
Date: 2026-10-25 UTC. Research-only finding; no Builder fix or release.

## Source authority
Preregistered at `4ebe7a3f4c5eb190006caeab8159778c75fe86ab` before code and observations. Experiment source: `427f8ce831bf6963c875afe7605c6298942be282`, based on canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; original Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044` unchanged. Product owner #407 and defect #408.

## Independent hosted actual results
Two genuine source-exact GitHub Actions executions, Linux Ubuntu 24.04 kernel 6.17.0-1022-azure x86_64, both completed SUCCESS with explicit `O77_REAL_TESTS=17 DEPTHS=3 SEVEN_REPETITIONS_PER_ARM PASS`.
- Push court: [run 40188187267](https://github.com/FCMO-AI/.CMPCT/actions/runs/40188187267), focused job 121153343886.
- PR court: [run 40188237953](https://github.com/FCMO-AI/.CMPCT/actions/runs/40188237953), focused job 121153488960, raw artifact [12597316658](https://github.com/FCMO-AI/.CMPCT/actions/runs/40188237953/artifacts/12597316658), uploaded ZIP SHA256 `b4d39a2533ffc12522db73706f4ca6ab7a695885046f74b3f96b87980b3cafa0` (from upload receipt).

## Observed properties
Both fully-independent GitHub runs executed 17 genuine syscall checks: four nested/Unicode regular-file positive cases × two comparators, four rejected hostile path/type cases × two comparators, and a post-open mutation negative.
- Linux `openat2` with `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS`, nonblocking opening and post-open `fstat` preserved regular bytes/inodes in valid cases; rejected intermediate/final symlink-to-outside, `../` and FIFO.
- The safe per-component `openat(O_PATH|O_DIRECTORY|O_NOFOLLOW)` control also passed all cases.
- **After-open same-inode overwrite was visible** through pinned open descriptor, deliberately falsifying any claim that descriptor-rooted opening provides a content snapshot. The source data itself is mutable despite trusted path lookup.
- Complete source tree scanning, ZIP/WHL deferred reads, sparse extents, xattrs, authentication, archive bytes, Reader or release gates were not modified or exercised by this primitive court.

## Paired cached-open microeconomics (NOT full-product throughput)
Each of two hosted runs measured seven randomized-order repetitions per arm, 250 real open+1-byte read+close operations per repetition, on paths at depth 1, 4 and 8. Values are **median component-walk wall / median openat2 wall**; greater than one means `openat2` was faster in this specific setup.

| Depth | Push run | PR run |
|---:|---:|---:|
| 1 | 0.7750× | 0.8279× |
| 4 | 1.5842× | 1.7981× |
| 8 | 2.4817× | 3.0069× |

The shallow one-component source lookup **favors the simpler per-component `openat`** by roughly 17–29% relative to one-call `openat2`. This disproves universal performance superiority. Nested depth 4/8 suggests potentially material syscall-work savings worth testing in the true Builder; Python/ctypes dispatch overhead, cache warmness, kernel/platform and path distribution are not neutralized. No process startup included; absolute CPU, RSS, cold I/O, end-to-end archive create, extraction and memory economics unmeasured. Same runner type replicated results; not independent platform families.

## Scientific decision, strongest negative, counterfactual
**Decision:** `openat2` root-confined resolution is a viable Linux *primitive* and an especially promising nested-path option, **not an implemented CMPCT correction**. H1 supported on the targeted static/race-prerequisite cases; H2 **narrowed** to deeper paths, not general speed. The untrusted-root/symlink containment question already had a cheaper positive O52b per-component `openat` oracle; this work adds the different syscall-owner economics decision. It would have been sufficient to run one shallow and one nested-depth paired control to falsify universal speed; full matrix unnecessary. No discovery-policy amendment earned from this single episode.

## Handoff
Notify Builder source custody owner PR #407 and issue #408. Avoid parallel Builder edits. The owner may evaluate Linux descriptor-rooted admission paired with macOS/Windows fallback, preventing TOCTOU at all read sites, snapshot/coherency/metadata policy, actual installed three-host Builder/Reader evidence, CPU/RSS/temp IO, and unchanged revision-24 promotion laws. Do not merge/release on primitive evidence.
