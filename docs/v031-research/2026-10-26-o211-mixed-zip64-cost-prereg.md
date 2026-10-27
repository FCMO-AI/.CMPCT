# O211 prospective mixed ZIP64 inherited Deflate CPU ownership
Date: 2026-10-26
Status: PREREGISTERED BEFORE SCIENTIFIC INSTRUMENT / HOSTED RESULT

## Authority / scope
Source owner O193 PR #521 exact `392112ce859db5a7f85be593c82d1cabc1f5131f`; issue #551 O210 measured only raw Deflate reuse micro costs (2.26–11.95x) and explicitly withheld full-product credit. This episode does NOT implement a Reader patch or change any release, benchmark, format, frozen historical court or Discovery policy. O193 is unchanged. Active neighboring streaming and extraction PRs #552/#553 own different source.

## Primary decision question
On ONE real installed Builder-produced revision-24 archive containing a physically sparse >=4GiB logical member plus >=16 inherited `CODEC_DEFLATE` S_BLOB member streams discovered from genuine nested-ZIP provenance, how much of the *actual* unmodified O193 ZIP64 export CPU is attributable to writing those eligible small members? Is their total write+compression CPU share even large enough to support a material >=5% overall CPU saving by direct-stream reuse?

## Prediction / controls / falsification
Hypothesis: one huge member globally triggers the ZIP64 fallback, and unrelated, legitimately reusable Deflate members are recompressed through stdlib `ZipFile` rather than using existing physical streams. The per-member compressed `_ZipWriteFile.write` CPU of those eligible members is an **optimistic ceiling** on eliminable CPU; direct reuse must still pay verification/ZIP framing and may be smaller. Instrumentation may increase overhead, so preserve an uninstrumented genuine export control and repeat in alternating order in separate processes or report observed uncertainty.

Build one real Linux sparse file (~4GiB logical with many sparse extents) plus a deterministic set of >=16 1MiB content files, and ONE RFC1951 Deflate-9 ZIP of identical member contents so the ordinary Builder discovers inherited Deflate. Reject as INCONCLUSIVE, not a negative materiality result, if the ordinary Builder fails to select the required direct physical CODEC_DEFLATE majority or S_SPARSE source, source SHA differs, archive/index cannot be reopened, ZIP differs logically, or timed instrument cannot attribute per-member CPU. Source ZIP itself is a full-price extra member and must not disappear from whole-export accounting.

Measure complete export process CPU/wall, archive+ZIP bytes, all inherited `CODEC_DEFLATE` member bytes, total per-member `_ZipWriteFile.write` CPU, decoding/read_range ownership separately when available, max logical request and RSS. Include a Linux-specific actual 4GiB sparse host evidence witness; independently stream entire ZIP64 large member and all extra members through standard zipfile CRC/SHA. Keep raw trials and exact source/module hashes. Raw repeated controls may be noisy on shared CI.

**Decision:** if eligible small-member writer CPU constitutes <5% of total export CPU in all repeated genuine mixed-archive runs (after including profiler overhead), this corpus does not justify an expensive same-archive hybrid writer and O210 is narrowed to larger/more expensive mixes; do NOT falsely retire the entire family. If >=5% materially and stably, proceed to an owner-coordinated, **same-archive fully authenticated hybrid A/B**, charging all storage, verification, startup, I/O and RSS before product credit. If noisy/ambiguous, do not cherry pick repeats. Neither outcome justifies a parallel product Reader implementation.

## Strong alternative explanations
The 4GiB giant member compression dominates CPU; source ZIP member export overhead might dominate unrelated small-file recompression; Builder may prefer another codec; possible native direct Deflate stream eligibility may not exist for the chosen content; timed proxy may alter order/clock accounting. A raw Deflate microbenchmark or ordinary ZIP-only synthetic test does not prove total ZIP64 value.

## Hard safety and cost boundaries
No format/reader/codec/evaluator/promotion modification; complete SHA+CRC of readback, exact installed source, no entrusted customer files. Unmodified exporter may have prior known correctness/security debt; this experiment does not repair it. Files are synthetic and disposable. Resource budget <=4GiB logical sparse, ~64MiB extras; bounded 1MiB ZIP range requests. No unearned portability credit for Ubuntu-only result. Scientific metrics are not current published release parity evidence.
