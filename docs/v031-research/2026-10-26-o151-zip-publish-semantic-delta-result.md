# O151 — source-exact POSIX ZIP staging compatibility court (result)

**Date:** 2026-10-26 UTC. **Status:** decision-changing cross-candidate product-compatibility research; no new ZIP exporter, no merge, no release.  
**Hypothesis frozen before evidence:** `docs/v031-research/2026-10-26-o151-zip-publish-semantic-delta-prereg.md` at `a4a6ae0f6c8c2b1801dbc708a07b7458d5736d16`.  
**Result-bearing HEAD:** `1318eeef89bea0d40b694d7d16f8fe41819decbe`.  
**Hosted Actions:** https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947 — **6/6 jobs SUCCESS**, Ubuntu 24.04 and macOS 14; no skips/fails in O151.  
**Test Git blob:** `01f14a1fbbc24b7cbbf85f7230b5bdbc9e0df393`.

## Primary answer

**Yes: the two competing stage-and-replace implementations preserve exact logical ZIP bytes but change successful-output filesystem semantics in distinct ways.**

The same frozen valid revision-24 `raw.bin` archive (input SHA-256 `5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d`) was exported by three genuinely installed, source-bound engines under process umask `022`:

| Engine | Exact source HEAD | New `new.zip` mode, both OS | Stage mode before publication | Existing symlink output | Previous symlink referent |
|---|---|---|---|---|---|
| O140 prior writer | `d8b69758dbcbb66fe28fa7cf59598916df160d2d` | **0644** | No stage/rename | **Preserved** | **Changed** to new ZIP |
| O149 #492 | `ca01d885fedc8ffc343b9c3c624eddd134158452` | **0644** | **0644** for absent target | **Replaced by regular file** | **Preserved unchanged** |
| O150 #491 | `48bbb41661f8b19d369c50b06bec1018cd4400e9` | **0600** | **0600** for absent target | **Replaced by regular file** | **Preserved unchanged** |

O149 and O150 each issued two witnessed atomic renames per run; O140 issued zero. For the existing symlink case, *both* candidate staging files were 0644 immediately before publication because the implementations copied the original target's mode. That matters for any future claim that staging is always private.

**Logical output was equal in every cell:** ZIP SHA-256 `910e3be250460beac06083166a0641ed1398506ae40949e56efd3c3c73a564db`, length **176 bytes**, member `raw.bin` contained exactly bytes 0..63, `ZipFile.testzip() is None`. CMPCT source bytes were unmodified in all six cells.

This is a measured compatibility fork, not proof that either publication contract is intrinsically unsafe. O150's new-file 0600 may be a deliberate confidentiality choice, but should not be described as preserving old ordinary umask behavior. Both candidate symlink changes may be deliberate atomic-pathname semantics, but must not be described as unchanged symlink-following behavior.

## Evidence and audit

Original source HEAD, Git Reader blob, frozen vector blob, exact test blob, installed module path outside checkout, source fixture SHA and per-cell JSON/logs were recorded for each job. CI source bind uses Git's blob identities:

- O140 Reader `e46e6121842d485cb209118576ebf3ba3719080d`;
- O149 Reader `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`;
- O150 Reader `f38662c8db4132895778951263d83d24022f9296`;
- independent vector `d10b7dab9126d39e819a74279c186363a163f2ef`.

The six raw artifacts, in the same three-engine × two-platform order, are:

| OS | Engine | GitHub Actions artifact |
|---|---|---|
| Ubuntu | O140 | [12628622286](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947/artifacts/12628622286) |
| Ubuntu | O149 | [12628352727](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947/artifacts/12628352727) |
| Ubuntu | O150 | [12627937213](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947/artifacts/12627937213) |
| macOS | O140 | [12629030937](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947/artifacts/12629030937) |
| macOS | O149 | [12628686293](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947/artifacts/12628686293) |
| macOS | O150 | [12628966519](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947/artifacts/12628966519) |

Direct inspection of the six job logs recovered six `O151_RESULT` JSON witnesses and six `O151_AUDIT_PASS` records. Their `actual` dictionaries matched the **preregistered** `predicted` dictionaries independently on Ubuntu and macOS. Each job produced an authentic ZIP rather than merely passing a test harness; output SHA was identical across hosts and engines.

## Why current CI status matters

Both donor PRs have **positive dedicated ZIP failure-atomicity courts**, but their generic tests are still red: original O150 #491 `40268808543` ended **797 pass / 39 fail**; O149 #492 `40269565312` ended **797 pass / 40 fail**. Reported failures primarily arise from inherited test modules expecting explicit experimental engine/environment variables (`engine attribution required` and `CMPCT_FIXTURE_JSON`), rather than directly falsifying the new ZIP output semantics. O140's immutable source-bound court also necessarily fails the Git Reader blob identity check on both descendants: its original frozen source is `e46e612...` and must not be rebased/rewritten to bless new source. **Neither candidate has generic or frozen-authority approval.**

The O151 test-only HEAD initially had **Engineering Evidence FAIL** from missing exact heading names in PR description, not product/test failure. The dossier is being reconciled without changing the validator. O151's official r24/ZIP workflow reported administrative SUCCESS with performance job **SKIPPED**, so it is **not** a measured performance approval.

## Best-scoped decision

1. **Deduplicate ownership**: #491 and #492 implement the same repair class with different mode behavior. Choose a single authoritative stage-and-replace owner; retain one as independent replication/differential reference rather than launching a third product implementation.
2. **Explicitly decide the successful-path contract**: absent target POSIX mode (0600 privacy default versus historical 0666&~umask), existing symlink leaf meaning (follow referent versus replace link), existing inode/hardlink identity, basic mode, ownership/xattrs, and temp-file visibility. If contract changes, document it and demonstrate why it improves the product rather than silently claiming parity.
3. Preserve O143 negative proof and O149/O150 positive exception-atomicity observations. Add a conservative source-exact integration court for O135/O140/Deflate/ZIP64 plus metadata/namespace policy. Evaluate temporary full-ZIP disk, create/extract overhead, Windows replacement behavior and full official same-runner economics before promoting.

## Adversarial self-review and limits

The test uses a monkeypatch forwarding to the actual `os.replace` only to snapshot stage file mode/size/ZIP validity immediately before rename. It does not alter ZIP serialization or the replacement outcome. Temp directory is private; this is **not proof of cross-user disclosure** even when stage mode is 0644. The symlink referent is a normal regular ZIP in a private temporary directory; no concurrent attacker, mount propagation, unusual ACLs, xattrs, alternative umasks, crash, ENOSPC, Windows, or sustained performance workload was tested. ZIP SHA equality on this 176-byte fixture does not prove equality for all compression routes or huge ZIP64 files.

## Counterfactual / Discovery lesson

A static inspection of `mkstemp(0600)` versus `os.open(...,0666)` under umask 022 and `os.replace` versus `open('wb')` would have predicted both forks cheaply. The installed same-input court was warranted to verify the actual product executed those paths and retained an identical ZIP; this inexpensive discriminator is reusable in future atomic-publication reviews. No evidence supports changing Discovery Engine policy or weakening release gates; shared `STATE.json` remains untouched.

**Classification:** product-compatibility evidence and orchestration/convergence decision; not a shipped fix, benchmark win, security exploit, or license to merge/release.
