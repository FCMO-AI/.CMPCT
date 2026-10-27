# J24R05 — Shared sparse range reconstruction loop (prospective preregistration)

**Date:** 2026-10-27 UTC. **Research-only; no merge/release credit.**

## Source authority, concurrency and ownership

Canonical `main` release is v0.30.0, on-disk revision 24. This stacked experiment starts from J24R04c PR #596 exact `c83baa1868b24a3cc74373a495db938c224b4621` with Reader blob `cd85d54710205ce0ba3d5dcf401451643aed1814`. The original Reader is PR #569 `c5e13bb3fbb4cdade8b64246658ce7c7818de41f` and the logarithmic owner is PR #584 `70336307312b5b277f0885c0057d2cddab0aefc1`. Do not change any owner branch. A check of open PRs at entry shows #596 owns the dual-path same-surface implementation; this subordinate experiment is explicitly a different loop architecture, not a duplicate owner. `docs/discovery/STATE.json` is stale and separately owned by #574; no shared mutation. `docs/discovery/CONCURRENCY_PROTOCOL.md` absent from main.

## Scientific question

Can the small/large selector feed **one common reconstruction loop** instead of duplicating its body, reducing maintenance and preserving favorable large-extent asymptotics while improving the prior E=4 +5.514% measured slowdown? This is a simplification/falsifier of the two-loop architecture, *not* a new threshold. Read ranges and all invalid-input exceptions must remain exact.

## Mechanism and controls

For E<=4, use a direct iterator over the already validated extent list. For E>4, retain exactly the existing authenticated end-key `bisect_right` and iterate by index with constant auxiliary memory. Consume both through the same logical-byte reconstruction body. No persisted offset array, slice tail, extra decoding, full-file materialization, changed physical bytes, or altered validator.

Controls: source-exact #569, #584 and #596 Reader; same authentic O212 r24 archives and same 256-late-one-byte ABBA workload. Large-E should retain >=10x vs #569 and stay <=5% median latency overhead vs #584 on E=4096 and E=65536; E=1 and E=4 should stay <=5% over #569. The existing J24R04c E=4=+5.514% remains a **failed frozen experiment** whatever the new outcome. A 5% observation is a *research* criterion; official release gate separately requires both >5% relative and >3ms absolute. No post-hoc threshold change.

Alternative explanations: hot runner variance at tiny submillisecond scale, iterator creation overhead, generator/yield dispatch, implementation-specific cache effects. ABBA must compare installed authentic sources on same host and file bytes, with raw child repetitions preserved.

## Cheapest evidence ladder and kill

First run independent algorithmic micro under deterministic seeded extents (only preliminary, no product claim). Then original O212/J24R01/J24R04 tests with held-out E=2,3,5,8,16,37,129 and hostile geometry; exact installed candidate and historical SHA. Only after these pass, hosted 3-host semantic and 3-source ABBA. If E=4 still >5%, or E=4096/65536 exceeds 5% vs #584, or any bytes/exception differ, reject/narrow; no tuning by threshold. Watch full open time, memory, decoded bytes, publication and release gates separately; this mechanism claims none of their improvement.

## Counterfactual, complexity and exit

The observed J24R04 +5.514% and two nearly duplicated reconstruction loops are sufficient to justify ONE structurally simpler trial. If a shared iterator still misses, stop threshold gardening and pivot to different ownership/representation or retire this family as the next primary activation. Preserve negative receipts and hand off only a decision-complete result. Never modify the frozen original instrument to make a candidate green.
