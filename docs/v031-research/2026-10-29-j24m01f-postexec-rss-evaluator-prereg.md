# J24M01f — Linux post-exec sparse verification memory court (preregistered 2026-10-29 UTC)

**PREDICTION BEFORE IMPLEMENTATION.** This is a *test/evidence attribution repair*, not a Reader optimization, a new product capability, or a reduction in the strict 128-MiB memory ceiling.

## Authority and exact sources
- Released main `80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0 / revision 24); source integration candidate #738 at `ec112a87ea34349b63885f3f0bea4689f192bd2f`.
- Original inherited test `tests/test_j24v01_sparse_verify_streamed.py`, Git blob `dc31bd4a46c117e6621a76a91b7bdeef85579ebf`, unchanged in this preregistration commit.
- Relevant fixed negative: full suite #40900353249, `795 passed / 5 failed`; original separate Python child `ru_maxrss=180420 KiB` exceeds strict `<131072 KiB` assertion; 4 other historical release/custody metadata failures.
- Real parent `ru_maxrss` immediately before child fork/exec = **180420 KiB**. Separate same-archive child reported `ru_maxrss=180420` before importing CMPCT, but `/proc/self/status:VmHWM=14780` pre-import and `23536` after complete verify. Exact Reader blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`; input `9380bb61e19c3bce95eebe99029402996380cdb02df3dfabd77c1c2edaaaa2e9`, 1162 physical bytes / 256 MiB logical / 8192-byte sparse data extents. Research owner #768 documented this without changing tests.
- Independent J24M01e Linux no-CMPCT kernel control confirms `ru_maxrss` can carry parent high-water through fork+exec; prior J24F08 #549 / O95 #453 already use post-exec `VmHWM` as a more accurate metric. Reuse their conceptual donor rather than inventing a new metric.
- #738 remains responsible for Reader/compaction code and production promotion, and #749 remains a separate physical-publication security veto.

## Primary falsifiable question
Does using Linux's **actual new process** post-exec `VmHWM` for the already separate 256-MiB sparse `CMPCT.verify()` worker restore source-authenticated full-suite resource evaluation, while retaining the same unmodified strict `<128 * 1024` KiB predicate, actual decoded bytes, physical input, Reader code, and verified-member count?

## Candidate intervention (test-only)
In the original sparse resource-test's in-child script:
1. Keep the *same* Builder-produced genuine 256-MiB sparse file, subprocess startup, CMPCT import/open/verify and `verified==1` invariant.
2. Read `VmHWM` in KiB from `/proc/self/status` **after** the complete verification; reject an absent/invalid counter rather than silently falling back to inherited `ru_maxrss`.
3. Keep `peak_kib` and its existing original **strict less-than 131072 KiB assertion** exactly, but bind it to the post-exec HWM. Retain `ru_maxrss` under a *distinct diagnostic* name in the result for causal provenance.
4. Add a separate Linux-only independent subprocess positive control: touch substantial parent memory before fork+exec, verify child `ru_maxrss` carries that high-water and post-exec `VmHWM` stays materially lower, without importing CMPCT. The independently reported counter must be positive/finite, or fail. Do not modify `pytest`, limits, Reader, Builder, format, release policy or frozen benchmark comparators.

## Alternatives / strongest simpler controls
A: leave `ru_maxrss` (simplest code but fails to isolate memory after exec on actual Ubuntu; repeated historical false high-water). B: subtract parent peak from `ru_maxrss` (not valid; historical max cannot be subtracted to recover actual child max). C: use `VmHWM` after exec (direct kernel process-local metric, Linux-only; small additional /proc read). D: `tracemalloc` (does not capture native/allocator RSS and perturbs memory). Choose C; keep D/B rejected.

## Predictions and disproof
- Under full original Linux test order on the exact candidate source, the 256-MiB sparse test should switch **FAIL to PASS** with child `VmHWM <131072 KiB`. The remaining four unrelated failures should remain visibly failed, not greenwashed.
- The separately controlled artificial high-water parent should yield child `ru_maxrss` at least **32 MiB greater** than child `VmHWM` after child exec while `VmHWM` is positive and limited; this validates that old and new metrics are not synonyms. If Linux cannot provide positive VmHWM or the positive control fails, instrument is invalid.
- If the unchanged archive/Reader under full suite produces `VmHWM >=131072 KiB`, the hypothesis is falsified and **the same 128-MiB predicate must still fail**. Do not weaken thresholds or substitute another low-memory archive.
- Distinguish scientific court SUCCESS from whole-suite PASS. Preserve the four unrelated historical failures, prior source blobs and raw artifacts.

## Costs and promotion gates
- One short `/proc/self/status` read in resource-only test child after verification, not in production. Additional subprocess and transient 160-MiB touched parent allocation in isolated positive control; no product I/O/storage/memory change. This test is Linux-only; Windows/macOS should skip it unchanged.
- No claim of improved product runtime or release-readiness. CI may remain red because of four inherited metadata/release tests. Full application/product and stage inode custody #749 remain unresolved.
- Transfer exact result to owner #738. No shared Discovery STATE write: current stale cache / #574 ownership; no broad policy amendment from one research episode.

## Decision rule
If positive control and actual full-order sparse test pass, declare **evaluator attribution corrected on this source/host**; do not relabel historical run #40900353249. If either fails, preserve raw negative, classify as unresolved and choose a different causal measurement method instead of moving the ceiling.
