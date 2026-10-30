# J24G65 — public one-op DELETE Reader-open phase attribution result

**2026-10-30 UTC. Final scientific decision: `DELETE_REPLAY_MAJOR_COST_OWNER` on 3/3 measured hosts. RESEARCH / DIAGNOSTIC ONLY. No Reader optimization, product promotion or format change.** This is a genuine new result under [preregistration](2026-10-30-j24g65-delete-phase-attribution-prereg.md), frozen in first commit `260951c6631910ed145aebc03b1868cb5770a46c`, before the instrumentation and source-bound tests.

## Exact provenance

- Canonical repository `FCMO-AI/.CMPCT`; research PR [#809](https://github.com/FCMO-AI/.CMPCT/pull/809), stacked on J24G63 [#805](https://github.com/FCMO-AI/.CMPCT/pull/805) at parent `7f509d244325d4b6ea6d0e752ea365f79c33a742`.
- **Result-bearing code HEAD** `e5c5c021ed824dad3eff73b03da0c14eb4e6b4d8`. Immutable inherited replay blob `03743ca2a06c022c2ec64243a90fe373cf91e899`; Reader blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`. Builder `a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2`, Writer `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`, validator `5ea3b8f26058b0983c9686295c73f15472bc3ffe`.
- Hosted [Actions #41007933563](https://github.com/FCMO-AI/.CMPCT/actions/runs/41007933563), Ubuntu 24.04, macOS 14, Windows 2022: three specialized jobs **SUCCESS**. All three independently ran the same installed-source tests, 72 raw observations each, detached physical-wire referee and 4/4 hostile receipt mutations refused per host.
- Original artifacts: [Ubuntu #12956556774](https://github.com/FCMO-AI/.CMPCT/actions/runs/41007933563/artifacts/12956556774), [macOS #12955938989](https://github.com/FCMO-AI/.CMPCT/actions/runs/41007933563/artifacts/12955938989), [Windows #12956163347](https://github.com/FCMO-AI/.CMPCT/actions/runs/41007933563/artifacts/12956163347).
- Downloaded GitHub original artifact ZIP SHA-256, separately measured after hosted execution: Ubuntu `f2e5d26ad07221fb11f776d403f7f645565f1718d5fd3de2f3567798b63ec64d`; macOS `09b6359ed118bd445bda268a019bca11b05941a704eeac2e1aa527b8e42bc402`; Windows `782fc45798746bd7e9b9370272fdf8df8fcbd9d96ccceab471d52e5fefc8ba90`.

## Prospective primary result

Source-bound genuine Builder + 63 public `append_delete` one-operation signed generations: 2,111 original files, 2,048 live files. Control: **same effective index, same member bytes**, privately appended full checkpoint. On every host the checkpoint costs **+12,990 stored bytes** above the 300,548-B chain (+4.32%). It is not a free shipping optimization.

| Host | Uninstrumented excess open (chain − checkpoint) | Wrapped excess open | Extra replay | Extra footer | Replay fraction | Instrument perturbation | Frozen decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Ubuntu 24.04 | 54.314 ms | 54.311 ms | 53.475 ms | 0.544 ms | **98.46%** | 0.0041% | MAJOR |
| macOS 14 | 53.584 ms | 49.507 ms | 48.047 ms | 0.348 ms | **97.05%** | 7.61% | MAJOR |
| Windows 2022 | 60.130 ms | 60.691 ms | 59.187 ms | 0.928 ms | **97.52%** | 0.93% | MAJOR |

All hosts pass the prospectively frozen materiality gate (uninstrumented excess >=3 ms), attribution gate (replay share >=60%) and perturbation guard (<=15%). **3/3 hosts support the same causal allocation.** The 2/3 cross-platform threshold was exceeded.

This is **not** a 97–98% faster product. It means 97–98% of the *additional* Reader-open cost of this specific depth-63 DELETE chain versus a private checkpoint is charged to the existing replay helper under the measured wrapper. A future implementation cannot claim that gain without source-exact full Reader A/B and whole-product resources.

## Detached after-host physical and arithmetic review

After GitHub Actions concluded, the three original ZIPs were separately retrieved and checked with a non-CMPCT Python reviewer using standard `zipfile/struct/hashlib/statistics`, MessagePack and system libzstd. It independently:
1. Recomputed every primary median, 72-sample SHA digest, call count, residual timer identity, replay fraction, perturbation and declared outcome;
2. SHA-verified all three original archive ZIPs and their physical contained revision-24 chain/checkpoint bytes;
3. Independently decoded the 64 chained physically authenticated generation footers from the original archive (63 `del` plus checkpoint), checked SHA-256 against decoded payload and applied the 63 deletes to the base index without importing CMPCT;
4. Confirmed this independently reconstructed 2,048-row effective index equals the appended checkpoint index exactly, with no rewritten chain prefix.

All three passed. The first independent attempt failed only on Windows artifact ZIP path spelling (`\\` in the saved manifest versus `/` in ZIP entries); the reviewer normalized ZIP separators and re-ran the same bytes without changing archive, output, prediction, evidence or threshold. This post-result secondary verification is explicitly **not** a prospective performance trial.

## Strongest negative and limitations

- Both the earlier [#805](https://github.com/FCMO-AI/.CMPCT/pull/805) and this J24G65 run observe DELETE overhead, but absolute Windows wall numbers differ between independent runner allocations (31.01 ms vs 60.13 ms). Cross-run timing is **not** a same-runner speed comparison and must not be explained as product change.
- Thin wrappers have measurable host-dependent perturbation; macOS 7.61% is within the frozen 15% guard, not zero. This is host-proven scoped attribution, not a universal performance guarantee.
- 63 operation generations are Writer-real; the checkpoint control is privately appended and adds real bytes. No shipping Reader rewrite exists; no source, on-disk format, native ABI, benchmark, release gate or `main` changed.
- Synthetic ordinary files in this experiment carry no sparse signed fsmeta/hardlink owner rewrites; fsmeta-heavy eligibility, malformed tail recovery, filesystem semantics, physical cold disk I/O, peak RSS, memory traffic, create/extract, native Reader and ZIP/Zstd competition remain unmeasured.
- The detached auditor used the same r24 footer framing contract, but a different implementation and no CMPCT imports; it is not cryptographic author authentication. Host source verification and stored Git objects remain the source authority.

## Decision, comparison and handoff

The independent DELETE diagnosis **confirms** the same broad cost owner that #801 attributed to RENAME on two hosts, while not pretending their data are a same-input A/B. Public same-path PUT was comparatively cheap under #805, so there is no basis for a universal update-speed claim.

The next highest-value action is **not** another deletion-specific threshold or expensive full matrix. [#808](https://github.com/FCMO-AI/.CMPCT/pull/808) owns a nonduplicative mixed-op plus signed fsmeta cross-generation factoring oracle: require it to prove exactness and cost first, then integrate under the shared [#795](https://github.com/FCMO-AI/.CMPCT/pull/795) Reader/preflight owner only after source-exact real public Writer cold-open, journal recovery, xattr/hardlink integrity and whole-system CPU/RSS/bytes/portability gates. If the mixed oracle fails, the next smaller route is to amortize O(N) per-generation DELETE lineage state (without changing r24 bytes), using the same physical archive and original helper as control.

Discovery policy/state unchanged: #574 owns stale state reconciliation; this new causal result is preserved here and on #809. No concurrency collision or self-modifying policy lesson earned. Product/release credit **0**.

## Post-result secondary robustness analysis (non-preregistered; no additional success gate)

After the original decision, a separate script recomputed *secondary* scope/shape checks directly from the original 3 ZIPs, without rebuilding any corpus or changing evaluation criteria. These are descriptive supporting observations, not a fourth prospective test or a product benchmark.

| Host | 512 files / 63 DELETE: extra replay (ms) | 2,048 / 1: extra replay (ms) | 2,048 / 32: extra replay (ms) | 2,048 / 63: extra replay (ms) |
|---|---:|---:|---:|---:|
| Ubuntu | 13.377 | 1.094 | 27.734 | 53.475 |
| macOS | 11.433 | 0.886 | 31.795 | 48.047 |
| Windows | 15.178 | 1.233 | 30.802 | 59.187 |

The growth across these four physical cases is consistent with repeated full-index work as both member count and depth increase; **only two member-count scales and three depths do not establish formal asymptotic complexity**. The footer excess at 2,048/63 is small and positive across all three (0.544/0.348/0.928ms), despite chain validification of 64 genuine footers.

To test whether the primary 63-depth attribution was a single-block artifact, independently computed within-block **mean** ratios replay excess / Reader-open excess. Across the four alternating blocks they range 0.985–1.012 Ubuntu, 0.970–1.015 macOS, 0.973–0.977 Windows. Fractions above 1 are possible from measurement noise and non-identical averaged timer components; they must **not** be read as the physical replay timer consuming more than total wall or as improved product speed. The prospective decision uses paired **medians** and its distinct perturbation guard, not these posthoc means.

**Counterfactual discriminator:** an inexpensive source-visible count of `_apply_journal_ops` per real committed generation plus n=512/depth63 micro-attribution would already have shown a strong plausible replay cost (11–15ms) and indicated that an additional broad synthetic optimization exercise would have low marginal value. That observable would have been prospectively recognizable, but it alone would **not** prove >60% attribution at 2,048/63 or pass the host perturbation gate; therefore this is a local research-sequencing lesson, not an earned modification to the Discovery Engine policy. The strongest remaining question is actual mixed signed-fsmeta applicability in the public Reader, already owned by #808.

### Cross-platform CPU timer resolution

The original Windows primary-case `time.process_time_ns()` data take only five distinct values across 24 observations: 0, 15,625,000, 46,875,000, 62,500,000 and 78,125,000 ns. The **15.625ms CPU quantization** prevents fine-grained Windows CPU attribution, despite the nominal nanosecond API. Ubuntu/macOS exhibit finer measured CPU resolution. The frozen J24G65 inference explicitly uses high-resolution **wall** spans and an independent uninstrumented **wall** perturbation guard; Windows CPU must not be presented as an independently precise confirmation of the replay/footer split. No original acceptance rule was changed.
