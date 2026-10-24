# v0.31 prospective cross-owner salvage × cooperative Writer composition

Status: preregistered engineering/scientific court; not release authority.
Date: 2026-10-23 (America/Mexico_City).

## Immutable inputs and authority
- Target: `FCMO-AI/.CMPCT`; ship checkpoint v0.30.0 / format revision 24. No format, comparator, base, threshold, historical v0.30 lock, or release change.
- Owner A (Windows + POSIX transaction-wide Writer + Reader stack): PR #304 exact `fdb752b9e9ac72af74a44575b926e24ecacd812e`, `src/cmpct/transactions.py` blob `fd8d922ae5a6e77ab7e01bf599da16a14aca1cff`.
- Owner B (bounded unverified forensic candidate scanner): PR #293 exact `d311391903a50a3c18260c5404b19611d0434b1d`, `src/cmpct/transactions.py` blob `94c25029fdd167c00871aabbe8fe90fbe7490026`. Owns `src/cmpct/cli.py`, scanner tests, hardening, and focused workflows.
- Owner C (prospective v0.31 fingerprint and inherited four-red fix): PR #302 exact `2825253a2b40386df173b7f5497abffbe6539f91`, source-locked additive to B. Owns exact eight PR #266 blobs plus composition prereg/workflow.
- GitHub truth at start includes PR #309/#310 Windows contention research: do not reimplement Windows lease or relax their liveness limits.

## Problem
Each owner has positive separate evidence. They do not share one installed source. PR #302 and #304 are currently divergent in `transactions.py`: one includes bounded salvage, the other cooperative Writer lease. Promoting either by overwriting the other would silently lose a property. Latest general Test success on #302 (819) and on #304 (inherited Reader/Writer stack) cannot be combined by narration.

## Prospective hypothesis
Preserving Writer code **byte-for-byte outside the original `recover_blob_records` function**, preserving salvage candidate iteration **byte-for-byte from PR #293**, and taking the other owner paths at their original Git blob IDs yields an integrated v0.31 branch where:
1. POSIX/Windows cooperative Writer behavior and its existing focused courts remain unchanged;
2. forensic candidate enumeration and streaming CLI preserve all offsets and explicitly label claims `unverified` and generation membership `unknown`;
3. prospective candidate identity removes inherited four release-epoch failures without modifying v0.30 historical custody;
4. source-bound tests and full general tests work on **one installed candidate**;
5. ordinary creation/extraction bytes retain their inherited behavior (no compression or performance win claimed).

## Strongest simpler control and alternative explanation
The base PR #304 alone should already pass Writer tests but lacks bounded salvage; PR #302 alone passes salvage/prospective identity but lacks current Writer lease. A narrow snapshot-only source audit can prove no conflict, but cannot prove runtime interoperability. Equal-looking tests on two separate SHAs prove nothing about the union. The strongest simple control is byte-identity of owner subregions *plus* real installed product tests.

## Decision/kill
- Any change to Writer lease code outside the original recovery section; or any semantic modification inside the salvaged scanner is a provenance failure.
- Any actual lost update, Windows lease safety regression, destination/file escape, wrong candidate offsets, corrupted candidate classification, four inherited release custody failures, or in-place lock/version rewrite blocks promotion.
- Any current baseline timing or archive-size loss belongs in explicit debt; green tests do not grant release/performance credit.
- If source exact merging is unsafe, preserve independent owner branches and do not force-merge.
- Publish raw exact-head check status, including skipped/pending runs, and explicitly classify any Windows contention limit already documented by PR #309.

## Execution order
1. Commit this preregistration before code or new union tests.
2. Compose exact B/C owner blobs on top of A's HEAD using Git-tree overlays. Handle the single physical collision in `transactions.py` by splicing the exact B salvage candidate section over the A legacy recovery function.
3. Land isolated source-lock and interaction tests; preserve old owner tests unedited.
4. Execute hosted focused and full general tests; request the Windows hosted product court as triggered by ordinary PR machinery when available.
5. Reconcile CI and source identities; do not claim full green when a required job is omitted. No merge/release.


## Pre-implementation source-audit correction (2026-10-23; before composed product source)

The eight PR #266 prospective fingerprint source files are **already present byte-for-byte** on Writer PR #304: each matching Git blob agrees with PR #302. Therefore no source overlay of those eight files is warranted, and doing so would only duplicate already-satisfied custody. The correct minimal union instead preserves #304's prospective source receipt unchanged, adds #293's bounded salvage source+CLI+specialized tests, and reconciles the shared `transactions.py` and `docs/HARDENING.md` surfaces explicitly. PR #302's experiment-specific workflow is not transplanted because its narrower original-source guards do not describe the merged Writer transaction module. This amendment narrows the earlier prospective method without changing its scientific hypothesis, acceptance criteria, or evidence strength.


## O2 prospective hardlink-alias interaction (added after O1 hosted result, before O2 code)

Base exact-head source: `e522ae27bc7f9c69b3ff59dfc03f1c73c6ec4f63`. O1 Linux hosted 46/46 and Windows hosted 36 pass + 2 platform skips, both on the exact source. This O2 question is deliberately separate from the original O1 preregistration, not retroactively part of its prediction.

**Question:** When two archive pathnames are genuine hardlinks to the same inode, does a public cooperative Writer operation via one pathname preserve one coherent committed namespace and the same physically framed candidate offsets through *both* aliases? The physical candidate scanner must not claim an obsolete member is still logically live merely because its original blob remains on disk.

**Prediction:** Create an r24 archive using the real Builder; create `os.link` alias; check `os.path.samefile` before and after; collect identical original/alias candidate sequences; rename one member via the hardlink alias; both Reader paths verify the identical committed namespace; both physical candidate scans still agree on the same original candidates marked `unverified` and generation `unknown`. Do not infer the rename from header candidates.

**Control and alternative:** The inherited Writer POSIX and Windows suites already verify cooperative hardlink locking, and the inherited salvage suite already verifies framing. Neither tests the cross-product through an actual alias *after* a mutation. This additional test is bounded to one public Writer transition; no new algorithm needed.

**Kill:** Any successful transition that only one pathname observes, any altered physical header claim, incorrect trust elevation, or an unsupported system-level hardlink creation treated as a silent pass invalidates the test. The test must not alter the existing Writer's cooperative contention/wait contract.

**Evidence rung:** installed-package exact-source Linux and Windows test, plus launch of official r24/ZIP same-source performance receipt when the final latest test-bearing commit triggers it; raw results, including infrastructure failures, retained. No O2 result is asserted before execution.
