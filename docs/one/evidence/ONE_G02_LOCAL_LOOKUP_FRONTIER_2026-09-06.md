# ONE-G0.2 local lookup frontier — 2026-09-06

Status: mutable handoff for the current local-lookup carrying-cost campaign.
Experimental line: ONE-G0.2.

## Why this frontier exists

Native attribution showed the 64-entry local nomination ring performing approximately one scalar key comparison per input byte on mature measured rows. The purpose of this campaign is to preserve exactly the same local reuse decisions while reducing that creation-time bookkeeping cost. The ring remains authoritative until an accelerator survives both isolated and fused-observer gates.

## Terminal result 1 — tombstone/rebuild hash: reject

Authority: `docs/one/evidence/ONE_G02_LOCAL_INDEX_HASH_EXACT_RESULT_2026-09-06.md`.

- exact source `0cb00d4e23cc9d831d28258a745e3a44666608c9`;
- run `34008825904`, job `101420881402`, artifact `9981831540`;
- 93 semantic/hostile tests passed;
- exact lookup decisions preserved;
- aggregate candidate probes / baseline comparisons **1.047093x**;
- mature size medians **1.7243x, 2.2715x, 2.2700x** at 16/64/256 KiB;
- worst row **3.4387x**.

Cause: tombstone history plus saturation-triggered rebuild exported more control/probe work than the scalar ring. Reopening predicate explicitly excludes threshold/rebuild tuning.

## Terminal result 2 — backward-shift hash: real improvement, hold

Authority: `docs/one/evidence/ONE_G02_LOCAL_INDEX_BACKSHIFT_EXACT_RESULT_2026-09-06.md`.

- exact source `f5d2c4e5186f8ca9b882eafdd379ae3eb275d7dc`;
- run `34010841450`, job `101426268997`, artifact `9982406490`;
- 93 semantic/hostile tests passed;
- exact decisions preserved;
- aggregate candidate probes / baseline comparisons **0.127772x**;
- size medians **0.7006x, 0.6983x, 0.7188x, 0.8930x, 0.9323x** from 4 to 256 KiB;
- worst ordinary row **0.9394x**;
- fixed state **2.3333x** baseline;
- same-bucket hostile stream remained exact but exposed long-cluster work.

Interpretation: tombstones were genuinely causal. Removing them transforms the design from a large loss into a broad win. It still fails the frozen `<=0.90x` mature-size gate at 256 KiB and therefore is **not promoted**. No size dispatcher is allowed merely to harvest the favorable rows.

## Active Builder — compact fingerprint ring view

Frozen authorities:

- `docs/one/evidence/ONE_G02_LOCAL_INDEX_FINGERPRINT_VIEW_PREREG_2026-09-06.md`;
- `docs/one/evidence/ONE_G02_LOCAL_INDEX_FINGERPRINT_VIEW_HOSTILE_AMENDMENT_2026-09-06.md`.

Shape:

- authoritative 64-entry ring unchanged;
- 128-byte mirrored fingerprint view only;
- fingerprint is an already-available byte from the 64-bit Gear-state key, with no extra hash mixer;
- `memchr` rejects ordinary misses over one contiguous logical ring interval;
- full 64-bit equality remains the sole hit authority;
- O(1) maintenance: two fingerprint-byte stores per inserted slot;
- no tombstones, deletes, cluster repair, rebuild policy or size dispatch.

Hostile review caught that the inherited byte-pattern case named `cyclic_local_hits` did not actually produce Gear-key hits. Any source before the amendment is diagnostic only. The repaired source adds a native key-stream control with 64 live keys followed by 4,096 guaranteed hits, timed entirely in C with A/B-B/A ordering. A separate all-same-fingerprint hostile stream remains mandatory.

Promotion still requires the original hard gates plus hit-rich elapsed `<=1.03x`. If the compact view fails, the next allowed family is an explicitly SIMD/bulk full-key comparison or a different local-reuse representation, not another open-address policy or size threshold.

## Claim boundary

Nothing in this frontier changes ONE reader semantics, wire bytes, format, density, selective access, integrity, v0.29 authority or deferred-v0.30 authority. These are isolated native creation-time lookup experiments until a candidate survives fused-observer integration.
