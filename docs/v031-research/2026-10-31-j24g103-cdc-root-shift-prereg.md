# J24G103 — one bounded shift-resilient representation falsifier (prospective O0)

Date: 2026-10-31 UTC. **FROZEN BEFORE ANY J24G103 CODE OR MEASUREMENT.** Research-only; no product/format/version/release claim.

## Current authority, ownership, and why one last attempt
Canonical `FCMO-AI/.CMPCT` released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/revision-24. Extend existing Phased1 scientific owner #879 from `1b9b3c4925e8a0ef160b1bde8cee7b0359b36c72`; parent #876 owns root-rebase custody; #869 owns publication protocol; #823 owns Reader; #574 owns Discovery STATE. No narrow duplicate open PR is known for content-defined physical block sharing. No write to those owners.

PARETOBONK frame review after J24G99/101/102: J24G99 rolling tails are the stronger simpler control for append-only; J24G101 demonstrated ~1.99x retained bases; J24G102 exact 4/16 KiB SHA-block model reduced two-version capacity to 1.062–1.115x **but fails on one-byte early displacement (2.005–2.035x)**. This task tests a genuinely different *boundary-placement* mechanism with a single cheap oracle. If it cannot survive a one-byte displacement or charges too much read/build cost, **retire the CDC root-rebase approach** instead of expanding COW parameter gardening. No more nearby chunking variants on a loss.

## Locked physical sources / inherited baselines
Use original GitHub Actions #41120248525, producer SHA `129edec976efe8bb604584517de39553487fec34`:
- Ubuntu ZIP #13007508236 SHA-256 `19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b`;
- Windows ZIP #13007244298 SHA-256 `c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab`.
Four pairs: 4096 and 8192 members each. Reuse immutable J24G102 `makepair` physical parser to check all 63 genuine signed DELETEs, index/record integrity and exact r24 terminal-root reconstruction. Compare the **same bytes** to J24G102 `priced` fixed-block 4/16 KiB control, direct full two-image copies, and historical J24G99 ~1.004–1.019x rolling-tail (different operation; do not call it equivalent).

## Hypothesis and fully charged information model
Use a deterministic streaming content-defined boundary (fixed SHA-derived 256-entry gear table and cumulative uint64 rolling fingerprint). Exactly two target average chunk sizes: **4096 and 16384 bytes**. For each, cut after minimum target/4 when fingerprint matches mask=target-1, or at maximum target*4; reset rolling fingerprint only at every cut. No data-dependent sizes, corpus identity, hand-picked mask, threshold tuning or oracle boundaries. Do not compression-encode chunks or exploit gifted decoder facts. Build SHA-256 keyed blocks; charge each distinct payload byte once, **44 bytes per distinct block** and **32 bytes per block reference + 64 bytes per root manifest**. Verify byte-identical reconstruction and independent hash/root-record tamper refusal. Compare same charge to fixed blocks.

Required perturbations: original physically valid checkpoint pair; one-byte insertion at offset 512 in the new root; one-byte insertion near its midpoint; one-byte deletion at offset 512; independent seeded random payload of equal length; and a 4096-byte aligned move control. Perturbations are *only byte geometry*, not valid CMPCT claims.

**Primary prereg gate:** for **all four** source-pairs and **both** target sizes, charged CDC `total/max(old,new)` must be <=1.25 in original and one-byte early insertion, and <=1.30 at midpoint shift/deletion. In original-only cases CDC cannot exceed same-size fixed block charged total by >15%. Any failure retires generic shift-resilient two-root CDC from this campaign; never adjust targets/masks to rescue.

**Strong simpler control:** the published r24 replay/Owned Reader already avoids physical root rebase, and J24G99 tail model stays below 1.019x for its append-only workload. Even a gate pass **does not authorize productization** until charged complete CPU/wall, writer materialization/write amplification, hash work, RSS, selective logical/physical reads, decode-unit amplification, GC, pinning, crash cuts, filesystem semantics, native portability and CAS publication can beat these alternatives.

## Cheapest evidence rung / falsifier
O0 exact Python representation model on same authentic physical sources. Measure warm monotonic wall and process CPU for constructing each whole two-root model in **three repeats** per arm, same host; report raw values and maxima (not cold Reader). Charge >=1 buffered pass over each full image for CDC vs fixed slicing; measure peak Python allocations in one separately labeled exploratory run when practical, no RSS claim. If CDC construct cost >10x fixed median on all four physical pairs for either size, treat as causal product debt even if bytes survive. No speed threshold is a promotion rule.

Independent referee must re-parse source and recompute ratios/chunks from scratch with differently structured code, reject at least three falsified receipts, verify the exact SHA of each source/old/new image and tamper negative. No lookups into benchmark fixture identity, no imported published Reader, no CI result inferred from local data. Source-controlled hosted run should retain original ZIP/receipt and exact-head. A runner/provider failure is unmeasured infrastructure, not a product loss.

## Decision and continuity
This is deliberately **one bounded final different-frame attempt** for the COW physical-root family, not a reason to keep optimizing one knob. PASS means O0 representation headroom only and immediately moves to strongest simpler product route; FAIL means retire CDC root sharing under this physical form, preserving contradiction. Do not modify docs/discovery/STATE.json, policy, original #879 prereg/results or any comparator/threshold. Preserve prediction and outcome in separate append-only evidence with exact source identity.