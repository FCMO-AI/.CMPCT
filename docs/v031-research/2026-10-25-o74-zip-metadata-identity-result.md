# O74 — Held-out ZIP metadata-identity collision: decisive result

Date: 2026-10-25 UTC. **Scientific decision: FULL_METADATA_COLLISION.** This is a bounded negative for unsafe *metadata-as-proof* identity, **not** a demonstrated current CMPCT vulnerability, better compression ratio, change to shipping software, or release authorization.

## Prospective source and chronology
- Scientific parent O71 #427 exact HEAD `330a1fa1c642d4bd4ddf2a1bd6cadd22b94cc19a`; product Builder blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`, codec blob `dc3446b0eed82edfba9380e3885a20aa45577899`.
- Prediction registered before experiment at `4c1afe71e1a61979f4e36809443f7ecd269e497d`, `docs/v031-research/2026-10-25-o74-zip-metadata-identity-prereg.md`.
- Exact **result-bearing** scientific and genuine installed-product HEAD `bc49a4fc8740a0bdad54335c893e906446460a49`; experiment source blob `6542913a4d6169bbbe291197750363e7eae381fc`, workflow blob `aad8d5f17223181ac754cc418dde6589114bff40`.
- Hosted [O74 scientific Actions #40183967450](https://github.com/FCMO-AI/.CMPCT/actions/runs/40183967450), job `121140715792`: **SUCCESS** on CPython 3.11.17 Ubuntu 24.04.
- Original [artifact #12594769176](https://github.com/FCMO-AI/.CMPCT/actions/runs/40183967450/artifacts/12594769176), GitHub-uploaded ZIP SHA-256 `f8e0a30cdbf7507df12fb50d27b708cea1fbbe5c43870e5c4a9bb91d7f40294f`. Contains JSON for stdlib and authentic installed CMPCT, source/Builder/codec blobs, workflow raw logs and SHA receipts. This document is added *after* measured HEAD and cannot borrow another experiment without reexecution.

## Actual paired ZIP observations

Two physically **distinct** authentic stdlib single-member Deflate ZIPs:
- Full ZIP bytes: **65,676 B each**; source expanded bytes **65,536 B each**; Deflate stored stream **65,556 B each**.
- Member name `payload.bin`, Deflate method 8, flags zero, CRC32 **`a13df364`**, sizes, date, attributes, offsets and all other `ZipInfo` fields checked are equal.
- **Entire local ZIP header (before compressed stream) identical** and **entire central-directory + end-of-central-directory tail (after stream) identical**. Sole differences reside in compressed stream bytes.
- Expanded SHA-256 A: `78ef4a6de2837adf96d2ade9f4c9ad14b248bb8d3f051e465b1b4f5f5e66b7f5`.
- Expanded SHA-256 B: `4f6ce368f1a1077d85df3f420a41b2a539f0d037fff9cf39b8f8949fb398d094`.
- Complete ZIP SHA-256 A: `e9be48866f83d286b95e172e64424b3f36aa877743775ce74358398a27b16216`.
- Complete ZIP SHA-256 B: `9a5c3e5256986dafdab229c100ce715fc18200272b0ee3f97e010f5fc9461b38`.
- Independent zlib CRC verification and four known-suffix GF(2) inverse checks PASS. Python `zipfile.ZipFile.read` independently reconstructs each correct distinct source.

Actual installed authentic CMPCT revision-24 builder/reader product **does not conflate the two ZIPs** in this test: `Builder.build()`, `CMPCT.verify()`, `CMPCT.read()` and `extractall()` all PASS and preserve both physical ZIPs exactly. Result archive **132,577 B**, SHA-256 `717254d7187483087f80f1e316e461759f8e95f05837a0785c1018b0820a05f8`. One measured create wall **0.007386 seconds** is only a single correctness-run incidental observation, no paired timing/benchmark credit.

The recorded scientific assertion `O74_CONFIRMED_METADATA_NONIDENTITY_WITH_AUTHENTIC_CMPCT` printed in the hosted job. It means *same ZIP metadata is not a safe certificate for merging different expanded data*. It does **not** assert that the present CMPCT Builder uses such a certificate.

## Decision / adversarial self-review / limits

**Falsified:** unverified cross-ZIP deduplication based solely on names, CRC32, method, compressed and logical lengths, flags, offsets and other ZIP metadata, even when complete local header, central directory and whole container size agree. Source authentication must eventually compare strong expanded content identity (or an equivalently sound exact reconstruction proof) before two logical objects may share one owner. Cheap metadata features remain allowed to prefilter/prioritize VZIP candidates; this oracle does not establish a cost-effective predictor, does not preclude probabilistic prioritization, and does not prove any current CMPCT safety failure.

The synthetic incompressible 64-KiB collision is intentionally adversarial. Only one corpus and one hosted Linux x86-64 Python build/extract observation were run; no Windows/macOS/Android/native ABI/general large corpus/performance coverage. CRC is not cryptographic authenticity and no external source signatures were tested. No format/runtime code change or official ZIP/Zstd/ABBA release gate is credited.

**Counterfactual transferable discriminator:** before productizing any 'same ZIP member' ownership shortcut, try the 32-bit CRC collision with matched lengths/central-directory bytes. That cheap math/actual-ZIP oracle can invalidate metadata-as-proof without an expensive reconstruction benchmark. It does not justify global changes to Discovery Engine policy from one example.

**Concurrency:** O63 #418 owns VZIP product admission; O71 #427 holds independent structural byte-economics evidence; O68 #424 and O73 #429 cover different costs/physical organization. Their source and hypotheses remain unchanged. The next unclaimed valuable action is prospective cheap candidate **screening with full exactness confirmation**, not another CRC-tuple test.

**Evidence status at result landing:** focused exact-head O74 scientific/product job SUCCESS; Engineering Evidence originally failed on PR description *section names*, not experiment source. PR description was reconciled without weakening the validator; its final verdict must be checked separately. Other inherited generic CI, exact-head full product and official release gates remain independent and no merge/release is authorized.

quality-ratchet: Preserve stronger-than-CRC object identity, original equal-header/central metadata hostile counterexample, entire release/hardening law and trusted negative evidence. Neither a forced CRC collision nor the single successful CMPCT check counts as a compression performance gain.
