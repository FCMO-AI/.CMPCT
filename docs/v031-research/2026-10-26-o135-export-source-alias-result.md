# O135 — ZIP export source-inode alias: source-exact product result

Date: 2026-10-26 UTC  
Status: **SCIENTIFIC CONFIRMED / STATIC PRODUCT FIX CANDIDATE VALIDATED ON TWO POSIX HOSTS / NOT MERGED OR RELEASED**  
Primary preregistered prediction: [O135 prereg](2026-10-26-o135-export-source-alias-prereg.md) at commit `341c0776fdc6ec6e00240d5b47e28394a28392d1`, **before** product commit `d1bb0f960cda85a983b78f9cb329366cbaee3a58`.

## Problem and baseline

The exact owner export Reader in PR #284 (`2e493d2d941f9c144c0c5050b41c88dc7c6e57dd`, `src/cmpct/reader.py` Git blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`) reads a valid CMPCT archive from an open file/mmap and truncates its legacy ZIP output on `export_zip(out)`. It does not test whether the output is a different **physical** inode. The source can thus be the object about to be truncated. This is the ZIP export endpoint, not the independently owned extraction defect O118/#468, and not the post-verification mmap mutation problem O2–O5/#286.

## Insight and hypothesis

Before either native or fallback legacy ZIP output is opened, compare the source's open FD's `(st_dev,st_ino)` from `os.fstat` with any existing destination's `os.stat`. Refuse equality before modifying filesystem objects. Prediction: original loses source integrity on same-path/hardlink/symlink static aliases; candidate rejects all aliases safely; disjoint conversion remains exactly readable. The change adds no archive-header or ZIP semantics.

## Alternatives considered

Lexical path equality misses hardlink and symlink aliases. Trusting callers is not a safe library contract. A private committed output snapshot protects more races but adds disk/CPU/I/O and overlaps the independent staged-output work in #286. Globally refusing preexisting outputs would regress accepted legitimate overwrites. Selected O(1) static inode guard is intentionally narrower than a race-free publication architecture.

## Evidence

### Source binding and workflow

