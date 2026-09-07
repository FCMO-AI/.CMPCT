# ONE-G0.2 AuthTree SHA prefix-state clone — hosted negative / partial seed

## Mission Lock / Referee

Authority: `docs/one/prereg/ONE_G02_AUTH_TREE_PREFIX_STATE_CLONE_PREREG_2026-09-07.md`.

Result-bearing source head: `9709cb05ce48c06555f41f6a3058341265ceea1a`.
Hosted workflow run: `34111466781`.
Result job: `101708638784` (`prefix-state-ab`).
Artifact: `one-g02-auth-tree-prefix-state-9709cb05ce48c06555f41f6a3058341265ceea1a`, artifact id `10014667262`, digest `sha256:754d26ebbe285299e66845301681a009ccb37e12319c05737e0d34144bdd36a6`.
Scientific exit code: `1`.

The workflow itself is red because the final step deliberately enforces the preregistered scientific decision. Compilation, semantic tests, the frozen A/B, and exact-head artifact retention all completed successfully before that decision step.

## Result

**Decision: `prefix_state_clone_insufficient`.**

All candidate roots were byte-identical to baseline (`exact_failures=0`). Candidate-added payload staging was exactly zero and the benchmark reported 336 bytes of bounded prefix-context workspace.

The mechanism is real but too small for the frozen advancement gate. Across roots >= 8 KiB:

- hosted productive wall median ratio: **0.964018966x** (~3.60% lower wall time);
- hosted productive process-CPU median ratio: **0.963914216x** (~3.61% lower CPU);
- max wall ratio over the entire 1 KiB-1 MiB grid: **0.995258416x**;
- max CPU ratio: **0.991659716x**.

Per productive row candidate/baseline wall ratios were:

| root bytes | wall | CPU |
|---:|---:|---:|
| 8,192 | 0.971019568x | 0.970182866x |
| 16,384 | 0.967822008x | 0.966659735x |
| 32,768 | 0.964833760x | 0.964452617x |
| 65,536 | 0.964386190x | 0.964180850x |
| 131,072 | 0.961593654x | 0.961517794x |
| 262,144 | 0.958759167x | 0.958740615x |
| 524,288 | 0.963290663x | 0.963188118x |
| 1,048,576 | 0.963651742x | 0.963647582x |

The frozen gate required every >=8 KiB wall row <=0.97x, median wall <=0.92x, and median CPU <=0.95x. The 8 KiB row narrowly missed the per-row wall gate and, more importantly, the aggregate effect is far from the required 8% wall improvement.

## Mechanism interpretation

Cloning a context after hashing only the fixed domain prefix avoids repeated initialization/prefix bookkeeping, but it does not remove the dominant SHA-256 compression work. The fixed prefixes are much shorter than one SHA-256 block, so there is no reusable completed compression block to amortize; most work remains in leaf payload and parent-child digest processing. This explains the broad but shallow ~3-4% gain and why the curve does not approach the frozen target at large roots.

This result rejects **prefix-state cloning alone as the preferred AuthTree construction answer**. It does not establish that the implementation is harmful: it is a reproducible bounded micro-optimization seed, but adopting it now would spend portability/maintenance budget on a small gain while the broader authenticated-placement path still has larger cost owners.

## Hostile Reviewer / exploratory follow-up

A non-authoritative local diagnostic tested a causally different idea: bypass repeated `SHA256_Update`/`SHA256_Final` parent-message handling by assembling fixed-size parent blocks and calling low-level compression directly. Applying direct block staging to all AuthTree messages regressed roughly 2-6% locally because copy traffic outweighed call savings. Restricting direct compression to parent nodes while leaving leaves on the ordinary path showed a small local improvement, and combining parent-direct handling with leaf prefix cloning produced roughly 4-6% local reductions on most tested rows. These diagnostics are discovery evidence only: they were not exact-head hosted receipts and do not justify promotion.

The useful conclusion is narrower and stronger: **do not continue optimizing the same prefix-copy mechanism or resurrect whole-message staging.** If parent-message specialization is pursued, preregister it as a distinct bounded-workspace experiment and charge all copied bytes; otherwise move upward to the shared-family/full-ingest cost owner where the existing structural savings are much larger.

## Campaign consequence

The resource-accounted multi-buffer route is already retired, and prefix-state cloning alone now also fails its advancement gate. Authentication work should not become an endless SHA microbenchmark tunnel. The next decisive work should either:

1. test a genuinely different parent-only fixed-message kernel with explicit copy/workspace accounting and a strict gain floor; or
2. move upward in scope and measure the already-promising shared authenticated Law+Surprise family inside a broader ingest envelope, where structural amortization has shown order-of-magnitude byte/build reductions versus independently authenticated roots.

No stored bytes, reader semantics, authentication semantics, v0.29/v0.30 comparator authority, or Genesis 15-workload status changes from this result.
