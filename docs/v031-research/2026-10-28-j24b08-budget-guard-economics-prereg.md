# J24B08 — Exact-source extraction-budget guard economics (preregistration)

Date: 2026-10-28 UTC. **Scientific independent execution/economic court; no product source edits, merge, release or format/version authority.**

## Source and coordination
- Released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Direct owner candidate: [#690](https://github.com/FCMO-AI/.CMPCT/pull/690) at EXACT `adcf38cb5be022567c1faf6538aefeef2f6b72de`, Reader Git blob `20f6e257a07a61a4c1aebe23ae23e4109d6c41c8`.
- Existing #688/#689 prove negative symlink cancellation; #690 repairs only signed negativity/type. [#693](https://github.com/FCMO-AI/.CMPCT/pull/693) independently proves a **separate nonnegative hardlink undercount** and owns that falsifier. Do not duplicate or replace any owner implementation. `docs/discovery/STATE.json` is a stale cache with a separate active owner (#574); do not overwrite.
- This preregistration must land as the first child commit, **before** research script and hosted measurements.

## Primary scientific question
Does the minimally patched, **installed** #690 Reader have a confirmed extractall timing regression relative to its actual released source on accepted, unchanged, equivalent-semantic r24 archives, once the full one-pass guard is charged? Separately, does the scalar guard itself add meaningful per-row CPU cost?

## Predictions and kill/narrowing
- Exact same Builder-produced archive, size, recorded byte hashes and selected subset of extracted filesystem semantics for both engines. No malformed data in performance arms; no security-equivalence claim to unsafe released source.
- Prediction: candidate remains within direct-base **5% AND 3 ms** timing noise/regression boundary on full accepted extraction at at least N=4096 ordinary files, while O(N) guard component overhead may be measurable. The numerical rule is borrowed as a diagnostic from `docs/PERFORMANCE_RELEASE_GATE.md`, **not** a substitute for the full release parity gate or a prospective tuning opportunity.
- **Falsify** a clean economic result if any sample has wrong output, source/wheel does not match pinned Git source, archive/metadata differs between arms, or candidate median slowdown clears both >5% and >3ms for the same geometry/host/mode after repeated observations.
- If medians disagree across systems or timing variance overlaps effect, mark ambiguous and require more controlled evidence, never call it a win.
- Expected decision: close or quantify **only** the timing/read/admission portion of #690's promotion debt, with a clear residual hardlink and full product gate remaining open.

## Strong controls
1. Released real Python Reader module loaded unmodified from `git show 80c358f...:src/cmpct/reader.py`, under the same installed unmodified `cmpct` package supporting modules as candidate; the historical Reader blob is checked.
2. Candidate Reader is the actually installed source from #690 pinned at exact HEAD. Check Git-blobs, installed module content, and unchanged Builder/codec files.
3. Generate deterministic but generic file trees only once per geometry via unchanged `Builder(...,workers=1,reproducible=True)`; archive SHA and complete output sha/path counts are controls, not free gifts to the algorithm.
4. Alternate base/candidate by ABBA order, fresh Reader/mmap per extraction, separate open and extract times, with cleanup, output inspection and hashing excluded from measured extraction region.
5. Both `max_bytes=None` and exact admissible cap, N=128 and N=4096, raw monotonic wall+process CPU repetitions, same process for the key library comparison. One large-file control only if the budget permits. Startup/build excluded from library extraction timings.
6. Separately use a source-equivalent scalar scan oracle for 100k synthetic valid row tuples to locate overhead. That oracle is **component-only**, not product evidence. Never compare a candidate with full semantic admission against an uncharged unsafe control as if security were equal.
7. Windows CRLF checkout/wheel normalization can differ from Git byte text; compare exact Git blobs and normalized installed source, preserving raw hashes, never silently weaken identity.

## Adversarial / alternative explanation
Dominant extraction work is filesystem creation + decompression/packing; the scalar check may be below noise. Conversely a hot-cache/micro-only result cannot substitute full installed Reader. Test an original archive with symlink/hardlink only as an untimed semantics follow-up, not a fabricated perf win. A crash/recovery/same-inode source mutation is outside this economic court. Resource memory, sparse allocation, filesystem race resistance, negative and nonnegative alias lengths, and full archive-size parity remain separate product gates.

## BONK / opportunity
- Directly changing #690 Reader duplicates owner implementation: reject.
- Re-running signed negative and #693 nonnegative falsifiers: existing direct evidence already answers them.
- New representation/codec now: low opportunity value versus confirmed published resource defect.
- **Selected:** small exact-source same-input economic court with independent raw receipts. A negative closes a promotion question; a positive identifies real timing debt. A best-case zero difference only narrows overhead, never proves full correctness.

## Scientific scope / release law
No product file, frozen evaluator, benchmark, format, version, release lock, metric gate, or `STATE.json` changes. This is draft research evidence; separate installed source identity and raw sample provenance are mandatory. Promotion remains blocked by #693 and other signed size/physical-owner guarantees irrespective of the timing result.
