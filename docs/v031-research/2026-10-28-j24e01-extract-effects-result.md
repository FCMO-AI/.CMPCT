# J24E01 — cross-kind extraction-effect model outcome and negative knowledge

**Research-only. Product source, on-disk r24, release v0.30.0 and discovery policy untouched.**
Scientific PR [#712](https://github.com/FCMO-AI/.CMPCT/pull/712), source base `main@80c358f8824ec1b20d349c92ed94c898090969b0`; first immutable preregistration `15600e4e86c95b1d1fa88ed45dfb9fe6f2cb2ac4`.

## Primary question and decision

**Universal exact write effects from decoded metadata alone: FALSIFIED for S_VZIP.** Existing authentic, same-physical-data, re-hashed revision-24 virtual-ZIP counterexample [#623](https://github.com/FCMO-AI/.CMPCT/issues/623) makes file size and recipe total agree while actual reconstruction is shorter. No metadata-only boolean/scalar that trusts those two fields can certify exact physical output. Some regenerated Deflate stream lengths likewise cannot be known without equivalent recompression or an external authenticated witness (see [#640](https://github.com/FCMO-AI/.CMPCT/issues/640)). Don't rerun this known decisive physical case just to create another scientific-green workflow. **Fail closed on S_VZIP unless a separately proven physical-recipe stream-length certificate is available**; historical VZIP support must not be silently dropped by any future product integration.

**Subset result under conditional authenticated-index/BHDR provenance:** a standalone pure standard-library research model, `research/j24e01_extract_effects_model.py`, structurally accounts direct blobs, symlinks, micro-PACK slices, fixed chunks, CDC, sparse extents, and iterative hardlink alias ownership before destination creation. It rejects mismatched row/physical metadata and the **four known quota-underflow shapes** from research #688/#693/#697/#700. Result is a *descriptor-geometry proof*, not archive authentication, exact bytes, output syscall safety, release correctness or successful product integration.

## Three scientific stages, with negatives preserved

1. **Initial frozen court** [Actions #40784919546](https://github.com/FCMO-AI/.CMPCT/actions/runs/40784919546), code `f8f2e6987801523e8fb8651539b57cec06f8ddef`: Ubuntu log **131 valid-graph errors + 200 mutant-assumption failures** (not infrastructure). Existing resolved alias-of-alias was misidentified as nonregular root; a longer sparse logical size with unchanged extents was actually a legal trailing hole.
2. **Prospective causal repairs** in `2026-10-28-j24e01-extract-effects-repair.md` frozen before corrected code. Memoize ultimate regular owner, not immediate cursor kind. Preserve original 2,000 seeds; replace nonhostile sparse mutant with strict negative-size mutant plus isolated direct physical mismatch. Repair does not touch product or lower the original H1/H2.
3. **Representation proof-gap extension** `2026-10-28-j24e01b-vzip-proof-boundary.md`: based on existing #623/#640 evidence, original all-storage-family hypothesis narrowed/rejected, not cosmetically reinterpreted. All 2,000 seed choices stay in the hosted court; valid VZIP schemas are counted as **uncertifiable**, rather than excluded or declared correct. Correct source-shape fidelity to actual six-field VZIP recipe and retain a separate physical-source witness as future prerequisite.

## Independent strong control / strongest critique

`src/cmpct/validation.py::_validate_index` already verifies most PACK/chunk/CDC/sparse shape constraints. Its remaining known gaps concern `S_BLOB` logical-to-physical size, K_SYMLINK, K_HARDLINK alias-owner sizes, VZIP physical stream output, and how the Reader uses verification **before** modifying destination. This research-model code **must not be blindly copied into production** as a second 160-line validator: double-scanning the same index adds CPU/memory, diverges semantics and creates two security oracles. Any product path should prefer extending/reusing the current bounded strict preflight and authenticating the already-owned effective index/physical records once. The legacy `extractall` creates `dest` before budget rejection, and filesystem containment/atomicity/TOCTOU are separate known gates. A valid metadata budget is necessary but not sufficient.

## Costs, controls, and uncertainty

All model cases are synthetic declared physical lengths, with an independently constructed expected-output sum. The 50,000-alias chain tests iteration without recursion. 2,000 original seeded graphs include all storage kinds; accepted subset and uncertifiable VZIP counts, 50k chain wall/CPU and exact final-host results must be read from the **latest source SHA's workflow**, not inferred from an earlier green. No full archive files were built by this PR, no Reader code installed/modified, and no CPU/RSS/temp-I/O, physical data read, SHA content, general filesystem namespace or product benchmark was measured. Any positive finding is **research/oracle evidence only**.

## Counterfactual and next action

A source audit of `_validate_recipe` and the already filed #623 issue could have rejected the universal VZIP inference **before writing any code**. This is a transferable prospective BONK discriminator: for each reconstruction mode, distinguish `declared length agreement` from `provable materialized length` and search the repository's existing negative evidence before adding a general metadata guard. No repository-wide Discovery policy mutation is earned from this isolated episode.

**Next unclaimed decisive work** after source-exact hosted result: a focused owner-controlled integration experiment using the already authenticated effective index, with actual r24 signed hardlink/symlink/sparse/VZIP files, pre-mutation destination proof, and CPU/RSS costs. Existing physical-size and staged-publication owners #609/#615/#569/#573/#690 retain product implementation claims; do not duplicate them.

## Exact-head final evidence

**PENDING** until final source/court and current GitHub CI are reconciled. Earlier **three-host green** on research-head `720b35df74c0a616d5114928d029fa55cb51a0c7` is not retroactive credit for the later revised physical-recipe-oracle and telemetry files. No merge or release.
