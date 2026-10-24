# O10 preregistration — bounded physical extraction vs O7 all-member materialization

Date: 2026-10-24
Status: **PREDICTION FROZEN BEFORE IMPLEMENTATION/MEASUREMENT**.
Source-exact parent: `FCMO-AI/.CMPCT@030bd50aff682592f67eba1dc5376b83bfe83fae` (draft PR #327), based on native PACK owner/batch security composition PRs #325/#326. Public released v0.30.0 / physical format r24 are untouched. This independent evidence lane does not modify or claim ownership of any native product/Builder/Reader code or the O7 evidence client.

## Question and baseline
O7's real public C test consumer preallocates *every logical regular-file payload* as `Item.bytes` before read or publication, despite a per-member <=16 MiB limit and <=4096 entries. This makes aggregate output heap demand proportional to the total logical tree, with a theoretical ceiling of 64 GiB exclusive of native indexing, batch buffers and overhead. O7 was expressly root-level synthetic evidence, not a secure or bounded general-purpose extractor. The new question is whether an independent public-ABI single-file-at-a-time, 64-KiB-range streaming client can reduce peak RSS substantially on **same archive / same source / same SHA-256 output** while preserving feasible wall/CPU and refusing pre-existing destination symlink leaves without following them.

## Cheapest decisive comparison
Baseline: unchanged inherited `tests/native_pack_consumer_o7.c` in **serial mode**, with its eager all-entry allocations, exact same ABI/source package. Candidate: **new independent** small C root-only streaming *research* consumer using `cmpct_entry_read_range` with a fixed 64-KiB buffer and POSIX descriptor-relative `openat(O_EXCL|O_NOFOLLOW)`. No private Python index access. Both source archives produced exactly once per cohort with canonical `Builder(..., workers=1, reproducible=True)`; every output compared against independently calculated original per-member SHA-256. Same runner/build, repeated alternating ABBA scheduling, record raw per-process wall, child CPU, peak RSS. Prefer random high-entropy `.bin` files for the first comparator because RAW selective reads avoid codec-complete repeated-decode semantics and show aggregate memory behavior without a group admission confound. Test at least small / medium / larger aggregate output; if available, also run a pack-friendly `.txt` control to quantify the time debt of subrange decoding.

Predictions: O7 baseline memory increases with total payload (likely multiple MB per cohort), while streaming RSS remains approximately bounded for similar entry counts and archive structure. Even though O7 serial is not a shipping extractor, comparison should reveal **test-consumer architectural debt**, not a CMPCT distributed product speedup. Streaming may be slower for Zstd S_PACK due to repeated complete decompression; keep that negative. No conclusion about physical SSD bytes, durability after power loss, Windows portability, symlinks/hardlinks for general tree or full-file authenticated RAW contents from per-range reads.

## Adversarial controls, kill/narrow law
- Assert candidate returns nonzero and leaves an external symlink target untouched if destination leaf already exists as a symlink. Do not grant O7 safety credit or claim arbitrary tree security.
- Reject non-root-level paths, invalid lengths, oversized logical totals, unsupported file kinds beyond the corpus; do not weaken native validation or bypass independent SHA verification.
- If streaming RSS is not materially lower on >=16 MiB output, narrow/retire the memory architecture hypothesis. If corrupted outputs pass independent hashes, fail the experiment. If performance suffers, retain the speed debt honestly rather than quietly changing the corpus.
- If the source changes during extraction, per-range reads may observe different states and lack whole-file logical atomicity: **not a verified snapshot or release-safe materializer**.
- Preserve all raw repetitions; never compare process-start-inclusive wall to library-only baseline; do not extrapolate full-product performance from this research client.

## Decision unlocked
Choose between (a) keeping eager-O7 solely as a performance instrument and designing a product extractor with aggregate RAM budget + bounded per-owner decode/staging, (b) adopting streaming as a productization seed for RAW/fallback only with a strict integrity+atomicity contract, or (c) retiring this route if host evidence does not support material headroom. No version, format, benchmark threshold, frozen comparator, research policy or canonical `docs/discovery/STATE.json` mutation in this independent lane.

**Evidence tier:** hosted exact-source C ABI A/B + hostile filesystem-control research. **Release credit:** zero until real platform/format/semantics/conformance/performance gates pass.
