# J24I17 — Authentic sparse owner × hardlink alias compaction resource result

**Date:** 2026-10-29 UTC. **Disposition:** `ALIAS_COMPACTION_RSS_DEBT_CONFIRMED` (product-candidate research only; not released).

## Prospective basis and exact source
- Frozen preregistration: `44cad3ea10d6bc76a2be3f5a1d40b473f136e474` (before implementing instrument).
- Tested exact scientific HEAD: `cda5f3b18b1547fefb9986c35c073a4faee056eb`, stacked on PR #735 source `82e90eca58ed0580df191378947004e4061d53c3`.
- Source locks: Reader `b2b7774c13a5c8235ff89786d171b7ea3ff20710` (#613), Builder `387192edd783e02bf7a44a38945214bf9d6c183e`, transactions `8d1e46e1fdf408c1d95ce9091e25fa159f0e6264` (#723). No product source modifications in this PR.
- Actual hosted installed-wheel scientific run [#40833676256](https://github.com/FCMO-AI/.CMPCT/actions/runs/40833676256), job `123313396842`, status **SUCCESS**. Original preserved raw GitHub artifact [#12879138938](https://github.com/FCMO-AI/.CMPCT/actions/runs/40833676256/artifacts/12879138938), original ZIP SHA-256 `ede39bfeba65cf6d6d26536bfd2bb61179ae64410ed7f87768c92c6c8a70d4a8`, equal to GitHub artifact digest.

## Measurements (scientific compaction-only, KiB, Ubuntu 24.04)
For both sizes, the source was a Builder-created genuine sparse owner with two 4 KiB physical ranges and one real append-update generation. Owner+alias variant added one true `os.link` entry and required Builder to encode `K_HARDLINK` to the terminal `K_FILE/S_SPARSE` owner. Every condition consumed source-identical bytes across two separate child processes; ABBA order was owner/alias/alias/owner for each size.

| Logical sparse owner | Topology | Peak RSS KiB (two trials) | Wall milliseconds (two trials) | Physical source / output bytes |
| --- | --- | --- | --- | --- |
| 2 MiB | Owner only | 25,580 / 25,580 | 8.467 / 8.472 | 1,478 / 1,310 |
| 2 MiB | Owner plus hardlink alias | 27,780 / 27,924 | 16.597 / 16.735 | 1,514 / 1,342 |
| 128 MiB | Owner only | 25,580 / 25,580 | 228.455 / 228.274 | 1,476 / 1,306 |
| 128 MiB | Owner plus hardlink alias | **285,844 / 285,828** | **819.805 / 817.477** | 1,510 / 1,340 |

The **conservative** RSS delta, minimum 128 MiB alias RSS minus maximum 128 MiB owner-only RSS, is `285,828 - 25,580 = 260,248 KiB = 254.1484375 MiB`. Both large alias trials exceeded the prospective +64 MiB rule. Exact per-condition output physical SHA, rows/index metadata, per-member logical SHA, path/hardlink topology, source SHA immutability, journal removal and sparse data head/tail passed. Topology variants differ in member count and physical metadata bytes; they are not byte-identical input A/B, nor is this an official release timing gate.

At 2 MiB the analogous conservative RSS delta was 2,200 KiB. The result is therefore specific to large sparse aliases, not a flat per-alias overhead.

## Independent physical archive audit (third code path)
Original hosted artifact ZIP was downloaded and retained unmodified. A standalone Python auditor using `struct`, `msgpack`, `ctypes libzstd`, `hashlib` and `binascii`, **never importing CMPCT**, decoded both r24 index forms, authenticated original and committed journal records, independently reconstructed logical sparse hashes through bounded zero-block hashing, resolved alias owners, cross-checked all source/output rows, metadata and per-member digests against raw child receipts, and validated source unchanged and final journal removal. Result: **PASS** — 12 original physical CMPCT archives, 30 indexed logical member rows, three independent deliberately corrupted physical blobs rejected by the auditor. The latter establishes auditor tamper sensitivity, **not** the product Reader's fail-close behavior under all perturbations.

Instrument correction retained: the first external audit iteration erroneously counted a valid checkpoint (kind0) as a journal delta (kind1); only the independent auditor's expected depth count was fixed before the final clean audit. No product source, scientific corpus, preregistered threshold, data, or outcome changed.

## Causal diagnosis and limits
- #735 streams `K_FILE/S_SPARSE` verification through exact donor #613, avoiding hole materialization. However a `K_HARDLINK` alias still follows `Reader.read()` during verification; the resulting large extra RSS is consistent with an O(logical-size) materialization. The experiment isolates the observable **topology-induced compaction resource regression**, but does not independently instrument every internal allocator call.
- #620 already owns the matching sparse-hardlink verification donor. Do not fork, copy, or replace that ownership. The next cheapest action is integrating its verified owner/alias treatment into the #735 compaction candidate, then repeat this exact scientific court with unchanged comparator.
- Source #735 may have changed independently since this run; HEAD SHA, source locks and exact CI evidence govern only this frozen commit.
- Ubuntu 24.04 only. No Windows/macOS, concurrent inode mutation, 4 GiB sparse alias, native reader ABI, official release benchmark, tempfile I/O or security promotion evidence claimed.
- Stage-name substitution of compaction [#726](https://github.com/FCMO-AI/.CMPCT/pull/726) remains a **separate hard security veto**, even if RSS is repaired. Published `main` v0.30.0 and revision24 are untouched.
- Generic CI may contain inherited historical release-identity test failures; only the specialized exact-head scientific court supports this measured claim. A successful workflow with skipped official benchmark is not official performance evidence.

## Decision and counterfactual
The hypothesis **advanced decisively**: under a genuine physical alias, the apparent 128 MiB compact regular-owner memory improvement does not generalize. The strongest alternative explanation, a different physical sparse payload, was addressed by exact owner logical bytes, genuine `S_SPARSE` admission and source-authenticated metadata; differing topology is intentional. This confirms **D5 productization debt** for the existing #620 mechanism, not a mandate to create a third verifier.

A prospective discriminator was already visible in #735's caveat: an owner+one-alias 128 MiB source-exact resource trial. It produced decisive evidence more cheaply than a full 15-row product benchmark. One result warrants a local future test inclusion, not a global Discovery Engine policy change; `docs/discovery/STATE.json` remains owned by #574.

**Next action:** existing #735/#620 owners may apply streamed sparse alias verification without weakening alias-size checks, then rerun this original physical topology court and independent auditor. Cross-platform safety and stage-custody gates remain separate before any merge/release consideration.
