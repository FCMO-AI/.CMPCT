# J24I45 — held-out stereo WAV/FLAC native verification transfer (prospective)

**Status at preregistration:** unexecuted experiment, evidence-only child of unmerged PR #788 at exact `2a6dbd5407731c5660faf71d04a4ef5de2d431bd`. No product, on-disk format, ABI, benchmark, release or threshold change is authorized. This record is committed before the generator, auditor, Rust probe or CI workflow.

## Primary question / mechanism
Does the source-owned single-pass native direct-WAV verifier from #788 continue to accept exact Builder-selected **stereo PCM16** with a structurally different interleaved two-channel pattern, while preserving native/Python logical identity and reducing complete verification work against the exact inherited #784 native implementation?

J24I44 tested six mono 44.1kHz random-walk sizes and found nominally faster streamed verification, but it did not demonstrate transfer to multichannel audio. The changed source geometry uses **two interleaved channels at 48kHz** with different deterministic structures: a seeded bounded-step walk in channel L and an integer periodic stepped signal plus bounded noise in channel R. Use fixed 2 MiB and 8 MiB PCM, each plus the canonical 44-byte WAV header. No codec pin or forced FLAC selection: Builder decides. This is one held-out family, not broad generality.

## Hypothesis and falsifiers
Prediction: a valid Builder output selecting direct codec 2 in at least one of the two sizes passes Python Reader full verify, detached physical r24/WAV/FLAC reconstruction, and both exact native `Archive::verify_complete()` alternatives. At 8 MiB+44 B, baseline repeated full decode should produce ~2x process-read-character count, while streamed candidate should reconstruct once. At 2 MiB the same-input A/B may be close or favor baseline; record any such loss.

Disproof / retire or narrow: no case is admitted by genuine Builder; a mismatch in reconstructed WAV, SHA256, CRC32, duplicated index or footer; candidate accepts a CRC-only, FLAC-frame or FLAC-magic corruption that baseline rejects; candidate fails a valid selected stereo case; material CPU/RSS/read/wall regression; source pins fail; raw trials or artifact absent. A missing codec-2 selection is a **negative admission finding**, not permission to force representation.

## Controls and decision
Frozen old native source: `0faa25827e7393f927252876d40e9f6cb53e5a24` (#784). Candidate native source: `2a6dbd5407731c5660faf71d04a4ef5de2d431bd` (#788). Both compile the same newly authored small Rust wrapper (the wrapper has no product decoder). The exact Builder source and installed Python deps are the same for both. Use deterministic same physical archive per arm, A B B A B A A B process order, separate process RSS/rchar, multiple verify calls with initial warmups discarded, and retain all raw observations. Track full archive bytes and SHA; do not credit as archive-size/creation/extraction win.

Independently audit physical r24 header, duplicate index, footer, CMA4, FLAC decode (libsndfile), authenticated WAV SHA/CRC, and original WAV bytes without importing cmpct. Preserve three independent one-bit/invalid FLAC corruption classes for both native arms on each admitted case. Original source remains unchanged. Reject any source-witness discrepancy.

Do not assume CPU gains from rchar; identify wall/noise uncertainty and VmHWM limitations. If 2 MiB is slower, do not threshold-garden until performance debt is real on structural held-outs and its cost/complexity can be charged. A green test is research/candidate evidence only, not three-OS installed-product or release parity.

## Concurrency / cost / next decision
Search at preregistration found no active J24I45 or stereo WAV PR. #788 owns native implementation and J24I44 mono court; this child only tests a non-overlapping held-out family. #765 retains native CRC ownership, #352 owns prospective installed-package aggregator. No modifications to those branches or `docs/discovery/STATE.json`. A 3-host native product release court and release gates are not replaced by this bounded Linux test.

Promote only the **scientific transfer decision** if independently audited, exact-source hosted receipts exist. Otherwise leave a scoped negative and return to stronger product/release priorities. No discovery-policy change is proposed from a single family.
