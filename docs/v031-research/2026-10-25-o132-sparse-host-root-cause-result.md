# O132 result — physical sparse eligibility explains macOS inherited Reader fixture red

**Scientific status: DECISIVE ROOT CAUSE, NOT A PRODUCT FIX.** Recorded 2026-10-26 UTC. Reference: [PR #480](https://github.com/FCMO-AI/.CMPCT/pull/480); [exact original prereregistered prediction](2026-10-25-o132-sparse-host-root-cause-prereg.md) committed at `d40a71f2de1206c61cc80e3cfa7e42714d1fb81c` before any scientific instrument code.

## Baseline and source custody
- Canonical v0.31 active development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; released v0.30.0 / revision-24 archive unchanged.
- O132 scientific branch starts from unchanged owner PR #294 `700fa74df7d9101b3d00322ab5b3606ee64faf88`. Original `tests/test_v031_destination_hardlink_leaf_alias.py` Git blob `ce3da2e0f6611ac624b75ab17d760173a8f03392`. Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`; codec blob `29526db4203723d83523fc95d074c346b63d7587`.
- Final measured instrument and JUnit court on O132 code HEAD `6e162a8ede618db9bc00849861594b51e3c36a4e` in [installed source-exact Actions run #40248182466](https://github.com/FCMO-AI/.CMPCT/actions/runs/40248182466). The event's synthetic PR merge sha `0dff0f0d7b70730d6c6db7c8f4c9f0176bdc1a37` is *not* the source ref used by checkout: workflow explicitly resolves `github.event.pull_request.head.sha`, and `head.sha` artifacts preserve exact checkout. No production merge.

## Direct scientific observations (each 16,777,216 original bytes)

| Host | Same-logical-content input | `st_blocks` (512-byte units) | SEEK_DATA/Hole | Direct codec result | Builder scan / actual archive storage | Complete `.cmpct` bytes |
| --- | --- | ---: | --- | --- | --- | ---: |
| Ubuntu 24.04 | Seek + write edge blocks | 16 (8,192 B) | Two data extents; interior hole | Sparse extents 8,192 B | S_SPARSE / S_SPARSE | 1,110 |
| Ubuntu 24.04 | `ftruncate` + `pwrite` | 16 (8,192 B) | Two data extents; interior hole | Sparse extents 8,192 B | S_SPARSE / S_SPARSE | 1,110 |
| Ubuntu 24.04 | Fully materialized zero middle | 32,768 (16 MiB) | No interior hole | None | S_CDC / S_CDC | 1,264 |
| macOS 14 | Seek + write edge blocks | 32,768 (16 MiB) | SEEK_HOLE advances to EOF | None | S_CDC / S_CDC | 1,264 |
| macOS 14 | `ftruncate` + `pwrite` | 32,768 (16 MiB) | SEEK_HOLE advances to EOF | None | S_CDC / S_CDC | 1,264 |
| macOS 14 | Fully materialized zero middle | 32,768 (16 MiB) | No interior hole | None | S_CDC / S_CDC | 1,264 |

All six logical inputs had **identical SHA-256** `e91b7faf9c1738b3ade9357d6ffeccee860e40385936ab98696bf503606f5109`. The exact installed Builder emitted the expected mode shown above. All six Reader `verify` and complete extraction SHA checks passed. Both scientific-host CI jobs ended **SUCCESS**; each received an independent receipt audit. This is an empirical result about the hosted filesystem, **not a universal APFS invariant** and not a comparable product compression win (the representations differ).

## Stronger builder-independent Reader safety court
The immutable hand-assembled revision-24 golden conformance record `tests/conformance/v24-sparse.json` (Git blob `002d29f71384bfe0213605eccc952f5ebc20df0b`, archive SHA `196838899361c8355578d8642644d48f35e62551e21ee761b66ce1254f0099e6`) contains one S_SPARSE file with holes and RAW/Zstd/Deflate extents. It is **not regenerated** by Builder.

Added `tests/test_v031_o132_golden_sparse_leaf.py`; the scientific workflow copies it unchanged outside `tests/` and independently audits its JUnit. **2/2 PASS Ubuntu and 2/2 PASS macOS**, no skip. Safe default extraction rejected an already-existing outside hardlink before modifying sentinel or archive SHA. Deliberate unsafe opt-out modified a temporary sentinel in-place with exact golden bytes, as the inherited contract allows, without modifying the source archive. These are **additional independent Reader S_SPARSE branch tests**, not a replacement or waiver of the inherited nine-case suite.

## Unmodified inherited regression: one Mac red deliberately preserved
- Parent #294 nine-test court: Ubuntu **9 PASS / 0 FAIL**, macOS **8 PASS / 1 FAIL**. Sole negative: `test_safe_extract_fails_before_partial_publication_on_preexisting_hardlink_leaf[sparse]`, `assert 5 == 3` at original line 97: actual **S_CDC=5** vs expected **S_SPARSE=3**. Failure occurs **before** the Reader destination guard and cannot be scored as a proven Reader regression.
- The workflow remains overall **FAILURE** due to the actual unchanged Mac court failure. We intentionally did not mark it allowed-to-fail, skip it, or revise the assertion. PR #472 and successor #479 also inherit this red.
- An earlier O132 run #40247905196's first inherited suite failed *during unrelated test collection*, Linux due to missing `zstandard` in `tests/conftest.py` and macOS due to `libzstd.so` linker lookup; subsequent workflow copied the original test file with bitwise equality to an isolated evidence directory, the exact existing #472/#479 method. This restored **genuine original nine-test execution** without editing the suite.

## Decision and counterfactual
**Confirmed scoped hypothesis:** Mac host physical allocation metadata (`st_blocks` equals full 16MiB; seek probes see no holes) causes the unchanged sparse eligibility prefilter to fail, so the real Builder selects S_CDC. Linux creates physical holes and Builder selects S_SPARSE. The strong dense control corroborates the causal discriminator; the observed failure is not a Reader guard result. `ftruncate` alone did **not** restore sparse physical allocation on this macOS runner, so it is not a portable repair.

Cheap prospective discriminator learned: record `(logical SHA, size, st_blocks, SEEK_DATA/HOLE, detected extents, actual index storage-kind)` for any filesystem-kind-dependent regression before rewriting the policy or relaxing a storage-mode assertion. Source/content equality does **not** guarantee physical extent equality across operating systems. This is a transferable experimental lesson, but one observed family does not authorize revising Discovery Engine rules.

## Scope, negatives, costs and release debt
No changes to production Builder, Reader, codec, native core, on-disk revision, golden vectors, released data, shared discovery state or benchmarks. No change to original nine tests; no safety bypass or lower bound. Static Reader preflight still has TOCTOU race debt. Mac expected-`S_SPARSE` regression remains red and still blocks owner promotion until the suite obtains equivalent meaningful tests or an explicitly justified portable control **without weakening the invariant**. Mac host cannot be forced to expose physical holes by merely seeking/ftruncating. The hand-built vector proves direct S_SPARSE Reader behavior but does not validate Builder's ability to create sparse representation on Mac.

Unmeasured: full product create/extract CPU/wall, peak RSS, temporary materialization, selective reads/amplification, filesystem differences beyond hosted Ubuntu/macOS, Windows NTFS, native ABI integration, full release ABBA parity. No product win, merge or release earned. Stronger design future: separate Reader safety's physical storage-kind coverage (independent fixed-byte vectors) from host-dependent Builder sparse optimization outcomes, while preserve a separate honest exact Build→Extract functional check.

## Durable CI evidence
- [Actions #40248182466](https://github.com/FCMO-AI/.CMPCT/actions/runs/40248182466): scientific job Ubuntu **SUCCESS** and macOS **SUCCESS**; inherited parent Ubuntu **SUCCESS**; inherited parent macOS **FAILURE**, only original sparse precondition.
- Scientific macOS artifact **12619756715** (zip SHA-256 `519363513040f4ff9d9a7c4912ca7afd09c82c58781618fc04a951c44927cf92`); scientific Ubuntu **12619451605** (`5c7979a9b0231e2f26c02f4737e4b1badf54155e36407b5861c69eed3a703c58`).
- Unchanged-parent Mac artifact **12619622013** (`336b4600c71576fa61728ed74f41c835f92ef39dadae531c097133ad257000de`); unchanged-parent Ubuntu **12619217224** (`f780c6d995b10c5f907bb980494d41c54336fa316dcd3282f364a1be27423dd6`).
- CI Engineering Evidence on current source was subsequently **SUCCESS** after exactly required PR headings were supplied without modifying validator. CI topology/version/native/fuzz also green at original code head. Generic tests and official performance parity remain independent; an administratively green skipped performance workflow confers no release credit.

## Highest-value next step
Notify parent safety owner #294 and composition owners #472/#479 of the **scoped physical sparse selection** and **two-host golden S_SPARSE safety PASS**, together with unmodified Mac inherited red. Owner should determine a valid portable safety-branch control while **leaving old negative visible** until an equivalent test or independently documented scope change is approved. Avoid a duplicate O132 implementation or Mac sparse threshold gardening. Return to stronger cross-guard convergence/TOCTOU architectures and complete product economics afterwards.
