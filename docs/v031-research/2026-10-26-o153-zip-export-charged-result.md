# O153 result — charged, source-exact ZIP publication (2026-10-26 UTC)

**Classification:** completed hosted research / convergence decision support, **not** a product, release or general-performance win. **Original preregistration:** `d4e801accf46a34f79f3b4c348cb48eb0e2f00f3`, committed before the oracle/workflow or observations. **Measured O153 HEAD:** `ffb1d57343c9ab705e490d56d98921a1d8449668`.

## Direct source and execution custody

Original source O140 [#488](https://github.com/FCMO-AI/.CMPCT/pull/488) `d8b69758dbcbb66fe28fa7cf59598916df160d2d`; staged alternatives O149 [#492](https://github.com/FCMO-AI/.CMPCT/pull/492) `ca01d885fedc8ffc343b9c3c624eddd134158452` and O150 [#491](https://github.com/FCMO-AI/.CMPCT/pull/491) `48bbb41661f8b19d369c50b06bec1018cd4400e9`. All three fetched as exact Git worktrees **on each same CI runner**, independently installed outside the instrumentation checkout and verified against the actual Reader Git blobs `e46e6121`, `496e70bd`, `f38662c8`. Shared O140 Builder Git blob `663ef092`; two exact original-Builder r24 archives per host. No regenerated per-engine input, no modified Reader/Builder, release gate or frozen controls.

**Hosted GitHub Actions:** [40274953708](https://github.com/FCMO-AI/.CMPCT/actions/runs/40274953708) on `ffb1d573`; Ubuntu 24.04 **SUCCESS**, macOS 14 **SUCCESS**. Each ran 84 fresh-child observations (two families × absent/existing regular ZIP destination × seven rotating balanced blocks × three Readers) with an independently audited JUnit-free raw receipt court. **168 observations total**, all exact ZIP member reconstructions and per-family full ZIP-byte SHA-256 equivalence. Raw JSONL, every sample, host/dependency/source identity and summaries remain in immutable CI artifacts:
- Ubuntu artifact **12629324300** (raw 84 rows, summary, source, host).
- macOS artifact **12629239453** (raw 84 rows, summary, source, host).

## Identical-input and byte-exact controls

| Family | Original CMPCT archive | Original archive SHA-256 | All exported ZIP bytes | ZIP SHA-256 |
|---|---:|---|---:|---|
| 96 tiny files | 2,342 B | `83c23968456e98fd0420ec28c173e5a662228bd40331e77379508f0649a50f2e` | 14,126 B | `9647938d38c06ac71e009a20f3e3836cc7a0fcbfdca990be77d6d06ac1a7ba13` |
| 2 large mixed files | 4,198,938 B | `f2be88f819d56e790d5ef5f79761eeab7d21ce978369f0d91d125a5548c668f9` | 4,206,769 B | `c00720f925f61ed6b6c6379c0c7af6c8e25ec95600b581d137665765c950ae94` |

All candidate ZIP SHA-256 hashes matched the exact direct baseline within each scenario; independent Python `zipfile` verified all members against source-file hashes and reported no damaged ZIP. **This does not imply identical output-filesystem semantics.**

## Measured library-only export wall — median milliseconds of 7/engine/scenario

| Host | Dataset / destination | O140 direct | O149 staged | O150 staged |
|---|---|---:|---:|---:|
| Ubuntu | tiny / absent | 2.358 | 2.626 | 2.574 |
| Ubuntu | tiny / existing | 2.428 | 2.643 | 2.609 |
| Ubuntu | mixed / absent | 134.371 | 133.640 | 133.743 |
| Ubuntu | mixed / existing | 133.618 | 133.309 | 133.796 |
| macOS | tiny / absent | 1.942 | 2.453 | 2.445 |
| macOS | tiny / existing | 1.984 | 2.353 | 2.334 |
| macOS | mixed / absent | 130.505 | 130.412 | 139.482 |
| macOS | mixed / existing | 134.623 | 134.275 | 144.190 |

**Positive:** staging does not obviously double successful ZIP export work. On Ubuntu, both staged large-file medians are within roughly 1 ms of direct O140; process-output block counters show the same 8,224 OS blocks per large export across engines, but this metric is **not** proof of equal physical/durable bytes. Library CPU on Ubuntu also remains close; fresh-process wall includes startup and is reported separately in artifacts. Peak process RSS was roughly 25 MB (tiny) or 51 MB (large) on Ubuntu; compare raw per-sample figures rather than interpreting process RSS as incremental staging allocation.

**Real measured cost:** on Ubuntu small-file exports, staging adds about **0.18–0.27 ms** (roughly 7–11% of ~2.4 ms), consistent across the seven paired blocks, but **below the absolute 3 ms promotion red threshold**. It is an architectural extra-path cost, not a release-blocking conclusion.

**Strongest adverse observation / contradiction:** on macOS O150's large-output medians appeared **6.88%/7.11% slower** than O140 (both cross the repository's local 5% + 3 ms numerical discriminator). However, the **actual block-paired changes oscillate in sign**, spanning approximately -25.7 to +19.2 ms (absent) and -12.9 to +24.8 ms (existing). O149 likewise shows high per-block variance. This is **ambiguous host noise / potentially real source difference**, not an established product regression. Do not cherry-pick the median or grant O149 a confirmed cross-host speed win. If this becomes release-decisive, replicate on a quieter controlled runner while preserving exact code/input and all raw samples.

## Physical semantics and limits

- **Absent output mode under umask 022:** O140/O149 **0644**, O150 **0600**; source-exact confirmation of independently obtained O151 evidence, not a new discovery.
- **Existing regular output inode:** O140 **preserves** inode on success; O149/O150 **replace** inode. The old hardlink identity may be retained at a different pathname. Existing 0644 regular destination remains 0644 for both staged candidates in this court.
- No unpublished staging residues were observed in any of 168 successful exports.
- Linux `ru_oublock` was 8,224 for each large success; macOS reported 0 in this hosted run. Neither metric measures peak temporary-file allocation, flush/fdatasync durability, write amplification at the device, or filesystem crash consistency.
- The full ZIP content is still O(output bytes) as a temporary file while stage-building; this bound is architectural, not an instrumented physical peak. No output near ZIP64 >4 GiB, hostile namespace race, symlink behavior beyond inherited O151, ACL/xattrs, network filesystem or Windows semantics tested here.
- Results are a focused **successful ZIP-export** economics court; O143's original failure negative, O149/O150 failure-atomic positive courts, generic tests and official parity remain separate.

## Decision and counterfactual

**Primary question:** whether either staged writer is clearly Pareto-worse in measured successful ZIP economic cost. **Answer:** no robust large-output cost defeat established; tiny-output relative overhead is reproducible but sub-threshold in absolute units, and macOS large-file timing is explicitly ambiguous. **No clean product winner on timing alone.** The actionable differentiator is output semantics: O149 preserves the original umask-derived 0644 absent-output mode, whereas O150 changes it to 0600. Prefer **O149 as the semantic-compatibility integration candidate** *if* its other inherited security and failure-atomicity gates remain valid; this is a source-limited engineering recommendation, **not** permission to merge.

O151 had already shown full ZIP parity for one small vector; O153's distinct contribution is the same-runner two-family **charged CPU/wall/process/memory/physical-output evidence**. Cheap counterfactual: this A/B/C court could have discriminated economic debt before opening two competing writer implementations; future sibling candidate conflicts should be resolved with one same-runner charged control and an explicit compatibility contract before parallel product rewrites.

**Discovery policy:** unchanged. `docs/discovery/STATE.json` not edited because it is a staleable centralized index with an independent reconciliation owner; exact PR/artifact receipts outrank it. **Concurrency:** overlap recognized (#491/#492/#493); no other owner's product code or branch modified. **Next highest leverage:** owner-level O149/O150 deduplication + deliberate output mode/symlink/hardlink policy; then original failure-court integration and frozen release-parity. No further nearby ZIP timing parameter tuning without decision-changing evidence.

**Exact-head truth:** measured workflow **2/2 SUCCESS** on `ffb1d573`; product source unchanged; original broader generic/release gates are not promoted by this scientific result. **Release credit: 0. Merge: NO.**
