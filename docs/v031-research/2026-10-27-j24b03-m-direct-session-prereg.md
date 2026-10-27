# J24B03-M — authentic direct-owner session economics (prospective)

**Date:** 2026-10-27 UTC. **Status:** PRE-RESULT scientific preregistration.
**Owner:** existing Phased3 direct-owner PR #609; no changes to Reader, Builder, format, benchmarks, or CI success thresholds.

## Decision fork

J24B03-P already measured a true +135.467 ns per 16-byte RAW range call (+37.94%) on signed 128-byte r24 direct members, with no absolute micro-veto. J24B03-A established three-host correct rejection of malformed physical sizes and RAW header offsets. Whether the guard creates *material complete-session* CPU/wall/RSS debt on a valid high-cardinality archive remains unknown. It is a different product-economics question, not a fourth variation of the hostile-size hypothesis.

**Question:** At 1, 4,096, and 65,536 valid S_BLOB logical owners referencing one genuinely stored RAW physical owner, does the candidate impose a meaningful complete cold-open + cross-member selective-read + close or strict-preflight regression over the authentic unchanged v0.30 Reader? A tiny micro win/loss does not answer this.

## Baselines, alternatives and source identity

- Historical, exactly main `80c358f8824ec1b20d349c92ed94c898090969b0`, separately installed as frozen-baseline.
- Candidate: current #609 source on exact executing HEAD. Reader/validator SHA-256, import path and physical archive SHA are checked per subprocess.
- Strong simpler control: leave the existing O(1) guard rather than introduce complex per-archive caching or skip safety for throughput. Alternative explanation: index decompression, pathname validation, process startup and scheduler noise may dwarf guard overhead.
- Same Builder-independent but genuine revision-24 wire, with authenticated duplicated index, one physical RAW block and N logically distinct regular-file rows. Same byte image for both arms. This probes legal dedup-heavy generic archives, not a compressed fixture identity exploit.
- ABBA ordering `baseline,candidate,candidate,baseline` repeated three times for each scale (36 fresh worker processes), separately measuring cold open, strict preflight, full session and CPU. Worker process startup is excluded; all Reader work and shutdown are included. `VmHWM` captures Linux process high-water RSS, or nullable elsewhere.
- Validity: every member queried once, returned length/hash/selected bytes checked independently; zero-length and EOF reads valid; N logical objects and exactly one physical block proven. All archive/source hashes, raw worker data, process identities and order retained.
- No change to previously frozen J24B03-H failed prediction. J24B03-A remains the security acceptance court.

## Frozen decisions (before measurement)

For N=4,096 or N=65,536, mark `MATERIAL_DIRECT_SESSION_DEBT` if **both** candidate/baseline median CPU and wall complete-session ratios are >=1.10 **and** both absolute median additional times are >=25 milliseconds; OR the median candidate process `VmHWM` is >=8 MiB higher than baseline. Separately mark `MATERIAL_DIRECT_PREFLIGHT_DEBT` if **both** CPU and wall ratios are >=1.15 and **both** absolute median additions are >=50 milliseconds. Otherwise `NO_PREREGISTERED_MACRO_DEBT_SIGNAL`. Record all observed numerical negative and positive movements, even below veto. The N=1 profile is a control, not a candidate-selection target.

No claim of parity follows from a non-veto result: this tests direct RAW dedup on one Linux host, not full workloads, Zstd/Deflate, extraction, mutable source attack, Windows/macOS performance, O215 chunk-open debt, or release benchmarks.

## Evidence and release boundaries

Prefer an independent stdlib referee recomputing medians and decision from raw observations without importing CMPCT or trusting harness summaries. Do not claim success until a source-exact hosted workflow actually passes. Failure or noise is preserved, not threshold-adjusted. Use signed r24 conformance/product-owner facts; historical releases and PR #569 remain unchanged. If the macro veto fires, hold #609 for architectural rehabilitation; if not, hand the bounded result to #569 owner while retaining direct-size correctness as the product priority.
