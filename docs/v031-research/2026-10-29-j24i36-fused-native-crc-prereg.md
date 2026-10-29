# J24I36 prospective hypothesis — fuse physical CRC with native strong SHA verify

**Preregistered 2026-10-29 UTC, before implementing code or running candidate CI. Status: PREDICTION, not result.** No frozen workload, release gate, format revision, comparator, or product version changes.

## Authority and source boundary

Canonical published `main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0 / r24; experimental native correctness source is PR #759 at exactly `e67ed337e78e021ba91f7bc6bdc271ae0ddd6b51`, with native `lib.rs` blob `463c50633be74423e92a074b7d7577db6a4b0cf9` and `vzip_dispatch.rs` blob `cd1a367761465cbba3e8054f743af551c1e560e1`. The separate [scientific PR #762](https://github.com/FCMO-AI/.CMPCT/pull/762) proved one true negative: a genuine 27-byte r24 RAW symlink with a flipped CMA4 CRC-only header bit was rejected by Python `CMPCT.verify()` but accepted by native `Archive::verify_complete()`; both preserved payload SHA-256. Do not edit #762's negative court or reinterpret its observation as an SHA bypass.

## The decisive question and alternative frames

Can we close that physical-header-consistency divergence for **direct r24 RAW, Zstd, Deflate and real symlink**, with CRC accumulated from the **same streamed decoded bytes** already fed into the strong SHA verifier, without a second payload scan, an archive-format change or a material strong-verify performance regression? A pass is a native product candidate, not release credit.

Alternatives: (A) leave CRC-only mismatch admitted in native SHA verification, consistent with SHA-only integrity but inconsistent with Python strict physical-field semantics; (B) compute CRC in a second full pass, which exports full decoded-byte reads and memory traffic; (C) do the checksum while reading each verification chunk, using the authenticated expected physical CRC for direct records only. Select C for smallest plausible cost and direct format alignment, but preserve A as the strong simpler control and B as an accounting comparator. Composite pack/chunk/sparse paths are deliberately **not certified** for physical CRC by this initial direct-member patch.

## Predicted observations, falsifiers and hard boundaries

Use **unchanged builder-independent frozen** `tests/conformance/v24-direct-codecs.json` source bytes and unchanged real symlink source from J24I30. For each of RAW(0), Zstd(1), Deflate(4), flip **only one bit of the physical CMA4 CRC32 at header offset +28**, leaving physical data, physical SHA, authenticated index/footer and logical data byte-identical. For each pair, require: (1) unchanged archive opens/verifies in installed Python and native; (2) changed archive is rejected by both in explicit full verification; (3) native still rejects separately corrupted physical bytes, present contradictory logical SHA, and unchanged historical zero-length optional SHA semantics inherited from #759; (4) detached non-CMPCT referee confirms only CRC differs and decoded SHA remains unchanged.

If any originally valid frozen fixture fails, or a CRC-only mutant is accepted by repaired native, the proposed fix is **falsified**, not rescued by weakening vectors. If installed source, compiler or CI fails before the behavior executes, classify as infrastructure. If a transformed archive changes bytes on write, this candidate has violated its no-writer/no-format premise.

## Cost gate, scale and adversarial self-critique

Compare native full-verify original versus candidate on exact same 64-MiB deterministic direct RAW archive (one emitted artifact, two sources, repeated same-runner randomized/ABBA order), separating process startup from in-process verification where possible. Capture complete bytes, wall, CPU where portable, RSS, file reads if measurable, checksum enforcement and valid/mutant outcomes; unchanged small vector checks cannot certify whole-product performance. Define a provisional investigation hurdle: median strong-verify wall regression above **5% plus 2 ms** on matched 64-MiB input means do not promote without redesign, but this cannot replace any stricter canonical release criterion. Multiple samples and raw timings required. A second CRC accumulation necessarily consumes extra ALU cycles, even when no second logical stream is read; claim *one input traversal*, not *zero cost*. Any unexpected checksum incompatibility or unsupported codec remains explicit.

Do not broaden into zero-size compressed-frame integrity (owned by PR #763 / issue #764), platform extraction, stage publication, v0.30 frozen release bindings, or native format redefinition. No auto merge/release.

## PARETOBONK / handoff

Owner is the separate Phase3 J24I36 stacked candidate, not #755's full format/legacy admission program. Preserve #762 science immutable; post evidence and link to #755, request reconciliation with native owner #759. Exact current branch/claim must be checked before writing. No Discovery STATE mutation unless a decision-changing current frontier genuinely changes. The cheapest falsifier is fixed golden CRC mutation + native compiled court; only after it passes invest in full 64-MiB overhead measurements or higher-cost platform work. Counterfactual observation to test: a one-bit CRC-only mutant is sufficient to discriminate strict physical-field custody without any payload cryptographic attack.
