# J24C03 — Source-exact direct-owner custody composed with J24C02 Reader

**Status:** prospective, independent integration replication. **Date:** 2026-10-28 UTC. This record was committed before any Reader/validator/test edits on this child branch. **No merge/release authority.**

## Authority, separate owners, question

Published main is v0.30.0, format r24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Parent compositional Reader **#569** exact commit `c5e13bb3fbb4cdade8b64246658ce7c7818de41f` owns strict S_CHUNKS/S_CDC/S_SPARSE admission, effective authenticated index, and fd-owned extraction; the parent source blobs are Reader `dbd4ac576a05a47eae97e1e40de89cf1de440516` and validator `51c2849061f99a4afeddb7666956b24566ce7de0`. Separate direct-owner safety source **#609** at `45e7d24600f3e9a79e0ac99c9e28624f01418584` (Reader blob `72a1fd0acda62e518d53594c521391d42a9190e4`) has the original J24B03/H2/H3/H4 scientific safety courts and a measurable RAW read cost. Hardlink alias ownership is separate #615; direct Deflate payload authentication and transactional ZIP publication have independent owners #284 and #150-family. No edits to those branches.

**Primary question:** can **only** #609's direct S_BLOB logical-size, RAW physical-header bounds/flags, ordinary blob flags/reserved, symlink-size, RAW extraction-header and fast direct-Deflate ZIP-export guards be composed into the **same source** of #569 without losing any of its existing multi-owner methods, validations, and relevant r24 exact behavior?

## Baseline and falsifiable prediction

Parent #569 lacks these direct checks in source: `_blob` does not require zero flags/reserved, `read_range` does not bind direct file size or RAW BHDR, `read` does not enforce direct symlink logical size, `_direct_deflate_stream` copies a Deflate stream without checking the indexed/physical owner, and `_raw_blob_view_for_extract` omits zero flags/reserved. #569 separately holds **measured 27–28x S_CHUNKS open-time debt**; this composition does NOT pretend to fix or waive it. Simpler control is parent source unchanged. Other candidate is wholesale transplant from #609, which would **delete** #569's authentic fd/sparse/CDC/chunk work; rejected.

Prediction: the composed child preserves parent #569 code byte-for-byte **outside explicit guard hunks**, rejects the existing builder-independent 24 signed direct-size and 10 unsupported RAW header adversarial cases and 10 Deflate export cases, and accepts every valid frozen direct-codec and owner test. Inherited #569 O215/J24C02 tests must remain unmodified. The H4 zip control output must remain byte-identical to inherited valid export. Source/blob SHA provenance, exact installed modules, all raw receipts and separate comparator identity must be recorded.

## Implementation boundaries and negative/external costs

Use a minimal additive splice into **only** `src/cmpct/reader.py` and `src/cmpct/validation.py`, with no changes to #569 constructor, recovery, S_CHUNKS/S_CDC/S_SPARSE, Linux fd publication, Builder, codec, ABI, format or release. Reuse unaltered original #609 focused tests and scientific harness where possible, not new easier assertions. A validation that only passes by changing historical negative predictions is rejected. Bounds must be checked before mmap slicing. No extra full index scan. The already measured #609 direct RAW 135ns micro and +35–73ms high-cardinality debt remain **inherited debt**, not free; full combined Reader wall/CPU/RSS across host kernels remains unmeasured until an honest same-source cost court executes. A malformed admission with partial writing, changed valid bytes, revived #569 bug, test/worker provenance failure, or any weakened strict check kills an integration claim.

## Distinct outcome classes, ownership, transfer

This is an **independent composed research/product-candidate branch**, not takeover of #569 or #609. Source-exact targeted tests are product-path evidence only for their concrete domains; full release CI, native signed journal parity, ZIP authenticated payload, atomic export, hardlinks, extraction rollback, MAC/Win path safety, official size/create/extract parity and measured runtime are separately owned/required. Communicate resulting HEAD/test truth to both source owners; do not merge or release. If targeted controls pass, hand the smallest patch to owner #569 for further convergence. If not, preserve a concrete counterexample and stop promotion. No change to frozen thresholds, Discovery Engine policy or `STATE.json` (owned by #574).

## Alternative frame / opportunity cost

PARETOBONK: A new adjacent RAW-header mutation has low information value after H2/H3/H4; an unintegrated security patch has weak product leverage. Composition tests the architectural/ownership boundary directly, is reversible, and carries a more valuable kill condition. Native C acceleration O218b/c and sparse/hardlink/ZIP publication remain concurrent owners. No duplicate implementation of their mechanisms.
