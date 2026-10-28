# J24C07 — compose authenticated VZIP projection into J24C03 guarded Reader (prospective)

Status: **preregistered research/product-composition candidate**. Not a release, not a format change, and not an assertion that independent green PRs imply a green composition.

## Authority and source boundary
- Canonical published CMPCT v0.30.0, on-disk revision 24.
- Exact composed Reader source owner #630 at `0a128ff55c7ae0f14c6bdf019a81b40f0d894eff` (on #569), chosen BEFORE code changes.
- Independent virtual ZIP physical-geometry owner #624 at `a4b54266f7cb09e03f9d8704155774b10d6351ab`.
- Historical falsifier #622 and issue #623: a fully reauthenticated ZIP with logical size exceeding physically reconstructible bytes can pass strict preflight, and a selective in-bounds read returns an empty response.
- #630 owns direct RAW/Deflate range and extraction custody, #637 independently owns native ABI3 economics. Neither branch may be overwritten. Discovery STATE owned by #574; no shared state write.

## Primary falsifiable question
Can the exact #624 `_validate_recipe` physical projection and `range_vzip` exact-result-length postcondition be composed into #630, without losing direct BLOB, signed CDC/sparse/chunks, FD-owned extraction, original valid virtual ZIP semantics or adding archive-wide scans per selective request?

## Prospective prediction and kill conditions
1. Valid frozen revision-24 virtual ZIP STORED, Deflate mode0 and mode1 reconstruct exactly, SHA matches, real ZIP opens, and all zero/partial/full ranges remain exact on Linux/macOS/Windows.
2. A fully reauthenticated index declaring impossible signed recipe projection is rejected by strict preflight, including +/- one-byte logical, skeleton and payload mutations. With preflight omitted, a read of one declared-but-unreconstructible byte raises an explicit error; it must never silently truncate.
3. Original #630 Reader/validation source is byte-identical outside `_validate_recipe`, its invocation in `_validate_index`, and `range_vzip`. Independent source audit checks these exact changed regions against original #624 source and forbids changing frozen tests, codecs, release gates, comparators, format, version or source owner branches.
4. Run unchanged J24K05 focused court and independent inherited #630/#569 correctness controls; if any valid ZIP is rejected, any hostile read truncates, any direct-owner guard disappears, or source provenance fails, the proposed composition is not valid.
5. Measure actual preflight wall and CPU against exact #630 source on a small and a recipe-heavy case before claiming economic or release benefit. No benchmark credit from operation-count reasoning alone.

## Causal mechanism and alternatives
A signed logical `recipe.total` is only metadata: compare skeleton literal sum to authenticated skeleton uncompressed size and each stored/retained/canonical payload to the correct authenticated source size; compare reconstructed projection with total. Do not infer Deflate mode2 compressed length from uncompressed bytes. At `range_vzip` check returned length on BOTH early and final returns. Stronger simple control: original #630. Alternative full reconstruction at admission is potentially correct but expensive; a per-range full preflight rescans/may race inode; rejecting mode2 breaks compatibility.

## Evidence order and integrity
Preregister this note as an isolated commit **before implementation**. Implement minimal deltas. Keep original J24K04 scientific observational test immutable because its expected vulnerability describes published baseline, and run J24K05 candidate test separately. CI: three-host clean installed candidate + direct inherited controls + version/source fingerprint, durable raw receipts even on negative. Distinguish evidence-only source inspections, focused integration evidence and full product/release gates.

## Scope and safety
Synthetic public fixture data only. No private corpus, user data or unrelated FCMO context. No release/merge without exact-head tests, full Reader performance, portability, recovery, engineering/evidence and official promotion controls. This PR cannot claim complete semantics of Deflate mode2, concurrent source mutation or hardlink identity without new evidence.

## Decision
Promote as an integration candidate only if all specified focused tests and source custody hold. Otherwise preserve a precise negative, retry only when new information can change the decision; do not weaken tests or thresholds.
