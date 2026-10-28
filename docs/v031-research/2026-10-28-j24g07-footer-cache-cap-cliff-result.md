# J24G07 — Authenticated orphan footer chains exceed negative-cache work budget
**Date:** 2026-10-28 UTC. **Science / source-exact installed product behavior, not a product fix.**

## Identity, preregistration and source ownership

- [PR #655](https://github.com/FCMO-AI/.CMPCT/pull/655), branch `agent/phased2-v031-j24g07-footer-cache-cap-cliff-20261028`, based on immutable owner #650 at `10a6bc150cfa0ceb8608ee826dc09650ca3f4e3d`.
- Preregistration **before instrument**: `fd4a35e043e26e28741182e657f215975295bb29`.
- First exact experiment source HEAD: `149ae20f2a5385f2acc5a71f2c675739cbb1e738`; tested Reader blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`, same first-party Builder blob as owner #650. No product/validator/format code changed.
- [GitHub Actions #40644405689](https://github.com/FCMO-AI/.CMPCT/actions/runs/40644405689) **SUCCESS**, Ubuntu 24.04 / installed genuine Python 3.11 candidate source. Artifact id `12796613297`, ZIP SHA-256 `db51db395fbebc7729f31e65798ea6b21d714fd6944d99b3bb1fb040503c1c29`, files include source receipt and result-bearing `court.json` / `court.log`.
- Original authentic Builder archive: **970 bytes**, SHA-256 `f728d41f460af615ac25fe01e70c47226d114250c296775450cdcb9d0cd7e316`; logical member SHA-256 `e5f012a019b3ff6810235ee4c13425670701dcd9859005ecbe1fe811f0b8daef`; selected Builder checkpoint **902**, depth **0**, in every test (including hostile tails). Two full independent executions per case, real `read` / `read_range` / `verify`, direct actual decoder call instrumentation.

## Preregistered prediction and actual measurements

The candidate only caches all failed ancestors when `len(known_bad)+len(seen)<=16384`; if an initial chain exceeds that, *none* of it is added, yielding repeated long replays. For N>M=16,384 predicted `C=(N(N+1)-M(M+1))/2+M+1`; for N<=M `C=N+1`. The exact prediction held at both measured N and all controls:

| Same-source tested input | Physical archive bytes | Real decoder calls | Median open/read/range/verify wall | Median process CPU |
|---|---:|---:|---:|---:|
| Linked orphans N=16,384 | 1,328,074 | 16,385 | **123.286 ms** | **123.278 ms** |
| Linked orphans N=16,400 | 1,329,370 | **278,665** | **1,844.992 ms** | **1,844.756 ms** |
| Independent flat SHA-valid orphans N=16,400 | 1,329,370 | 16,401 | 113.596 ms | 113.560 ms |
| Equal-byte no-FMAGIC tail | 1,329,370 | 1 | 0.795 ms | 0.797 ms |

Changing **only 16 extra footer records (1,296 bytes)** near the threshold increased real decoder calls by **17.007×** and observed full-operation median wall by **14.965×**. For the same physical file size, linked versus flat SHA-authentic orphan tail wall was **16.242×**; versus equal-byte no-magic tail **~2,319×**. All logical bytes/verify/fallback checkpoint stayed correct. Changes are in *recovery work*, not in compression, archive creation or user logical content. This is not a measured full-system performance/release benchmark, no geographic transfer and no peak RSS data.

Exact physical SHA-256:
- N16384 linked: `180c3c276c6d56d5f40795f85678bf68f9b09a8a92436db3996b5bdbf83cc032`
- N16400 linked: `ed621d9b085260ec68a31211e50f2eaa9783faa488d2302b25fc282a76b56d98`
- N16400 flat: `a84c520993c310b98d41125ed8e88009d59532f2bb732988c41c21d3a2d523db`
- N16400 no-magic: `9d10b48b2a3e6e9ad43576323db6d05a9a5a10cc1f047636464683a93a1d8096`

## Product boundary, alternative explanations and next decision

The predicted call counts and 15× wall-step reject the simpler explanation that only filesystem scan bytes are responsible: same-size flat authenticated footers require near-linear work, and no-magic tail requires one decode. The original J24G04 deliberate 256-footer test cap was retained untouched; this separate research instrument only extends to N16,400. The experiment uses a SHA-authentic invalid appended tail (not forged metadata hashes) following an authentic valid checkpoint. Published v0.30.0/r24 and candidate #650 source are unchanged.

**Important API distinction:** the separate `src/cmpct/validation.py` `ParserLimits.max_delta_depth=128` belongs to explicit structural preflight; the ordinary `CMPCT(path)` reference Reader does not call preflight by default (as stated in `docs/HARDENING.md`). This experiment therefore measures the ordinary Reader *recovery scan*, not successful strict preflight admission of 16k signed deltas. The latter should be investigated separately. It would be misleading to claim the preflight limit mitigates this ordinary-open CPU work without actual integration.

**Decision changed:** the #650 negative-cache candidate **bounds retained positions but does not bound attacker-controllable replay work**. Retain its legitimate 103.71× N256 static gain as a seed; do not promote it as a globally bounded recovery mechanism. Need an explicit memory *and work* bound preserving older checkpoint fallback and exact latest-generation selection under supported immutable sources, plus a supported mutable-archive contract informed by [J24G06c #654](https://github.com/FCMO-AI/.CMPCT/pull/654). All proposals must honor release semantic/format/old-reader baselines and avoid threshold tuning. Do not turn SHA-authentic but invalid suffix into a silently accepted latest generation.

**Self-critique:** two measured repetitions on one Github Ubuntu host, no OS distribution parity, RSS sampling, full process startup, projected 17k+ cases, independent generated archive-byte custody or full release matrix. The wall ratio is reproducible within this narrow two-repetition case and consistent with decoder call count; it does not prove remote exploitation or general attacker access to local archive modification. A valid Writer generally appends rooted generations; our orphan grammar is hostile malformed-tail input.

## Discovery Engine / coordination

Primary falsifiable question yielded a decisive **confirmed** outcome. No conflicting ownership: separate source-locked scientific child, original owner #650 untouched. Same-repo and separate scientific #654 mutation frontier preserved. Counterfactual: inspect both *retained memory* and *work done before cache admission* at a bounded-cache threshold; a five-line source read predicted the cliff before any expensive run. This is a prospective useful investigation heuristic, but does **not** yet earn modifying Discovery Engine policy or `STATE.json` from a single episode. Next simplest unclaimed experiment: test whether a bounded progress certificate can guarantee work without unbounded per-footer facts; specifically contrast source-authorized invalid chains versus chain-depth safety/admission under normal open, and verify no weaker recovery semantics.
