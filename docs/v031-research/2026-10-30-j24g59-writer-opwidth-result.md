# J24G59 — True public Writer reachability of J24G58's wide-op index (decisive negative)

**Scientific decision: `ORDINARY_WRITER_FAST_PATH_NOT_REACHED`** for the current public Writer mutation entrypoints and the 64-generation boundary across Ubuntu, macOS and Windows. **This narrows product applicability; it does not falsify J24G58's ≥16-op helper speedups or modify/retire its independent implementation.**

## Authority and preregistration

- Repository: `FCMO-AI/.CMPCT`, published main `80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0 / format r24 unchanged).
- Separate scientific draft [#798](https://github.com/FCMO-AI/.CMPCT/pull/798), stacked on J24G58 [#797](https://github.com/FCMO-AI/.CMPCT/pull/797) exact parent `cd75aca5df40ff5dd2dbdab67b7770604bc8404f` (which itself inherits #795 `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`).
- Preregistration committed at `194582327db15b2d18205c250d3899cf5d396da8`, **before test and workflow implementation**.
- Source-exact hosted tested head `57a1f63caab0ed7c929dd7918377d1b6ff0d79c1`; code hash `src/cmpct/journal_replay.py` = `ba5ac2d01be9757651576a6fb5d640c4d212a62a`, public Writer `src/cmpct/transactions.py` = `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`, both **unchanged** from #797 parent.

## What was measured, not assumed

[Exact-head tri-platform hosted workflow #40991811610](https://github.com/FCMO-AI/.CMPCT/actions/runs/40991811610): **SUCCESS, 3/3 jobs** (Ubuntu 24.04, macOS 14, Windows 2022), product actually installed and authenticated by source Git blob plus installed-module source comparison. Each platform:

1. Build a genuine reproducible 80-file r24 archive using public `Builder`.
2. Execute public `append_update` (replace), `append_update` (insert), `append_delete`, `append_rename`, then 60 additional real `append_rename` operations. Preserve after each mutation its latest footer's position/kind, previous pointer, actual signed MessagePack payload SHA-256, revision, member count and observed `ops` width. A **detached** Zstandard/MessagePack parser—not CMPCT Reader's generation decoder—authenticates each current committed generation.
3. Before the 64th operation preserve the 63-delta archive; at the 64th preserve the kind-0 full checkpoint, then issue a 65th ordinary rename after checkpoint.
4. Instrument the *actual installed Reader* invoking `_try_indexed_row_mutations` on each history and verify all 80 physical member SHA-256 hashes. Observe `ops_width=1` on every delta, never `>=16`. At the depth-63 archive, **62** dispatcher calls reject admission (a replacement of an existing `put` bypasses the dispatcher by an earlier direct shortcut); at the checkpoint **0** calls; at depth-1 **1** call rejecting admission. **0 standard Writer-produced indexed dispatches**, on all three hosts.
5. Separately construct an *explicitly nonpublic* SHA-valid 20-op signed delta with private `_append_generation` over the same authentic base, verify all 80 contents, and observe **exactly one `indexed=True` call**. This proves the optimized helper can run and identifies the product entrypoint boundary rather than blaming implementation failure.

The project public CLI routes `update/delete/rename` one-to-one into these same Writer functions (`src/cmpct/cli.py` lines 88–96). The newest real Writer commit is a checkpoint when the inherited depth reaches 63; a chain of 63 single-op deltas is **not** one 63-op generation.

## Raw preserved evidence

| Host | Result JSON SHA-256 | Original artifact |
|---|---|---|
| Ubuntu 24.04 | `eaba3088641638222e5c652cd5dd7ae752962bfb3dbffbbe5ae3462a61df9999` | [#12949024912](https://github.com/FCMO-AI/.CMPCT/actions/runs/40991811610/artifacts/12949024912) |
| macOS 14 | `7cf9f791ab3538d89a0f72312a20cd90ad8ee5d28b555086b1eb611024a39adc` | [#12948724480](https://github.com/FCMO-AI/.CMPCT/actions/runs/40991811610/artifacts/12948724480) |
| Windows 2022 | `525152820fb862f57781737164c2f94d41ddb33ea5bae62ab83a078a1cda72e6` | [#12949816081](https://github.com/FCMO-AI/.CMPCT/actions/runs/40991811610/artifacts/12949816081) |

Each artifact contains the complete independently decoded signed-wire generation trace, Reader invocation counts, verified source identity, host/runtime, and raw original build log. The host JSON digests **differ as expected** due to host-specific source-file metadata and timestamps; no cross-platform byte-for-byte archive identity is claimed. A preceding Ubuntu-only positive [push run #40991457265](https://github.com/FCMO-AI/.CMPCT/actions/runs/40991457265) on earlier test HEAD `56c9fd08afa3cf8c39443bca006f997ee7345cbd` produced the same decision; original [artifact #12948664051](https://github.com/FCMO-AI/.CMPCT/actions/runs/40991457265/artifacts/12948664051), receipt JSON SHA-256 `7edcc8079b0c5a049e32abae5eb9e890efa4d82d796b8422714d6868ed3d52aa`. The final tested head differs **only in line-ending portable test/workflow mechanics**; no product source changed.

## Scientific consequence and strongest controls

J24G58's same-generation helper court **still** demonstrates a measured 4,096-rename median `174.235 ms → 5.238 ms` (**33.266×**) at exact code source, plus **684,896 B additional Python-traced allocations** for the large synthetic case. Those are valid measurements of a **different eligible input shape**: 4,096 operations in one signed generation. The current ordinary public Writer does not create that input shape. Therefore **shipping-performance credit from the helper court on ordinary Writer-generated archives is 0** without a reachable admission or measured whole-product win. Third-party/historical wide-op r24 journals may still benefit, and the current Writer can read the explicitly constructed positive control.

The strongest simpler alternative is to leave J24G58's helper as research and focus the real product bottleneck: current Reader replays up to 63 **separate one-op deltas** between checkpoints, repeatedly rebuilding name/metadata ownership. A cross-generation indexed replay session could reuse the index across commits while preserving individual durability boundaries, but this is currently a **hypothesis**, not implemented or benchmarked. Historical exact-source [#344](https://github.com/FCMO-AI/.CMPCT/pull/344), [#346](https://github.com/FCMO-AI/.CMPCT/pull/346), [#358](https://github.com/FCMO-AI/.CMPCT/pull/358) already establish substantial *batched signed-delta* hot-path/ownership evidence and must not be falsely promoted as today's standard Writer-derived chain economics.

## Contradictions, costs and boundaries

- This court does not prove absence of public batching APIs in unknown external extensions, future Writers, or manual/private r24 generation paths; it proves tested current `transactions` public mutations and their CLI routes do not admit J24G58 optimized ≥16-op branch.
- The workflow does not measure complete creation/extraction, benchmark against ZIP/Zstd, cold-start CPU/RSS, xattr ownership on hardlinks, recovery from truncated footers, or real 4K-index physical Reader latency. All remain **unmeasured**.
- Proven xattr owner/index fixes remain on separate draft PR owners #773/#783/#789/#795. No edits to those surfaces, branch owners, frozen sources, `main`, `docs/discovery/STATE.json` (#574 owns reconciliation), format, version, benchmark thresholds or release gates.
- Exact-head Engineering Evidence, Version Discipline, CI Topology, R36 Attribution are separately tracked; a specialized SUCCESS is not a merge/release permit.
- Causal alternative explanation—“the indexed function is broken, so never fires”—is directly falsified by 20-op physical positive control. Another explanation—“64 generations are coalesced to a 64-op batch”—is falsified by footer kind+width evidence.

## Counterfactual replay / transferable prospective lesson

**Earlier cheapest discriminator:** inspect (a) the optimized helper's `len(ops)>=16` admission condition and (b) every public Writer `delta={'ops': [op]}` mutation path **before** benchmarking 4K-op synthetic fast paths. A 64th-operation physical footer check then confirms a full checkpoint, not a batch. This discriminator was prospectively recognizable from the code and would have narrowed the product claim earlier at negligible cost. General lesson: *measure reachability of an optimization from shipping product entrypoints before interpreting impressive synthetic helper speedups as shipping benefits*. One newly confirmed case does **not** justify rewriting the Discovery Engine policy; keep it a scoped scientific lesson.

## Decision and next exact action

`ORDINARY_WRITER_FAST_PATH_NOT_REACHED`. Preserve #797 helper speed evidence and extra-memory negative, tell owner #797 to narrow attribution. **Highest-value unclaimed action:** benchmark source-exact *ordinary* 63-single-delta Reader open vs identical final-index checkpoint at 2–4K files, with raw repeated cold-process wall/CPU/VmHWM plus one authentic metadata rekey/64th-checkpoint case. Then preregister a cross-generation ownership model that can eliminate repeated sort/rekey without weakening per-commit recovery. A helper with no reachable standard-Writer path should not be promoted merely for synthetic 33×.

**No product modifications, merge, version, format change or release. Scientific finding: decisive; product speedup: unearned.**
