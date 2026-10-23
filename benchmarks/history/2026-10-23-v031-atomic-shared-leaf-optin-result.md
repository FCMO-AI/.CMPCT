# v0.31 — optional atomic publication for pre-existing physically shared leaves: bounded decision result

Date: 2026-10-23
Status: **FOCUSED PRODUCT VALIDATED, RESEARCH ECONOMICS MEASURED, CONCURRENT SECURITY FALSIFIED, RELEASE BLOCKED.**
Authority: draft [PR #297](https://github.com/FCMO-AI/.CMPCT/pull/297), stacked on owning [PR #294](https://github.com/FCMO-AI/.CMPCT/pull/294) `700fa74df7d9101b3d00322ab5b3606ee64faf88`. The owner remains unchanged; no merge/release.
Prospective prediction: [preregistration](2026-10-23-v031-atomic-shared-leaf-optin-prereg.md) committed **`69655aac9347d53e955c73081fb2d0722554032a` before any implementation or measurement**.

## Problem and decision

The parent's static preflight refuses a direct-truncate regular destination file when `st_nlink>1`; it prevents overwriting an outsider's shared inode but also refuses **legitimate in-root hardlink aliases**. Does a conditional **new-inode, same-directory atomic publisher**, exposed only through `CMPCT.extractall(..., atomic_shared_leaf=True)`, recover extraction while preserving the old outside inode, the archive's logical bytes and default strict refusal?

**Within the specifically tested static POSIX/Linux scenarios, YES.** Ordinary default behavior `atomic_shared_leaf=False` is unmodified, archive bytes and revision 24 unchanged. Atomic opt-in intentionally breaks the old destination hardlink relationship: the untouched sibling retains old content/inode, the new output leaf receives a different inode; archive-defined hardlinks can reestablish their own new identity. This is *not* an equivalent destination filesystem semantic to `O_TRUNC`.

## Exact-source hosted product evidence

Final focused product court [GitHub Actions run 40037986890](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037986890), exact source HEAD **`4a4161097fe51c4308da47d13c8dac7516f8e2d2`**, corrected Reader Git blob **`d1fdf5839c5ead102b7dd5787bb99215c8fbff3b`**. Installed genuine CMPCT package with Rust native component, actual Builder r24 artifacts; source blob pinned in dedicated workflow.

- **9/9 original parent controls PASS** in 0.10s, unchanged tests: external alias rejection (BLOB, nested, sparse, PACK, VZIP); safe atomic CDC, single-link reuse, unsafe explicit opt-out and intentional benign hardlink rejection *by default*.
- **15/15 new opt-in controls PASS** in 0.13s: external BLOB, nested, sparse, eight-ZIP PACK, VZIP, 255-byte POSIX NAME_MAX; in-root shared sibling identity break; preserve old mode when metadata=False; decoder error cleanup; atomic replace error cleanup; ancestor symlink rejection; CDC control; **two distinct archive-file leaves sharing one destination inode**; archive-owned hardlink reconstruction after owner publication; late failure on second sparse extent leaves original shared inode untouched and temp removed.
- On protected cases, outside inode, size, content and hash unchanged. Sparse holes remain physical holes in tested 16MiB file, not written as 16MiB zeros.
- A late sparse failure **does not roll back earlier independent archive members**: this is **per-leaf publication**, not archive-global transactionality.
- Same-runner honest research and negative evidence are *not* generalized to concurrent security, platform parity or release.

### Original implementation falsified, then corrected without changing evaluator

First candidate Reader blob `562b6af136c252ddc8ff25f968c5c1d4d3760408` passed 9 inherited + 12 new controls at [run 40037024981](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037024981). The next newly preregistered actual-Reader test revealed a hidden **within-extraction ownership transition**: two destination paths share inode X (`st_nlink=2`); publishing the first member atomically lowers the second member's remaining old-inode count to **one**, with no concurrent actor. The helper's redundant second `nlink>1` requirement then rejected the second file. [Negative run 40037494067](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037494067) recorded **9 old PASS; 12 new PASS / 1 FAIL** against the original helper. A local independent POSIX new-inode control also reproduced the 2→1 transition.

Corrected code retains the preflight selection claim and checks `S_ISREG` at staging time, **not** a stale link count. The same new test and all inherited controls subsequently pass on the corrected Reader blob. This does **not** establish TOCTOU safety: a concurrently exchanged *regular* inode can still be observed, and parent pathname pivots remain possible.

Prospective counterfactual: enumerate multiple archive destinations referencing the same pre-existing inode *before* implementing any repeated ownership check. The causal distinction between preflight ownership and mutable in-extraction link-count metadata would have revealed the failure earlier. This is a local transferable observation, not evidence to rewrite Discovery Engine doctrine.

## Actual-Reader charged research economics (not release parity)

The dedicated hosted court runs **7 repetitions**, rotating three arms on exactly the same archive per case: A = single-link direct legacy extraction; B = preexisting shared hardlink + opt-in atomic publication; C = single-link `atomic_shared_leaf=True`, which should remain the ordinary fast path. Library extract timing excludes process startup and full Builder creation; CPU measured in-process. Inputs and logical output SHA are checked. **A versus B differ in existing destination inode semantics**, so these are *cost indicators*, **not equal-semantics speed competition**, and cannot be used to pass the frozen performance gate.

From [run 40037986890](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037986890), median measured library wall milliseconds (7 samples):

| Genuine Builder representation | Final CMPCT archive bytes | A single default | B shared + opt-in | C single + opt-in | B–A extra wall |
|---|---:|---:|---:|---:|---:|
| S_BLOB, ~64KiB | 926 | 0.144228 | 0.179531 | 0.150177 | +0.035303 ms |
| S_SPARSE, 16MiB logical | 1,116 | 0.221304 | 0.284670 | 0.216236 | +0.063366 ms |
| S_PACK, eight ZIPs | 1,188 | 0.735711 | 0.778776 | 0.918246 | +0.043065 ms |

Runtimes are short and noise-sensitive; CPU medians and all raw repetitions must be consulted, not just the displayed medians. Source fingerprints/output checks appear in [raw ABBA artifact #12538057008](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037986890/artifacts/12538057008), artifact ZIP SHA-256 `18ae5ed991d5fcf3640354f46fe391ac427fb03a101ab1713f6bd29853346d5b`. Real complete RSS, temp disk peak, cold-open, platform and durability remain unmeasured by this court.

## Critical negative semantics: pre-existing destination xattrs

A separate authentic Reader xattr oracle compared the three modes using **Builder fidelity mode `reproducible=False`**, necessary because the Builder explicitly **erases host xattrs in `reproducible=True` mode by contract**. The first run of the experimental instrument incorrectly used reproducible mode and failed its archive-source-xattr restoration assertion; the instrument premise was corrected, not the product behavior or assertion.

Hosted exact-head [run 40037986890](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037986890) then proved:

| Mode | Old destination xattr retained | Archive source xattr restored | Old outside alias unchanged |
|---|---|---|---|
| Existing single-link, metadata=False, legacy direct | **YES** | No | YES |
| Shared-leaf opt-in, metadata=False | **NO** | No | YES |
| Shared-leaf opt-in, metadata=True | No | **YES** | YES |

This is a **real compatibility tradeoff** of publishing a new inode. Owner/group/ACL, inherited security metadata and other host-dependent semantics require separate evidence; do not invent full metadata fidelity. [Raw metadata artifact #12538346244](https://github.com/FCMO-AI/.CMPCT/actions/runs/40037986890/artifacts/12538346244), ZIP digest `0996eedbb9a1b9c861602530f614b8b7c9bcbb37989d40ba9531ef5fadbf5d86`.

## Independent security negative: atomic leaf is NOT root confinement

The same hosted workflow runs a genuine Reader deterministic adversary that replaces the already-validated destination **ancestor directory** with a symlink to another directory **after preflight and before materialization**. The output successfully replaces the outside directory's *leaf entry* despite the new-inode publisher; the old outside inode's content remains unchanged. The successful negative witness prints `REAL_READER_RACE_NEGATIVE_CONFIRMED`, classification `RESEARCH_FALSIFIER_NOT_PRODUCT_SECURITY_PASS`.

Therefore **neither current static preflight nor scoped `os.replace` protects the caller-selected root against concurrent pathname pivots**. This is Issue #265 debt requiring fd-rooted no-follow directory traversal **for every write and metadata operation**, with explicit definition of path-root vs opened-inode identity. This is an adversarial falsification, not a completed security feature.

## Current promotion boundary and next executable decision

The source is draft-only: version remains shipping **v0.30.0**, on-disk revision **24** unchanged. The parent `#294` and symlink owner `#269` remain distinct; #255/#270 sparse writer is an independent owner whose atomic publication semantics must be reconciled before integration. No merge or release.

The earlier exact-parent full Tests run [40032511249](https://github.com/FCMO-AI/.CMPCT/actions/runs/40032511249) gave 799 PASS and four inherited old v0.30 fingerprint/public attribution failures; its performance gate [40032511225](https://github.com/FCMO-AI/.CMPCT/actions/runs/40032511225) failed on those same tests before producing valid parity benchmarks. No changes to frozen tests, thresholds or version evidence are authorized. Current exact-HEAD full CI must be consulted independently; an administrative workflow SUCCESS with substantive performance job SKIPPED is **not** a performance pass.

**Disposition:** preserve as opt-in research/product candidate with 24/24 genuine focused tests and negative boundary evidence, not a default safety upgrade. Cheapest decision-changing next target: determine whether the controlled break in *existing destination xattr/owner/ACL* semantics can be explicitly documented as an opt-in contract, while a separate fd-capability design addresses concurrency. Then reconcile actual Reader writer selection with PR #270 sparse atomic ownership and execute same-source general/native/portability and genuine parity gates without weakening the parent.

No Discovery Engine policy change is earned from this bounded episode; `docs/discovery/STATE.json` is a staleable cache and was not blindly overwritten.
