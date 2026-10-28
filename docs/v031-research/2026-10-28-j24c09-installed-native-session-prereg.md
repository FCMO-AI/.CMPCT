# J24C09 — installed ABI3 Reader full selective-session economics (prospective)
Date: 2026-10-28 UTC
Status: PREREGISTERED; RESEARCH / NO PRODUCT MERGE OR RELEASE AUTHORITY

## Exact source and ownership
Stack on J24C08 #641 at `a639570c1e9f9b36decae3893265be74a6d185b0`. The original S_CHUNKS scanner, positive-only fallback, Reader, validation, optional extension build, original tests and frozen release gates are immutable for this court. Parent sources must match Git blobs: Reader `9bca5d1047f9c78984b945d7ca90e3149fe429ab`, admission `432e86f73f3f1751c04ccbb0e45858c18531da1d`, scanner `308598c42f2060a93d8c41ae8733faf4f18ec968`, setup.py `676c156740ead7c0673e16f9f9b9f47b5704bd8a`. No edits in #641 or other operator branches.

## Question
The previous J24C08 installed-wheel court measured 10.98–14.98x constructor gain at 65,536 references; its whole-product wall-time significance is unknown. What survives when one actual public Reader session includes opening, listing, repeated selective reads at three distinct logical positions, close, and (only on a small bounded profile) full read and strong verify? Does O(N) scanning during range reads consume the constructor win?

## Prediction and competing explanations
In a 65,536- or 262,144-reference one-owner authentic revision-24 archive, ABI3 still produces at least 1.5x median **whole selective-session** wall speedup versus the unchanged strict Python validator, with no >8 MiB observed RSS increase on platforms that support measurement. Stronger negative: if both arms give byte-identical answers but net gain is <1.5x at either cardinality, the accelerator's gain is *not yet product-class* under this workload; optimize/read-across representation or admit a split workload policy rather than reporting constructor speedup as end-to-end. Alternate explanation: range replay scans consume most session time; distinguish using separately reported open/range/full-read phases.

## Controls, workload and limits
- Same noneditable wheel, same installed Reader/ABI and identical input bytes in both arms. The **only** control change is `cmpct._chunk_admission._scan_refs=None` in the strict arm, before any Reader initialization. Native arm uses the real product path. No other monkeypatch.
- Independently generated, signed Builder-free revision-24 fixtures from unchanged O215 generator with physical RAW owners and authenticated indexes. Profiles: (4,096 refs, 1 owner), (65,536,1), (65,536,256), (262,144,1). A file's logical bytes are exactly the concatenation of its referenced owners.
- One source-pinned installation per host. Ubuntu 24.04, macOS 14, Windows Server 2022; Python 3.11. A/B/B/A and B/A/A/B cycles with 3 cycles per profile (12 fresh workers, 6 per arm), 3 timed sessions per worker. Each session: open, list, six separate exact 16-byte ranges (two each at beginning, middle, end), close. Only the small 4,096-ref case also performs full read and strong verify; do not invoke potentially O(N)-futures full read at 262,144 refs merely to fill a matrix.
- Record separate wall/CPU for open, list, range and total, process wall including startup, high-water RSS where supported, complete archive/stored/logical bytes, actual output digests, native-module availability and real invocation counts. Record raw samples and repeated process-level variance. Absence of an OS RSS metric is **unknown**, not zero.
- First independent test must establish every read equals the exact signed logical slice. Source and fixture hashes must agree between arms. No per-profile discard, outlier trimming, cross-host averaging or mutation of historical comparator/threshold.
- Admission/memory/no-regression cannot be inferred from the microbenchmark alone. A whole-product official release benchmark, recovery, extraction, update, cold open and adversarial read rights remain separate product gates.

## Decision / kill
A science-positive result requires both one-owner large profiles (65,536 and 262,144) >=1.50x median complete selective-session wall with valid source/semantic controls and no measured RSS increase above 8 MiB on hosts where RSS is available. If one ratio fails, classify `SELECTIVE_SESSION_GAIN_BELOW_PREREGISTERED_FLOOR`. If proof fails, `EXACTNESS_OR_SOURCE_CUSTODY_FAILURE` and reject claim. If RSS unavailable, decision is explicitly provisional for that host and memory is unmeasured. A relative win in constructor is never a substitute for a total-session win.
Do not change the rubric after seeing the result. Favor smaller/faster control if native carrying cost is not repaid. Do not deploy, merge, release, change format revision or edit Discovery STATE; preserve both positive and negative raw results.

## Handoff
If CI jobs remain pending, preserve run/source identities and continue another safe lane. Subsequent phase should use this decision to prioritize range-index architecture versus optional scanner distribution, not enumerate nearby microoptimizations.
