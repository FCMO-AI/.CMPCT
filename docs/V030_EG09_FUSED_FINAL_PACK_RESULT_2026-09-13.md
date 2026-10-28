# v0.30 EG09 fused final-pack result — 2026-09-13

Status: **partial negative; mechanism speeds creation but exact EG08 identity not yet recovered**

Exact measured head: `a54796bf5feeaad22818e8122624f22a00a019a7`

Hosted run: `34763994176`

Receipt artifact: `10320025714`

Artifact digest: `sha256:31f088911bf39d4af8a2a115168793aea007a3f9e36773c381b4c35e40462282`

Scientific verdict: `EG09_FUSED_FINAL_PACK_BLOCKED`

Exact failed conditions:

- `all_complete_archive_identity`
- `all_zero_byte_delta`

All other preregistered EG09 conditions passed.

## What EG09 tested

EG09 preserves EG07's level-1 compression behavior for geometry probes, cold-stream requests and metadata, but intercepts V25 requested-level-19 ordinary final object-pack emission. At that narrow first-pass boundary it applies the exact EG08 `(3,6,12,19)` best-so-far ladder, including useful tie continuation and stop-at-first-worse, rather than first emitting EG07 and then reopening/recompressing the archive.

The referee required complete archive byte identity to EG08, not merely equal stored-byte totals.

## Result

Across the frozen eligible-nine surfaces:

- aggregate creation CPU ratio EG09/EG08: **0.9105197738139481x**;
- aggregate wall ratio EG09/EG08: **0.910078841012674x**;
- maximum positive RSS delta: **0 KiB**;
- strong verification passed;
- locality geometry remained identical;
- tail recovery passed;
- no confirmed per-workload CPU or wall regression was reported;
- but complete archive identity and zero byte delta failed.

Thus first-pass fusion is a real creation-efficiency mechanism, but the current narrow requested-level-19 scope does not reproduce all EG08 selected physical bytes. It receives no product/frontier promotion credit in this form.

## Leading causal explanation

EG08 applies adaptive effort to every non-hot physical pack after EG07 has finalized the archive. V25 ordinary object packs are emitted through requested-level-19 compression, but **cold stream packs** are emitted through requested-level-3 compression. The EG09 implementation intentionally left all requested-level-3 calls at EG07 level 1 because that same requested level is also used by geometry probes; globally changing it could alter grouping and invalidate the same-geometry claim.

The preregistered `docs/V030_EG08_COLD_STREAM_EFFORT_ATTRIBUTION_LOCK_2026-09-13.md` directly tests whether cold stream packs actually carry any EG08 selected-byte savings. If they do, this identity failure has a concrete structural explanation and the next Builder must distinguish final cold-stream emission from level-3 probes instead of widening the `zc` hook blindly.

## Score custody

No frozen Genesis score, composed-R4 score, v0.29 identity, 8x locality law, recovery/integrity rule, numeric version or ONE status changes from this result.
