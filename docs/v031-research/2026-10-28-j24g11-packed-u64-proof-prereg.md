# J24G11 — prospective packed uint64 negative-footer proof tier

Date: 2026-10-28 UTC
Status: FROZEN PREDICTION BEFORE READER EDIT; DRAFT RESEARCH ONLY. No merge, release, format/version, benchmark/policy gate or prior-source edits.

## Authority, boundary and nonduplication

Source parent is J24G10 PR #664 at exact `da5552d4f74113de1887fdad9683b433bb6e6cf2`, Reader Git blob `0a8a7afa036cb4988b80836bcbe550c3b5d0bb40`. Published `main` v0.30.0/r24 remains unchanged. Source-owned #664 retains disk-backed exact SQLite negative-proof semantics; #661 retains AP certificates; #650 owns original negative-cache remedy. This child alone experiments with a different bounded representation. No `CONCURRENCY_PROTOCOL.md` or `tools/discovery_claims.py` exists on inspected parent; preserve PR ownership and immutable historical controls.

## Primary question and causal hypothesis

On SHA-authenticated orphan footer ancestry above the 16,384-entry hot cache, is *exact sorted uint64 offset storage* a better **middle tier** than immediately opening an SQLite B-tree? Each distinct 64-bit offset occupies exactly 8 array payload bytes, membership uses C-level `bisect_left`, and all bytes stay in a fixed prospective 1 MiB packed budget. On overflow beyond that byte budget, retain original #664 SQLite fallback (not silently unbounded memory). Preserve the signed-u64 bijection and check boundary values 0, 2^63, 2^64-1; no probabilistic skips.

## Stronger controls and preexisting lower rung

- Stronger fastest control: unbounded Python set on same installed Reader, **not** shipping policy.
- Inherited bounded control: exact #664 SQLite spill, plus #661 arithmetic-run mechanism where applicable.
- Detached pre-prereg micro on this host, Python 3.13, N=16,400 positions: alternating dense median build/query ~1.2/14.6ms packed vs ~15.8/136.4ms SQLite for 32,802 queries, Python set ~0.2/1.6ms; packed raw payload 131,200B vs SQLite physical 159,744B. This is *not* CMPCT product or whole-process-RSS evidence. The original first probe had an unrelated signed-u64 SQLite query overflow and was repaired; retain that negative, do not conceal it.
- Alternatives: retain SQLite only (slower), increase hot Python set (unbounded RSS), Roaring-like containers (extra code + density tuning), bitmaps indexed by file offset (large sparse-universe burden), and approximate filters (unsafe false-positive risk).

## Prospective hosted court and kill conditions

Use the unmodified first-party Builder/Writer to create a real signed r24 archive, append SHA-valid invalid ancestry, and compare original #664 Reader vs child Reader **and** unbounded set on identical physical archive SHA, installed from exact Git source; instrument identical decoder call sites and alternate trial order. At minimum: N=16,400 alternating and irregular spacings, N=16,400 AP favorable control, N=1,024 independent footers, and actual `append_rename` valid transaction; include high-u64 membership and duplicate/neighbor/invalid-domain oracles, and a >1MiB tier-overflow assertion that preserves disk fallback/cleanup. All logical bytes, checkpoint, range reads and verify must remain exact. Preserve raw wall/CPU repetitions and independent audit when practical.

Predicted: above-cap irregular chains still require exactly N+1 decode attempts and recover old checkpoint; the packed tier avoids any SQLite file there; eligible packed payload is 8N bytes, with fixed <=1MiB tier cap. Median paired product wall should improve >=1.2x against #664 on irregular cases, while AP, independent and valid cases have <=25% slowdown. A strong control may still win absolute wall, explicitly account this as exported-cost debt. No general RSS or source-snapshot support claimed: per-chain `seen`/decoded `chain` still scale, and same-inode mutation invalidates negative-proof assumptions (#654).

**Kill/narrow** on any wrong content/footer/range/verify or membership, wrong 64-bit handling, skipped valid checkpoint, leaked proof file, new unbounded backing tier or unavailable safe fallback; narrow if hosted wall gain <1.2x or normal-case overhead >25%; reject product promotion absent peak RSS, temporary I/O, cross-platform and full same-runner gates. Contradictions are evidence, never evaluator changes.

Next decision: retain a bounded packed intermediate tier, retire it in favor of SQLite or Python set if fully charged economics lose, or mark ambiguous and measure. Even a success is a *cross-candidate proof-store* gain only: to bound total open resources, separately revisit per-chain materialization and mutation contract. No `STATE.json` edit without decision-changing source-grounded truth; no automatic discovery-policy change.