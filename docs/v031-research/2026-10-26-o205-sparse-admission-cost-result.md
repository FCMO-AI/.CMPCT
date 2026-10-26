# O205 — real high-E sparse admission economics; final decision record

**Research-only / no Reader repair, no format change, no release.** 2026-10-26. Owner O193 #521; correctness Issue #533; inherited native/Python differential O202 #539. Source baseline O193 `392112ce859db5a7f85be593c82d1cabc1f5131f`, `src/cmpct/reader.py` Git blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`; `src/cmpct/validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`. No product files touched.

## Evidence identity and chronological provenance

1. **Original prospective prereg** `cf00530b763daef9d7ca252177e06d701b31ddfe` precedes the experiment and sets four comparisons, 30-ms/16-MiB full-preflight and 5-ms geometry thresholds.
2. **Initial harness FAIL** run [40398297741](https://github.com/FCMO-AI/.CMPCT/actions/runs/40398297741), artifact `12688050989`: an instrument claimed Git worktree must be entirely free of untracked files despite the hosted workflow deliberately creating `o205-evidence/`. No admission cost was measured. Preserved as infrastructure negative. Bounded correction prereg [O205b](2026-10-26-o205b-receipt-directory-prereg.md) at `5a3b836cdf5cd114d1457293146308eee71b5dd2`.
3. **First complete, traced trial** run [40398621917](https://github.com/FCMO-AI/.CMPCT/actions/runs/40398621917), HEAD `bea7d6366f389977da415c7c2aeb9f7b39eddc64`; artifact `12686634336`, ZIP SHA-256 `206c7e1c47f1c4f8e596faa3d83e9219352fc8c18c197ceb909978b1750ebfdd`. Genuine A/B/C/D 8 processes/arm, but tracer perturbs timing heavily. The original result classifier is **ADMISSION_COST_FORK_AMBIGUOUS**, correctly preserved, not retconned.
4. **Prospective observer-effect control** prereg `d4d3707f4e82a1f336d0e8356c5c4be6b115bd0a` *before* modifying the instrument. Added 8 fresh **untraced** and 8 **traced** processes/arm; unchanged workloads, limits, archive, source, thresholds, validator, parser, and product code.
5. **Decisive hosted O205c result** [40399249715](https://github.com/FCMO-AI/.CMPCT/actions/runs/40399249715) on exact experiment HEAD `15a2db2cde26be4e9947794276b57337319cb893`, raw artifact **12687384417**, artifact ZIP SHA-256 `71b0d1bffb4ecf65815424d5a54621d8d32525af1bfabf67b42dadd121685afe`. Installed Reader identity and Git blob authenticated. All 64 worker observations captured. **Scientific decision:** `FULL_STRICT_PREFLIGHT_CHEAP_ENOUGH_FOR_NEXT_OWNER_INTEGRATION_TEST` (bounded to this profile).

## Actual build and source identity

One actual Linux Builder-created `S_SPARSE` CMPCT from a **4,294,967,296-byte logical sparse file**, **4,096 physical extents**, **16,777,216 host allocated bytes**; CMPCT archive **533,466 bytes**, SHA-256 `ed8376fa24a388497358466c47c1e5f655b91c06e9c64cc4610c38e668947243`. All four modes opened **the same original bytes**, in independent Python worker processes; indexed extent count **4096**, verified four physical 32-byte markers and a hole, authenticated installed Reader. Separate in-memory perturbations (unsorted extents, wrong declared length) were rejected by the deliberately limited oracle.

## Raw medians, *untraced* eight repetitions/mode, same process boundary

| Mode | Wall ms | CPU ms | Peak process RSS KiB |
|---|---:|---:|---:|
| A Reader open only | 2.287899 | 2.287649 | 54,632 |
| B preflight without blob headers + open | 14.993249 | 14.993860 | 54,632 |
| C full existing strict preflight + open | 19.404401 | 19.405124 | 54,632 |
| D in-memory geometry-only pass + open | 3.804197 | 3.804096 | 54,632 |

C minus A **17.116503 ms** and no resolved RSS difference. D minus A **1.516298 ms**. Both satisfy prereg thresholds for this measured high-E profile. Crucially, D is **not** the semantic/safety equivalent of complete preflight: it omits bounds on decoded index/transaction/recovery, blob headers, and other hostility/format checks. Existing full preflight is the strongest already-proven correctness implementation and now has bounded, modest untraced additional cost in this one scenario.

## Observer effect / negative knowledge

The initial all-`tracemalloc` eight-process/mode experiment measured medians A **14.206**, B **199.001**, C **226.415**, D **25.952 ms**, which would radically overstate production costs. Confirmatory 64-worker trial collected separately traced A **18.374**, B **272.799**, C **306.452**, D **34.185 ms** on the same genuine structure. Huge tracer effect on allocation-heavy strict preflight; **do not use traced timings for user-visible product latency claims.** Still not a formal cold-I/O or product admission benchmark.

## Critical residual custody boundary

**Cost viability is not correctness composition.** `preflight_archive(path)` opens and closes one descriptor; subsequent `CMPCT(path)` independently opens pathname again. In a writable namespace, `os.replace` between those two opens can change inode, so separate-path preflight success does *not* authenticate the Reader's admitted bytes. A separate local generic POSIX `open → replace → open` primitive reproduced changed device/inode and SHA; it was **not executed against installed CMPCT** and is not asserted as an exploited CMPCT bug. The owner must bind the strict admission to the **same opened source/in-memory effective index** with safe lifetime and mutation policy, without substituting a pathname double-open as a release security fix.

## Interpretation / strongest limitations

The **decision changed**: full already-existing preflight is economically plausible for the authentic high-E file; don't prejudge it as too expensive from source inspection or tracer-distorted timings. This does **not** authorize blindly running preflight at every open. Eight replications per arm shared warmed page caches, one Linux runner, one highly sparse profile, ~533-KiB archive; median peak process RSS is setup dominated and does not resolve <1-MiB deltas. Whole-system extraction, source changes during read, malicious huge indexes, cold open, journal recovery, portability, full CI, release parity, and same-inode source lifetime all remain open. No format/Reader/test evaluator changes; no release.

## Next decisive owner action

With #521/#533 owner permission, bind the existing strict geometry invariant to the **same actual Reader effective index/open descriptor**; run fixed O202 authenticated valid/invalid controls + true 4-GiB Builder sparse + retrieval/ZIP64 controls and compare real *source-bound* Reader A/B on identical input under cold/warm modes. Do not duplicate parsing without evidence, eliminate recovery semantics, modify frozen gates, or treat a research oracle as a product fix. If increased cost appears on large transaction histories or filesystems, measure and narrow. Shared Discovery STATE remains staleable and unchanged; this detailed scientific record + PR/artifact is authority.

**Counterfactual prospective discriminator:** measure product timing without allocation tracing *before* interpreting a preflight wall-time regression; compare traced/untraced as an explicit measurement-control pair in future allocation-heavy Python parser work. This one episode earns a **local measurement lesson**, not a normative Discovery Engine policy change.
