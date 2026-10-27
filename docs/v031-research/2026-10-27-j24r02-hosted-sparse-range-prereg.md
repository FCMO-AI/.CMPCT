# J24R02 — hosted full-Reader sparse selective-range court (preregistered)

Date: 2026-10-27
Status: PRE-RESULT / FROZEN
Owner: staggered Phased2 activation, independent *evidence lane*, not the J24R01 implementation owner
Exact inherited J24R01 candidate: PR #584, `70336307312b5b277f0885c0057d2cddab0aefc1`
Exact original owner baseline: PR #569, `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`
Released v0.30.0 / on-disk revision 24: unchanged; no proposed product mutation.

## Decision question and source custody

Does the **already committed** J24R01 `bisect_right` S_SPARSE range implementation retain its >10x high-extent theoretical/micro speed benefit when measured as genuinely installed Python Readers, against the unchanged J24C02 linear Reader using **identical independently framed r24 bytes**, while avoiding material small-extent wall/CPU and memory regressions? This is a hosted experiment using the existing, unchanged `research/j24r01_sparse_range_abba.py` oracle from PR #584, not a new range implementation, scoring system, or release benchmark.

## Baseline, mechanism, controls, skeptical alternatives

- Baseline: #569 linear scan through authenticated sparse extents, already has source-exact semantic admission, signed-journal recovery, and diverse platform guards. Original J24R01 local algorithm-only numbers show ~90.6x/1,373x acceleration at 4,096/65,536 extents, but slower at 1–4 extents (0.76x/0.84x). Those numbers do **not** prove full Reader behavior.
- Candidate: #584 binary search on authenticated strictly increasing extent-end geometry; `bisect_right(key=...)` avoids creating an O(E) side index but adds callback overhead.
- Strong simple control: run old exact Reader and new exact Reader as separate **installed** packages with same process startup/import, same fixture bytes, external working directory, identical Python runtime. Do not trust a hot-only Python list microbenchmark as full-product evidence.
- Alternative explanations: Python setup, import overhead, fixture preparation, cold-open structural validation, or decoding could dominate; micro speed might disappear in authentic Reader. Small E may legitimately lose because callback overhead exceeds scanning. Full cold RSS may grow independent of range timings.
- Invariant: same full/selected logical bytes for each fixture, unchanged hashes of physical archive and underlying source; malformed geometry still rejected by unchanged strict admission. No formatter, codec, benchmark, evaluator or release-law edits.

## Frozen experiment and kill/narrow rule

Use the inherited J24R01 instrument **without edits** on Ubuntu 24.04, Python 3.11. Build two isolated installs from exact `#569` and `#584` source trees with dependency bytes held equal. Require source hashes from the installed modules to match the matching Git blobs; forbid workspace source imports. Four independently generated fixture scales: 1, 4, 4096, 65536 sparse extents. Use the original instrument's three interleaved ABBA rounds, four source positions per round, 48 fresh subprocess observations total (6 per arm per scale). All queries must byte-match the independent full logical oracle. Record open wall/CPU, batched range wall/CPU, host RSS and archive bytes; preserve raw observations + fixture SHA.

Decision is **SELECTIVE_HEADROOM_CONFIRMED_SCOPED** only if 65,536 median range wall is >10x better on the candidate, all semantic/source controls pass, and the small-E wall/CPU costs are clearly disclosed. Explicitly mark `SMALL_E_PROMOTION_DEBT` if either 1 or 4 extent cost exceeds the baseline by >10% AND >0.1ms for the 256-range batch in wall or CPU. This two-part small-E materiality signal is for prioritizing productization work, not a new release threshold; always report absolute differences and opposite interpretations. If high-E benefit fails or identity/semantics fail, preserve the negative. Hosted three-OS semantic tests of existing J24R01 are supportive portability evidence only, not three-host ABBA. No promotion credit from this experiment, no relaxing <5%/3ms official gate or zero-byte size rule.

## Verification, outcome, self-critique

Independent receipts must check 48 samples, exactly six per arm/extent count, full ABBA identity and source fingerprints against historical Git trees, same archive per baseline/candidate, raw values finite/nonnegative, and recompute medians and decisions rather than trusting only a printed PASS. An independent tester should also verify that the evaluator didn't drop unfavorable samples, alter the source, silently run the same code twice, or label a source identity rejection as a product slowdown.

Only after observed results append a separate outcome note; **do not edit this prediction**. A future run may compare the independent full release gate and full-stack portability, but this experiment cannot certify them. No changes to docs/discovery/STATE.json (currently claimed by #574). Stacking under #584 rather than editing its owner branch avoids concurrency collision; communicate a result to #584/#569.

Scientific classification: COST-BOUNDED PRODUCT CANDIDATE EVIDENCE, NOT CANONICAL PRODUCT CREDIT. Exact run/artifact identity and unresolved source/CI blockers must be preserved on any failure.
