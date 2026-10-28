# J24B10 — Signed sparse extent overrun versus extraction max_bytes (prospective freeze)

**Date:** 2026-10-28 UTC. **Scope:** science-only, released CMPCT v0.30.0 / revision 24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`. **Status:** PREREGISTERED BEFORE INSTRUMENT / RESULTS.

## The one question

Can `CMPCT.extractall(max_bytes=L)` publish a sparse logical file larger than authenticated declared size `L` when an attacker controls a SHA-consistent sparse extent descriptor but not the physical blob payload? Does the Reader's direct `pwrite` path enforce the extent's declared length, or can its actual physical blob length extend the file beyond `ftruncate(L)`?

## Baseline, mechanism and predictions

The original `src/cmpct/reader.py` (Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`) sums signed file row sizes for `max_bytes` and `S_SPARSE` extraction uses `ftruncate(fd,size)` followed by `_blob(idx)` and writes **each entire decoded blob** at extent offset without checking decoded length against extent `ln`, verifying final file size, or verifying the whole-file SHA. The separate strict `validation._validate_storage` compares extents to physical blob sizes, but ordinary extraction does not invoke that preflight.

**Frozen input contract:** create a Builder-independent genuine revision-24 archive for one `sparse.bin` with `L=16384` logical bytes: a physical RAW blob with `B=8192` bytes, one sparse extent `[4096,8192,[0]]`, zero holes before/after, SHA-256 of the complete correct logical bytes, two identical Zstd-encoded index copies and valid header/footer SHA-256. Mutate **only** the first extent to `[L-1,1,[0]]` in both re-authenticated indexes, preserving physical blob region byte-for-byte and the unchanged file row's logical size and SHA.

**Primary predicted outcome:** the signed mutant passes the ordinary `CMPCT(...)` open, fails strict `preflight_archive`, and `CMPCT.read`/`verify` reject. Yet `extractall(max_bytes=L)` returns successful and publishes a `(L-1)+B=24575` byte file, overshooting its declared budget by `B-1=8191` bytes. Original control `extractall(max_bytes=L)` must produce exactly L bytes with matching original SHA; original with cap L-1 must refuse before writing. Mutant at cap L-1 must also refuse. Positive original and signed mutant must share identical physical data bytes; only serialized index/outer framing may differ due re-encoding. All observations must preserve raw hashes and output lengths.

**Disproof:** if ordinary Reader rejects the signed mutant before publication, if output does not exceed L, if a source mismatch occurs, or if the probe cannot authenticate both index copies, primary hypothesis is false/inconclusive and will not be rescued through relaxed assertions. A failure to create a valid *original* control invalidates the instrument.

## Stronger control and alternatives

1. Existing strict `preflight_archive` is the strongest simpler structural control, not the released ordinary Reader; show that it rejects the mutated extent without changing its semantics.
2. Existing #572 / science #571 proves sparse SHA/premature-publication defects, but does not prove this specific physical expansion beyond signed logical `max_bytes`. This test targets only the **new quota/extent length discrepancy**, not another generic checksum failure.
3. Existing #569 owns broad admission and #255/#270/#573 own sparse extraction/publication. This PR changes **zero** product, test, validator, release, or benchmark files; notify owners with confirmed receipts, do not duplicate their fixes.

## Evidence ladder

- First: source- and schema-exact code/derivation; hand-built real revision-24 bytes, frozen positive/mutant/control comparison.
- Next: installed Reader on Ubuntu 24.04, macOS 14, Windows 2022; exact source git SHA, source file hash and real output byte counts; independently computed physical SHA/index and caller cap, full raw JSON persisted even on failure.
- Independent referee: parse the on-disk HDR/BHDR/FTR and compressed index; validate SHA-256 and physical segment identity; compare claimant's output-length receipts and reject tampering. Referee must not call CMPCT read/extract.
- Unrelated pytest/benchmark/red release checks retain full existing gates; a science SUCCESS is product defect evidence, never a safe product or release pass.

## Costs, limits, and ethical claim scope

No remote attackability, privilege crossing, arbitrary overwrite, universal sparse workload prevalence, memory amplification or general DOS claim. This is an intentionally malformed but SHA-consistent archive constructed by a malicious producer. SHA-256 index authentication is unkeyed, not an external signature. The exact scope is **logical-byte accounting and valid output size**, not physical allocated disk bytes, which may remain sparse. The production fix belongs to a strict, bounded preflight/streaming/extract-authority owner, must enforce extent geometry and output verification before publish, and must account CPU/RSS/temporary I/O and retained sparseness.

Frozen criteria and controls above may not be edited after result-bearing execution begins. Future corrections need an append-only superseding preregistration.
