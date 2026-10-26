# O150 — transactional ZIP export: first hosted exact-source result

**Date:** 2026-10-26 UTC. **Category:** candidate implementation + actual installed-product science, **not** merged/released.

## Question and original negative

On O140 [#488](https://github.com/FCMO-AI/.CMPCT/pull/488) `d8b69758dbcbb66fe28fa7cf59598916df160d2d` (Reader blob `e46e6121842d485cb209118576ebf3ba3719080d`), source-authentic O143 [#489](https://github.com/FCMO-AI/.CMPCT/pull/489) demonstrates that ordinary `CMPCT.export_zip(existing_regular_zip)` can overwrite a valid 190 B prior ZIP as **0 B** upon early physical RAW CRC rejection and as **98,344 B of incomplete invalid ZIP** when a later member fails. The original negative instrument remains unchanged.

O150 preregistered its inverse prediction at `2971c0623c357b5120f4c66211789bf7706e578e` before code. No format, benchmark, release or source-of-truth changes.

## Mechanism and exact-source custody

Candidate Reader Git blob `f38662c8db4132895778951263d83d24022f9296` keeps the inherited own-source inode / nonregular public destination checks. It creates a private same-directory regular sibling, runs the same ZIP serializer into the private file, and `os.replace()` publishes the entire closed ZIP only if the serializer succeeds. Cleanup removes stage on caught exceptions. Core codec/physical format/Builder/native unchanged.

First hosted scientific HEAD `633a050b26f1bfe19577b8835aa2255be7a0c2c1` ran full standalone [GitHub Actions 40268279194](https://github.com/FCMO-AI/.CMPCT/actions/runs/40268279194) **SUCCESS**, source/test/vector blob checks and installed Reader outside checkout. Ubuntu job `121395336009`, macOS job `121395336146`; each **4 PASS / 0 FAIL / 0 SKIP**. Independent workflow JUnit audit completed successfully. Raw original artifacts: Ubuntu [12626857863](https://github.com/FCMO-AI/.CMPCT/actions/runs/40268279194/artifacts/12626857863); macOS [12627352305](https://github.com/FCMO-AI/.CMPCT/actions/runs/40268279194/artifacts/12627352305). Original control vector blob `d10b7dab9126d39e819a74279c186363a163f2ef`, O150 test blob `102bb045734102c377c0552274a5185f57a64c18`.

## Direct measured outcomes

| Source-exact case | Ubuntu | macOS | Interpretation |
| --- | --- | --- | --- |
| Frozen independent RAW CRC corruption, existing valid target | prior ZIP exactly **190 B**, same pre/post SHA, parser rejects; PASS | same, PASS | early rejection does not truncate public target |
| Genuine two-member Builder late RAW payload corruption | prior ZIP exactly **190 B**, same pre/post SHA, parser rejects; PASS | same, PASS | no earlier local ZIP entry visible in public path |
| Clean fixed RAW archive replaces regular valid prior ZIP | 176 B independently readable, original output inode replaced, old hardlink retains old bytes, POSIX 0640 preserved; PASS | same, PASS | positive content **and compatibility loss** |
| Failed export to non-existing public destination | no output and no stage remaining; PASS | same, PASS | fail-closed path creation |
| Total | **4/4 PASS** | **4/4 PASS** | **8 successful actual hosted science controls** |

Read errors and export errors both report `OSError: blob integrity failure` in early/late corrupted cases. Original archive SHA is not silently rewritten. Each host emits `O150_AUDIT` with exact source, Reader, test and vector blobs and four named cases. Cross-host prior ZIP hash differs because zipfile writes host-dependent metadata; each host's **own** pre/post hash matches exactly. This is not a cross-host ZIP byte parity claim.

## Negative evidence, material debt and self-critique

1. **Inode semantics change on successful export (directly proven):** public target gets a new inode and another hardlink to old ZIP retains old content. Previous in-place overwrite modified that linked inode. User-visible compatibility requires owner decision, not dismissal.
2. ZIP-stage temporary storage can reach **O(output ZIP bytes)** plus an additional file inode; no compression/storage win is credited. New target defaults to restrictive mkstemp permission; owner/xattrs/ACL/hardlinks/metadata behavior not generally preserved.
3. Same-directory `os.replace` is atomic name publication for ordinary same-filesystem exception cases, **not** power-loss durability; no `fsync`, no protection from concurrent namespace swaps, no Windows/SMB/NFS or genuine >4 GiB ZIP64 evidence.
4. First hosted court only covers 4 cases per POSIX host. Real write failure mid-serialization (ENOSPC, EIO), rename failure, symlink-to-regular case, and cross-host ZIP64 full-product behavior remain unmeasured.
5. Full inherited CI is **not green** for first HEAD: original O140 workflow source-exact Reader pin refuses new Reader blob before executing its tests; O150 specialized court does not rewrite the historical pin. Initial Engineering Evidence red was a missing PR-body `quality-ratchet` marker; initial CI Topology red was fast-lane cancellation policy. Both documentation/workflow metadata have been corrected in later HEAD, without changing original O150 product/test blobs. General and fuzz were in progress at prior observation. Official r24/ZIP workflow's wrapper reported success but the substantive `performance` job was **SKIPPED**; do not count it.
6. Existing scientific/control law, size/timing thresholds and portable reader semantics remain unchanged. Results here cannot authorize merge or release.

## Scientific decision and counterfactual

**Positive research/candidate decision for ordinary exception-atomicity in tested POSIX domains.** O143's defect claim is not repudiated; its original negative remains valid for O140. O150's new candidate proves a different outcome against the same core cases. The cheap prospective discriminator was a SHA-protected **pre-existing valid output ZIP**, verified after deliberately provoking source read failure. That earlier control would have localized failure-publication risk before adding full ZIP performance measurement.

No discovery process-policy change is earned. No collision with O143's original scientific file; implementation explicitly stacked on O140 ownership, and no other owner branch changed.

## Promotion and next work

Owner of ZIP export (#284/#488) must adjudicate target inode/permission/hardlink semantics, then source-bind inherited O135/O140 exact original tests against this **new Reader** in a separate continuity court (never edit original historical fingerprints), add injected write/rename fault tests and substantial full-product size/create/extract/export CPU/wall/RSS/temp-I/O pricing, complete official substantive comparator, and validate host-specific semantics. This PR remains **DRAFT** until these debts are closed. Zero format/release/site modifications.