- **Product test HEAD:** `4470f4a9641ca3f4b5635bda416df2d5f123c4bc`, draft [PR #483](https://github.com/FCMO-AI/.CMPCT/pull/483), stacked exclusively on PR #284.
- Original Reader blob: `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`.
- Candidate Reader blob: `f1c945ac3bd93d73226c81099e95ff1a2d0a0f9d`.
- Immutable independently authored `tests/conformance/v24-direct-codecs.json` blob: `d10b7dab9126d39e819a74279c186363a163f2ef`. Inputs: RAW archive SHA `5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d`; Deflate archive SHA `91cd520c62f2d0ffce9e3c95dd46f76138d840bacd5ce9282b3c9efbc737e870`.
- **[Hosted exact-code-head scientific court #40253147083](https://github.com/FCMO-AI/.CMPCT/actions/runs/40253147083): four jobs SUCCESS**, authentic independently installed original/candidate code, Ubuntu 24.04 and macOS 14. Eight tests per job; **32 scientific cells passed**, no skip/fail in this focused court. Both disjoint output modes independently decode and match the golden logical SHA; each static alias is compared against full source SHA after child exit.
- Raw original/candidate custody artifacts:
  - [Ubuntu original #12621063130](https://github.com/FCMO-AI/.CMPCT/actions/runs/40253147083/artifacts/12621063130), ZIP SHA-256 `a7c3ac0e2830064cbc86c27a49cfad1c1442bb4063d707b5ce6ad0ce2b83b08d`;
  - [Ubuntu candidate #12621052943](https://github.com/FCMO-AI/.CMPCT/actions/runs/40253147083/artifacts/12621052943), `c50d95f8669c6c45849d4dd1c2e74555b5cdcb2e2fbe35df99052f44c74620d8`;
  - [macOS original #12620344188](https://github.com/FCMO-AI/.CMPCT/actions/runs/40253147083/artifacts/12620344188), `023a72817fac229c3eea22d50f1624323035f21f5f7b9de51a3eb3d011d03693`;
  - [macOS candidate #12620608382](https://github.com/FCMO-AI/.CMPCT/actions/runs/40253147083/artifacts/12620608382), `b6d14b1e7e645f4002ea7b77b531abeada730ea85346daa919b92cfa8fc67348`.

### Direct measured result — four independent host/engine jobs

| Genuine source | ZIP destination | Ubuntu original | macOS original | Ubuntu candidate | macOS candidate |
|---|---|---|---|---|---|
| RAW + Deflate | Independent | 2 exact ZIPs | 2 exact ZIPs | 2 exact ZIPs | 2 exact ZIPs |
| RAW + Deflate | Same pathname | 2 original archives truncated to zero, child SIGBUS -7 | 2 truncated, child SIGBUS -10 | 2 managed refusals, original SHA retained | 2 managed refusals, original SHA retained |
| RAW + Deflate | Hardlink alias | 2 truncated, SIGBUS -7 | 2 truncated, SIGBUS -10 | 2 managed refusals, SHA retained | 2 managed refusals, SHA retained |
| RAW + Deflate | Symlink alias | 2 truncated, SIGBUS -7 | 2 truncated, SIGBUS -10 | 2 managed refusals, SHA retained | 2 managed refusals, SHA retained |

The truncated original source has SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty byte string). The candidate's managed refusal exits with the court's explicit code 31 and reports `ZIP export destination aliases its own CMPCT source archive`; the original source SHA remains unchanged. The data show actual destructive mutation independent of whether the child returned success or crashed.

### Preserved initial infrastructure failure

The original court [run #40252762885](https://github.com/FCMO-AI/.CMPCT/actions/runs/40252762885) was **FAILURE**: importing the uninstalled original raw Git worktree failed because its package-owned native codec was absent, and unrelated root `conftest.py` imported a Linux-specific `libzstd.so` from experimental files on macOS. Neither failure was scored as a product negative. The source-bound workflow was repaired, **without editing the test assertions**, to independently install the exact historical source into a standalone target (including native codec) and run focused pytest with `--noconftest -c /dev/null` to avoid importing unrelated experiments. The later successful run above is the decision-making evidence; both initial and subsequent logs remain preserved.

## Losses, ambiguity and negative evidence

This is a **static alias check**. Concurrent attacker-controlled path changes between `stat` and output-open remain a TOCTOU window; in-place source writes after verification can cause mmap faults independently (O103/#459; O2–O5/#286). Exactly two small builder-independent rev24 variants were tested; the >4GiB fallback was **not physically exercised**. Network filesystems and Windows/NTFS not measured. A successful focused court is not a release gate. An O(1) syscall bound is a static model, not an observed performance benchmark.

## Safety, integrity and resource accounting

Every baseline destructive case is independently demonstrated through SHA-256 change and physical empty-source size, not fatal signal alone. Candidate refuses before any output publication; disjoint controls retain original logical SHA and ZIP decoding. Reader source, test-vector blob, package install origin and Git HEAD are recorded in source-custody artifacts. No user filesystem or private data involved. One `fstat` and up to one `stat` per export; no extra archive-sized buffer; no codec/snapshot change.

## Compatibility and portability

No CMPCT on-disk format change (r24), no new ABI, no reencoded Deflate output and no ZIP64 footer change. Hosted product evidence Linux/macOS. Windows, active namespace races, >4GiB and producer/consumer lifetime beyond static aliases unmeasured.

## Performance accounting

Product comparative create/extract/read, full ZIP-export wall/CPU/RSS, temporary I/O, large archive transfer, selective bytes, and official ABBA gate are **unmeasured**, not extrapolated. The parent PR #284's preexisting bounded physical Deflate verification adds independent runtime debt. This O135 patch adds a bounded pair of metadata syscalls and must be assessed in the composed ZIP owner before promotion.

## Public-surface check

Only open source and anonymous frozen vectors, GitHub action receipts, test identities and generic filesystem paths. No credentials, private corpora or internal company data.

## Completion gates

- [x] Frozen preregistration predates implementation.
- [x] Original and changed authenticated Reader execute on identical goldens through independent installed packages.
- [x] Two operating systems × two reader engines × eight controls: **32/32 PASS**.
- [x] Source SHA and unrelated original failures preserved honestly.
- [ ] Exact documentation HEAD CI and complete general/Native/Fuzz/performance/public disclosure gates must be separately reconciled.
- [ ] Owner integration, Windows and race-free output publication not established.
- [ ] No merge, numeric release or final product-credit authorization.

## Future leverage

Hand this minimal static guard to ZIP-export owner #284/#260, reconcile with O2–O5's independent staged-output architecture. The cheapest remaining discriminator for promotion is not additional same-alias variants; it is full ownership design under concurrent path/source mutation plus real performance evidence. A false generalization from this static success would be a release error.

**Decision:** `STATIC_SOURCE_ALIAS_DESTRUCTION_CONFIRMED`; `STATIC_PREOPEN_INODE_GUARD_SUPPORTED_ON_POSIX`; `FULL_PUBLICATION_AND_RELEASE_UNEARNED`. No discovery-policy or shared state update earned from a single mechanism-family result.
