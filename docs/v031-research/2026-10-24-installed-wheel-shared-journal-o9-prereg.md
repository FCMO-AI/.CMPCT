# O9 preregistration — installed-wheel prewrite Reader × shared bounded signed journal replay

**Date:** 2026-10-24 (UTC). **Status:** FROZEN BEFORE PRODUCT CODE EDIT. **Credit:** integration candidate only, not released.

## Source authority and independent owners
- Released floor CMPCT v0.30.0, format revision 24; active unreleased development v0.31.
- Parent [O3 PR #361](https://github.com/FCMO-AI/.CMPCT/pull/361) source `bf09afa516024e2503143189017a6931fc4947d0`: installed-wheel three-host signed-symlink court + receipt fail-closed. Preserve **every** byte of its Reader outside `_index_from_footer`, and preserve v0.30 release lock/format.
- Bounded replay owner [O7 PR #358](https://github.com/FCMO-AI/.CMPCT/pull/358) source `2c5334392c57f9c0f685c3751712acf0e242efae`, Reader Git blob `6de2edcf5b804e224a1c651ca77361af5667dc2e`, validator Git blob `2bb3f53c918ae93efb105364e2b93ea46aeca034`. Independent cold-cost [O8 PR #362](https://github.com/FCMO-AI/.CMPCT/pull/362) measured 4,096 journal-rename fresh-process whole wall 343.044→94.447ms (3.632x) with +1,090KiB/+4.09% Linux peak RSS; 512 operations only 1.019x whole-process. These are prior separate-source research observations, **not** O9 results.

## Primary question / best competing actions
Can the O3 exact installed-wheel, Python/Rust MessagePack, signed-path and hardlink safety stack coexist with O7's single indexed transaction-replay owner without regressing valid signed journal semantics, checkpoint opens, installed safety, or r24 performance? Compare with (A) leave separate proven implementations (safe but continued quadratic Reader replay), (B) duplicate a new Reader index (excess code/semantic drift), (C) surgical reuse of O7's proven `validation._apply_delta` with its bounded positional index and lazy Reader import (selected). Do not graft entire `reader.py` or `validation.py`: that would discard cross-owner guarantees.

## Hypothesis and falsifiers
- Preserve same signed source/physical r24 bytes, exact final indexes, legacy first-match put/rename and all-matches delete, sorted per-generation rows, malformed-op fail-closed, open/close resource semantics.
- Preserve all O3 installed-wheel signed unsafe negatives across Ubuntu/macOS/Windows and physical POSIX safe symlink; preserve 15 CPython jobs, metadata parsing, recovery/hardlinks/nested MessagePack, zero-byte size release rule.
- The smallest code change is owner-identical `_apply_delta_indexed` / `_apply_delta` graft with `heapq` import inside current validator, and owner-identical lazy `_index_from_footer` graft inside current Reader.
- The original source-exact O7 genuine authenticated journal/checkpoint unit court and 10,000-operation reference oracle must execute against the **new integrated Reader**. If any safety/test/parity or source identity difference occurs, preserve failure; do not weaken checks.
- Benchmark whole-system create/extract/open/startup/memory before promotion. Inherited O8 numbers may justify the integration attempt but cannot confer O9 performance credit. The official historical O3 performance FAIL (3 create regressions at source 1810a144...) remains real; do not suppress it.

## Evidence ladder, decision, carrying cost
1. Review exact owners and nonoverlapping method boundaries before editing (complete).
2. Preregister this document before code changes (this commit).
3. Land minimum source-exact graft and import unchanged owner adversarial tests.
4. Run independent authentic journal semantic court plus inherited installed-wheel safety and exact-head general/native/fuzz/CI parity; no merge on regressions.
5. Later quantify integrated cold-process and high-water RSS against parent source; if improvement fails or temporary replay indexes export unacceptable overhead, narrow/retire integration.
6. Additional responsibility: two product-file changes add one lazy import and one optional operation-local positional index. No format/version bump or release.

This O9 branch owns only integration; never overwrite PR #358, #361 or other agent branches. Current discovery STATE is older, staleable research navigation, not a lock. The official performance benchmark remains unchanged.
