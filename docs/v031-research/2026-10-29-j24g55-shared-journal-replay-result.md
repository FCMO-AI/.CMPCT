# J24G55 — shared bounded journal replay: physical positive result

Date: 2026-10-29 UTC
Status: **EXPERIMENTAL CANDIDATE PASSED ITS SPECIFIC SIGNED-JOURNAL COURTS; NOT MERGED OR RELEASED**
Owner: draft [PR #789](https://github.com/FCMO-AI/.CMPCT/pull/789), stacked on unchanged draft #783 `47ddedbeb844a8d59e9d142910c6705301214ce0`.
Prospective preregistration: `a95f2ee99bd7e15f63be23c88293a685dac7d5a7`, committed **before** code/tests/CI.
Evidence-bearing source head: `d32ea7c62fe72c07c1727d9ec34e4b4848b3199f` ([GitHub Actions #40974277189](https://github.com/FCMO-AI/.CMPCT/actions/runs/40974277189)); previous same-product-head source `af8e4fda3bd88a07899ae7c4ad15b6f774c85e2e` also passed three hosts ([#40973653520](https://github.com/FCMO-AI/.CMPCT/actions/runs/40973653520)) before the additional 64-generation and footer-recovery courts.

## Primary question and falsifier

Two immutable negative physical courts, [#786](https://github.com/FCMO-AI/.CMPCT/pull/786) and [#787](https://github.com/FCMO-AI/.CMPCT/issues/787), showed the validator's previous journal replay retaining signed xattr ordinal 2 after a deletion while Reader correctly remapped the owner to ordinal 1. J24G54a: stale ordinal out-of-range => false rejection of a valid committed archive. J24G54b: stale ordinal still in range => false acceptance of effective index attributing a legitimate xattr to the wrong member. Both were real Builder+native xattr+signed `append_delete` evidence on Linux and macOS. One ordinal-clamping fix could never address the in-range case.

**Prospective J24G55 hypothesis:** Reader, Writer/checkpoint and bounded preflight should share a *single* positional metadata replay function. Move exactly the Reader's existing operation into a cycle-free module, retain its function identity through Reader reexport, optionally bound file insertions when used by preflight, and keep all signed format checks elsewhere.

## Material engineering

- `src/cmpct/journal_replay.py` is the single semantic source for `_apply_journal_ops`, with `max_files` optional and `JournalReplayLimitError` on overbudget insertion.
- `src/cmpct/reader.py` reexports helper under the prior name, preserving transaction/checkpoint consumers. Existing Writer `src/cmpct/transactions.py` is byte-identical to parent.
- `src/cmpct/validation.py` validates signed delta shape/ops/blob budget, delegates to same helper with `ParserLimits.max_files`, and converts hostile budget/schema errors into typed parser errors.
- A separate source-normalized comparison of inherited Reader method from parent blob `c82ab200bf849f844587683992f0c702cc39059a` and new helper blob `ccb3fbeee64a21c1d1fbd37e471008d691ee97b4` returned `sameExceptOptionalBound=true`: all prior replay statements match exactly after reversing only the optional signature and insertion-time cap.
- A separate byte comparison found **unchanged** ParserLimits, footer recovery block, hardlink inode-xattr guard, full index/physical checks, and preflight public API in validator. This reduces the blast radius but does not replace tests.

## Direct source-exact CI evidence

[Three-host signed-journal Actions #40974277189](https://github.com/FCMO-AI/.CMPCT/actions/runs/40974277189) source `d32ea7c62fe72c07c1727d9ec34e4b4848b3199f`:
- **Ubuntu 24.04: 32 PASS, 0 FAIL.**
- **macOS 14: 32 PASS, 0 FAIL.**
- **Windows 2022: 25 PASS, 7 native-POSIX SKIP, 0 FAIL.**

Every host installed the exact CMPCT source into the tested environment and compared hashes of installed Reader, validator, shared replay, transactions and Builder against the checked-out source; both Reader and validator imported the *same function object*. All tests invoke the actual installed package, not an invented alternate implementation.

Linux/macOS physically built the baseline r24 archive with genuine source-native xattrs, appended signed delete, verified content, and extracted strict xattr bytes. The prior out-of-range and in-range cases **now both pass preflight**; independently inspected preflight effective index and Reader both associate the surviving signed attribute with its original path, not a different ordinal. Early-only and no-xattrs controls still pass.

Two independent referees without importing CMPCT verified original Builder bytes, compressed signed primary/checkpoint/delta, footer ancestry and digests, physical blob framing and unchanged payload. Across Linux/macOS, **5/5 + 4/4 tampered cases per host rejected**, total 18/18. Their scripts are adapted prospective *positive* judges; historical negative scripts and logged results in #786 were not rewritten. The outcome strings are `SIGNED_JOURNAL_DELETE_REKEY_PARITY_VERIFIED` and `IN_RANGE_SIGNED_XATTR_REKEYED_TO_OWNER_IN_PREFLIGHT_EFFECTIVE_INDEX`.

New direct controls extend beyond the two original negative cases:
- **Real 64th signed deletion/checkpoint:** create 66 files with xattrs on first/last, commit 63 deletions (depth=63) and the 64th checkpoint (depth=0); preflight/Reader agree before/after and native extracted xattrs remain attached to the two survivors.
- **Committed-footer recovery:** authentic valid archive with delete, corrupt newest footer SHA, truncate newest footer or append uncommitted garbage; preflight and Reader agree on the last valid committed generation and verify its content.
- **State/oracle control:** delta families insert, delete, rename, replace, multioperation, delete+fresh same-name put, owner overrides, 64 sequential operations, invalid fsmeta ordinal and malformed operation rejection; preflight and Reader effective indexes agree.

Original provider artefacts, not independently downloaded by this activation:
- [Ubuntu #12942310732](https://github.com/FCMO-AI/.CMPCT/actions/runs/40974277189/artifacts/12942310732), ZIP SHA-256 `a3d82faf1608ae323d97e88442d687d99c70a3bf69b7cdf233a841e15d0d93cd`.
- [macOS #12941457320](https://github.com/FCMO-AI/.CMPCT/actions/runs/40974277189/artifacts/12941457320), ZIP SHA-256 `c7a8ac81e44e839cf72751906cdf532f3c9c92da4ea86faf5f3ef113abf15557`.
- [Windows #12940664750](https://github.com/FCMO-AI/.CMPCT/actions/runs/40974277189/artifacts/12940664750), ZIP SHA-256 `1f31c5581dd966d68dcad36d9b31b04fb695a417ae56846130597a7e0bafa391`.
GitHub returned artifact SHA-256 metadata; this activation did **not** redownload independent ZIPs.

## Strongest negative, conflicts and limitations

The positive result is constrained to the signed-journal cases listed above and available host providers, **not** full general-purpose archive correctness, published wheel behavior, native Rust journal parity, host-level race safety or release acceptance.

A previous exact-head Engineering Evidence check failed first because mandatory PR sections had noncanonical headings, then because the literal quality-ratchet marker was missing. The PR description was corrected without touching the evaluator, and [Engineering Evidence #40974305922](https://github.com/FCMO-AI/.CMPCT/actions/runs/40974305922) succeeded at the measured source head after PR metadata correction. These were documentation/evidence-gate issues, not product semantic failures.

O69 strict-xattr on macOS remains red on a **historical evaluator assumption** that removing Python `os.setxattr` means no host xattr provider exists; the independent native Darwin provider makes that assumption false. O72 remains red because its frozen source-blob identity court expects an older Reader hash; it fails *before running behavior* on this changed source. Neither validator, source identity, thresholds, or frozen negative changed. These are unresolved owner-level promotion/integration blockers, not silently erased failures.

No measured complete archive sizes, create/extract/selective throughput, cold open, full CPU/RSS, temporary I/O, large-index latency, privileged UID/GID restoration, ZIP/Zstd same-semantics comparator, or official released v0.30 wheel proof. The optional file-count cap avoids unbounded append **count**, but the mechanism can incur O(n) per update and must be profiled at realistic scale before a performance release. A signed archive with inconsistent historical metadata may remain unrecoverable without an external oracle.

Other workflows on the same candidate must be cited by their terminal exact-head results rather than assumed from this focused court. A green administrative ZIP workflow is not a newly earned speed/size victory.

## Decision, counterfactual and handoff

**Primary scientific decision changed:** the paired defects from #786 are repaired on the J24G55 experimental candidate under the scoped installed three-host evidence. Shared semantic replay is materially stronger than validator-only range clamps, independent duplicated rekey logic, or a dynamic import cycle.

The prospectively recognizable discriminator was J24G54b's *in-range* wrong-owner case: it ruled out cheap superficial bounds repair and selected a shared path-identity owner before implementation. This is a local reusable lesson, **not** repeated durable evidence justifying self-modification of Discovery Engine policy. No concurrency collision was observed on this narrow mutation surface; existing #783/#786/#778 branches and `docs/discovery/STATE.json` remain untouched. The latter is staleable and has a separate reconciliation owner (#574).

**Next cheapest owner decision:** confirm exact-head general tests/native/fuzz/Engineering Evidence, reconcile O69/O72 through legitimate fingerprint/test authority without weakening their intended controls, measure realistic large-index whole-product cost, then have the #783/#778 integration owners decide safe merge sequencing. No version bump, format change or release credit before all applicable gates pass.
