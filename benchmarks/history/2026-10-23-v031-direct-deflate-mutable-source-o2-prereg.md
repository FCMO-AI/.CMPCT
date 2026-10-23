# CMPCT v0.31 — O2 mutable-source Deflate export boundary (preregistration)

Date: 2026-10-23
Status: **PREDICTION FROZEN BEFORE RESULT**. Research-only independent hostile replication; no production code modified.
Experiment ID: `v031-direct-deflate-mutable-source-after-preflight-o2-20261023`
Repository: `FCMO-AI/.CMPCT`
Exact source base: PR #284 HEAD `57746bbf5bcbee2d146235d958a5e6c068167c8a` (stacked on count-only ZIP64 PR #260 `333bea363fc4583abd1a1f33b68f20d2e07ba179`).
Owner: PR #284 owns direct-Deflate validation implementation. This isolated experiment may **not** replace or modify its product source.

## Why this question is distinct and decision-changing

PR #280 proved that ordinary export accepted already-corrupted Deflate streams. PR #284 fixes *static* corruption with `_verify_direct_deflate_blob()` before opening ZIP output, then copies compressed bytes with `_direct_deflate_stream()` during output construction. Its focused court validates static corruptions but does not freeze source bytes between verification and copy. The two operations read the same read-only **file-backed mmap**, not an immutable snapshot; another writer to the source archive may change its pages between the two reads.

Question: can a source accepted at verification time become a successful but invalid exported ZIP when the physical archive changes **after verification and before copying**? This tests snapshot/ownership semantics, not duplicate static-byte validation.

## Expected evidence / mechanism

Build a genuine independently assembled revision-24 direct-Deflate archive with one member from a fixed `zlib.compressobj(0, zlib.DEFLATED, -15)` stream. Level 0 stores uncompressed bytes in an RFC1951 stored block (5-byte block framing when <65535 B); changing exactly one payload byte retains compressed size and grammar but changes decoded content and invalidates the original logical CRC/SHA. Retain the original committed index, original physical blob header and all metadata.

Run three disjoint controls:
1. Immutable pristine source: `CMPCT.read()` and `export_zip()` and independent `zipfile.read()` return exact original content; exported compressed bytes equal original.
2. Source modified **before** export preflight: candidate rejects and leaves a pre-existing destination untouched. This is the positive control for PR #284's intended static fix.
3. Deterministic post-preflight mutation: instrument only the test instance's `_verify_direct_deflate_blob` wrapper so that it first calls the original validator, then writes one in-place byte to the underlying source archive, flushes and returns. Subsequently call unmodified `export_zip()`. Inspect the output with independent `zipfile` and check the actual exported raw stream and source/target CRC mismatch.

**Prediction:** (1) accepts; (2) rejects; (3) returns success, retains mutated raw Deflate bytes, while `zipfile.read()` rejects with `BadZipFile`. If (3) rejects or exports a valid authenticated snapshot, the suspected time-of-check/time-of-use gap is falsified. If concurrency injection or mmap visibility fails, outcome is **ambiguous infrastructure**, not negative product evidence.

## Controls and alternative explanations

- Simpler control: statically corrupt source before calling export; #284 already rejects it. A second static test cannot answer this question.
- Alternative explanation: `mmap.ACCESS_READ` may be snapshot-like on this host. Check source mmap bytes before/after injected mutation and preserve exact source segment SHA.
- Alternative: mutation might merely create an invalid Deflate stream. Level-0 stored blocks guarantee a syntactically valid stream; independently inflate mutated source bytes and compare payloads.
- Alternative: an output file might be partially written after exception. Distinguish successful return, parseable ZIP central index, and independently accepted logical member bytes.
- Alternative: the test wrapper may rewrite product behavior. It must delegate to the unmodified original verifier, mutate only *after* successful verification, and touch no other source methods.

## Decision and economics

Positive result narrows #284's proof to an **immutable-source / nonconcurrent-writer** assumption. Possible controls to evaluate later: read source from an immutable filesystem snapshot, or stage and authenticate exact compressed bytes into a temporary artifact and publish only after verification, charging memory/disk/IO appropriately. A simple `stat` recheck is not a race-proof fix; append-only source/writer locks only work with a real ownership contract. No general authentication/security claim against an adversary able to rewrite committed metadata.

Negative result requires original mmap/source identities and independently root-caused outcome before closing the question. One hostile case does not imply every platform shares the behavior. No archive-size, create/extract throughput, compression win, portability or release claim follows from this experiment.

## Promotion boundaries

Research court only; retain PR #284 owner code byte-identical. Do not modify frozen benchmarks, release gate, format revision, version, canonical branch, scientific policy, or shared discovery state. Host on source-bound GitHub Actions; preserve JSON evidence, source commit SHA, Reader blob and independent ZIP verdict. If evidence is decisive, give the owner a narrow comment pointing to the hosted receipt and required threat-model limitation.

**Expected scientific tier:** hostile product-path falsifier (research), not candidate product fix.
