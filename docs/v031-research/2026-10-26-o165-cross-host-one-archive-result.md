# O165 — Same-authentic-archive Linux→macOS r24 physical tree transfer (2026-10-26 UTC)

**Decision: NARROW POSITIVE — SINGLE ARCHIVE PORTABLE TOPOLOGY, NOT STRICT CROSS-HOST PHYSICAL IDENTITY.** Research/evidence only. No source product, on-disk format, benchmark, release or normative policy change. Preregistered *before* instrument/CI in commit `e0f3d3a52bd827519260ccf0f0bcc94fcd6c9099`.

## Source, run and independent audit

- Parent O162 source exact HEAD: `34fe4b6dc5cdf9e0bbe8cd61867f61b5c478ce15`; this child result-bearing code HEAD: `2157757659b95d45126b07ae2262e49f0aba7367`.
- Installed Builder Git blob: `663ef0922992b1fbb8f19e6eea88d55c10a56044`; Reader `e716233403dabd0966863c45635e18fa5ac6afb8`; O155 static oracle `0bef46e8d1944ff327063c66edc9bbc29fa58481`; original O162 fixture/harness `ed352ad593a41ed541b3cbb6774c8c5f447f3741`. Both hosted jobs checked source identity and installed CMPCT outside the source tree.
- [O165 exact-head GitHub Actions 40288932352](https://github.com/FCMO-AI/.CMPCT/actions/runs/40288932352): Linux producer job `121459147642` **SUCCESS**, independent macOS receiver job `121459371724` **SUCCESS**.
- [Original single Linux archive and producer receipts — artifact 12634314680](https://github.com/FCMO-AI/.CMPCT/actions/runs/40288932352/artifacts/12634314680). [macOS receiver full strict/portable JSON — artifact 12634904719](https://github.com/FCMO-AI/.CMPCT/actions/runs/40288932352/artifacts/12634904719).
- Raw downloaded artifact ZIPs were independently examined after the hosted run. The **actual 1,939-byte CMPCT binary**, not merely logged values, begins with `CMPCT24\\0` (r24) and has SHA-256 `f195d05c2719fec1e1759895d90ab06781a33d1a27c099093dcfb4366ddb0cd0`. This exactly matches the producer receipt, producer summary and macOS receiver receipt on the same Git HEAD.

## Measured product behavior and its exact scope

The Linux sender constructed O162's unchanged synthetic 10-entry quiescent POSIX tree once and created **one archive**. Installed Linux Reader verified and extracted those exact bytes with its source O155 strict physical manifest intact. This is the strong same-archive sender control.

The macOS receiver did **not** construct or recompress any source tree: it downloaded that identical archive, verified its SHA/byte size, ran installed `cmpct verify` and `cmpct extract` (both exit 0), measured the resulting physical tree with the unmodified O155 oracle, then tested a hostile hardlink mutation. The source archive bytes were unchanged after extraction.

- Linux strict source digest: `8e72d2b9273fe50b30a6bf84ee275d9250c339c48f26e17180d13f619ef60e94`.
- macOS strict output digest: `2610ed72a12d168e46326a55273dd60fe532d90f616b0e025cbb02e2a3e6845b`.
- **Strict equality is FALSE.** This is a real physical distinction, not a product-representation equality.
- Independent full-manifest comparison found **exactly three entry-field differences**: symlink `ln-dir`, `ln-file`, `nested/ln-nested` physical mode `0777` (Linux) versus `0755` (macOS). Names, raw link targets, all regular contents and hashes, directory/file/root POSIX modes, entry types and the hardlink equivalence group match.
- Separately labeled O165 portable view omits **only** the physical `mode` field on entries whose `type == "symlink"`. Linux/receiver projected digests both equal `0292ffc4d4e40d43c1d6e0cbd06616e5024b44403d6705fb9f4cadac50faeaa0`; full portable manifests compare exactly equal.
- Direct physical `os.path.samefile` verified `a-base.bin` and `nested/hardcopy.bin` refer to the same restored inode on macOS; O155 independently records the same two-member hardlink partition.
- Hostile control severed the restored hardlink while copying identical payload and mode: bytes still match, inode identity no longer matches, and the portable digest changes to `3824ffd79f60c465424c2588cb68b0ec22b8a4b66ef469a3c5e07dfc6a03da1b`. The projection therefore does **not** waive hardlink fidelity.

## Falsifier / alternatives / strongest negative

A single non-symlink-mode difference would have failed this court. No such difference occurred. The strict physical equality hypothesis is **explicitly refuted** for this artifact; the narrowly projected semantic equality hypothesis survived. Do not normalize away or relabel strict differences. A checksum-only result would not prove filesystem reconstruction, and independent archives per host would not prove cross-host transfer.

No evidence of general cross-host equivalence, arbitrary-byte POSIX filenames, destination Unicode/casefold collisions, ACL/xattr/timestamps, sparse physical allocation, hostile concurrency, transactional/crash durability, Windows semantics, native portability API, full tree size economics or broad representative workloads. Mac CLI verify/extract wall times are process-start-inclusive single observations and are **not** credible speed/product performance results. Historical O155 comparator and source/O162 evidence remain unmodified.

## Exact-head CI and inherited debt

Specialized O165 exact-head two-job cross-host workflow **SUCCESS**; CI topology and version discipline succeeded on the result-bearing source HEAD. Engineering Evidence initially failed due to three required **PR description headings** (not a code/test failure); rectify PR metadata, never weaken validator. General v0.31 tests were still running at the result-writing cutoff. Parent O162 #500 general test exact-head run `40283118280` completed **4 FAIL / 782 PASS**, from known historical source-custody/surface/classifier assertions also seen in preceding O155, not attributable to O165 code. O165 itself does not yet have an all-green general/regression/release claim.

## Counterfactual / discovery disposition

The decisive cheap discriminator was to send **one binary archive** with an original strict source witness to a second host. A portable projection declared *before* observing the outcome prevented both overclaiming exact physical equality and dismissing valid transferable byte/topology semantics. Neither a new representation, a discovery-policy change, nor a version advancement is earned. Discovery shared `docs/discovery/STATE.json` was not modified (PR #440 retains its owner).

## Next action

Owner reconciliation: make O165's raw source-exact Linux→macOS test a continuous *separate* portability court for an explicitly approved portable metadata contract; consider reverse-direction independent same-archive transfer and held-out adversarial names only if decision-changing. Do not fold the O165 projection into the strict O155 witness or use it as permission to relax the released archive/extractor's semantics. Resolve inherited CI red and full product/cross-platform release gates in their own ownership lanes.

## Final-head code-independent repetition and cross-run boundary

The result document commit `e7a4e7d6737a8b535f94149c2fe937fabe1b6acf` itself triggered a **new exact-head two-job court**, [Actions 40289443117](https://github.com/FCMO-AI/.CMPCT/actions/runs/40289443117). Linux producer job `121460767285` **SUCCESS**, independent macOS recipient `121461042305` **SUCCESS**. Fresh raw artifacts: [original archive + origin strict receipt #12636085072](https://github.com/FCMO-AI/.CMPCT/actions/runs/40289443117/artifacts/12636085072), [macOS strict receiver #12635825707](https://github.com/FCMO-AI/.CMPCT/actions/runs/40289443117/artifacts/12635825707). Those ZIP artifacts were downloaded and independently read after the run.

The second producer generated **1,935 B**, SHA-256 `1358a4dd1300bdb36dca701b9b46effd26868037aacd3d8326c3bd8534a3210a` rather than the earlier run's 1,939 B / `f195d05c...`. Within the second run, the original binary matches **exactly** between producer, downloaded artifact and macOS receipt, on the same source Git HEAD; the receiver passes the same payload/physical-hardlink/projected-manifest/hostile-mutant tests. Both independent sender source O155 strict manifests are **byte-equivalent as semantic JSON** and retain source strict digest `8e72d2b9273fe50b30a6bf84ee275d9250c339c48f26e17180d13f619ef60e94`; receiver strict `2610ed72a12d168e46326a55273dd60fe532d90f616b0e025cbb02e2a3e6845b`, portable `0292ffc4d4e40d43c1d6e0cbd06616e5024b44403d6705fb9f4cadac50faeaa0`.

**Do not interpret independent source archive size/hash differences as cross-host transfer corruption or deterministic size regression:** the O155 witness intentionally omits timestamps and other metadata that can vary when reconstructing the source fixture separately; source Git HEAD also differs by a documentation commit. A causal diagnosis of these cross-run archive bytes was not performed. The measured claim is one *identical binary* crossing the host boundary **inside each run**. The smallest future discriminator for deterministic production would pin ALL archived metadata (including timestamps) and both engine source identities, then compare real full bytes on one host—separate from this portability test.

An independent local audit also recomputed O165 portable digests directly from the raw hosted O155 JSON (without invoking the O165 hosted projection routine), verified only three symlink-mode differences, and challenged the portable hash: changing a **file** mode or a symlink **target** changes its digest, while changing only a symlink's excluded physical mode does not. This supports the exclusion's narrowness. The oracle remains scoped to its documented fields; O67 [#421](https://github.com/FCMO-AI/.CMPCT/pull/421) independently shows *hardlinked symlink inodes* are not represented by the tested O162 fixture and are not implicitly certified here.

CI on the documentation HEAD: specialized [40289443117](https://github.com/FCMO-AI/.CMPCT/actions/runs/40289443117), version discipline, CI topology, R36 and corrected Engineering Evidence [40289774416](https://github.com/FCMO-AI/.CMPCT/actions/runs/40289774416) **SUCCESS**. Engineering Evidence had earlier metadata-only failures due to missing required PR headings/markers; these were corrected in the PR description without changing the validator. Generic tests had not finished at this addendum cutoff, and the parent O162 historical CI red remains separate.
