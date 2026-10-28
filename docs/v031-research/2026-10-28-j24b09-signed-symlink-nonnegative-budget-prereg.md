# J24B09 — signed nonnegative symlink-size quota falsifier (prospective)

**Status:** PREREGISTERED BEFORE EXPERIMENT CODE. Science only; no product fix or release.

## Current authority / ownership (2026-10-28 UTC)

- Released: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, revision 24.
- **Installed candidate**: [J24B06-R1 PR #690](https://github.com/FCMO-AI/.CMPCT/pull/690), Reader head `adcf38cb5be022567c1faf6538aefeef2f6b72de`. This branch is stacked and research-only; do not touch its Reader or tests.
- Related independent evidence: [#688](https://github.com/FCMO-AI/.CMPCT/pull/688) finds negative-size symlink cancellation; [#693](https://github.com/FCMO-AI/.CMPCT/pull/693) proves nonnegative hardlink owner-size undercount on the same candidate. The latter owns hardlink research. **This experiment probes the distinct K_SYMLINK length-to-target-blob binding.**
- The active Discovery state in PR #574 is staleable coordination, not a lock. No concurrency claim script or protocol exists on the selected ancestor; before subsequent writes recheck current branches/PRs.

## Primary falsifiable question

**Can a fully SHA-authenticated revision-24 K_SYMLINK row declare a nonnegative length shorter than its actual independently verified physical target blob, and cause `extractall(max_bytes)` to publish that link while the requested byte budget is smaller than the archive's genuine Builder-reported logical expansion, even after #690?**

The original Reader `read(K_SYMLINK)` delegates directly to `_blob` without checking row[4]; `verify` hashes the delegated bytes; #690 validates that row[4] is a nonnegative exact integer but does not assert equality to the target blob. This is a source-level prediction, **not observed installed-product evidence**.

## Preregistered dataset and interventions

Generate one real Builder-produced r24 archive with:
- a deterministic 8,192-byte ordinary file `payload.bin`;
- one relative in-root symlink `offset-link` whose target text is exactly `payload.bin` (11 UTF-8 bytes);
- fixed reproducible Builder metadata, one worker, physical frames unchanged between baseline and mutations.

From the actual primary index, mutate **only** the K_SYMLINK row's declared size from 11 to `0` or `1`; recompress MessagePack at the original zstd index codec setting, replace both primary and duplicate tail indexes, recompute their SHA-256, and preserve the exact physical blob region. A mutation that touches any other decoded index field, physical bytes, source tree, or target blob invalidates the experiment.

Run the actual installed #690 Reader/Builder against:
1. honest original with `max_bytes=8192`: **reject before creating destination**;
2. honest original with `max_bytes=8203`: **accept** and publish exact 8192 file bytes + 11-byte symlink target;
3. signed zero symlink declared size with `max_bytes=8192`: predict **accept** and publish both objects;
4. signed one symlink declared size with `max_bytes=8193`: predict **accept** and publish both objects;
5. signed zero symlink declared size with `max_bytes=8191`: predict **reject before destination**;
6. signed zero symlink declared size with `max_bytes=None`: predict accept; distinguish nonnegative metadata from real length binding.

`verify()` must return 2 for every source and mutant; `read("offset-link")` must return exactly 11 bytes; `read("payload.bin")` must return exactly the source bytes. No symlink path outside the isolated destination is permitted.

## Decision / disproof

- **CONFIRMED_NONNEGATIVE_SYMLINK_QUOTA_UNDERCOUNT** only if all six cases behave as predicted, all index/physical identity controls and independent referee agree, and both hosted Linux systems pass on the **exact branch HEAD**.
- **FALSIFIED_BY_VALIDATION** if signed zero/one mutants are rejected before publication while healthy controls pass.
- **INCONCLUSIVE/INFRA** for skipped symlink creation, source identity mismatch, wrong payload, incomplete export, any other unrelated failure or failed detached referee. Never call infrastructure failure a product loss.
- No release/product credit even if confirmed. A complete repair must bind authenticated logical K_SYMLINK size to its physical payload, and separately address K_HARDLINK effective-owner binding (#693); this study must not implement either owner code.

## Controls and cost accounting

- Check raw/decoded primary and duplicate index SHA identity, header + physical span, unchanged physical bytes and member hash under an **independent parser** (standard Python + msgpack + libzstd/ctypes or separate zstd implementation).
- Persist original and hostile complete r24 files, exact source Git HEAD and installed Reader identity, data fingerprints and extraction receipts.
- Referee must reject at least five forged receipts: wrong source hash, wrong physical SHA, misstated declared length, inconsistent acceptance decision, and incorrect extracted link target.
- Ubuntu 22.04 and 24.04 (or Ubuntu 24.04 and macOS 14) are sufficient for this symlink proof; Windows symlink privilege is an explicit transfer gap. No CPU/RSS/product benchmark inferred from this small correctness fixture.
- Simplest strong control is the honest first-party Builder archive; alternatives (implementing product fix now, extending hardlink #693, changing max_bytes definition) are rejected because they duplicate ownership or weaken the falsifier.
- Preserve all negative/mixed results and do not adjust criteria after observation.

## BONK / continuity

The family already has decisive negative/zero-byte and nonnegative-hardlink examples; this is **one bounded final different-kind size/binding discriminator** rather than continuing an unbounded series of quota perturbations. If it confirms the same root, retire further row-kind variants and ask the existing product owner to design one owner/physical-size semantics gate; if not, record why symlink differs.

No frozen benchmarks, format, Reader, thresholds, Discovery policy or state may be altered by this research-only trial.
