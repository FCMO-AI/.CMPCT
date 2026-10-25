# O65 — POSIX extended-attribute read integrity, preregistration (2026-10-25 UTC)

## Exact authority and claim boundary
Release v0.30.0 / on-disk revision 24; canonical development parent `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. This is a separate experimental source-admission lane, independent of O47/O48/O50, O56/O57/O64 and O63. No edits to those owners' branches. Exact origin source and current claims must be reconciled before later promotion.

## Baseline defect
In non-reproducible mode, `Builder._capture_fs_meta` catches *every* `OSError` from `os.listxattr` and `os.getxattr` and continues with absent xattrs; when the filesystem enumerated a key but its value could not be read, a successful, verifiable archive can silently omit that attribute. The source classification is independent of compression/format; the reader cannot reconstruct information never recorded.

## Primary falsifiable question
Can source admission distinguish a truly unsupported xattr API/filesystem (safe existing empty-metadata compatibility path) from an observed-but-unreadable xattr or enumeration error (must refuse to claim exact source capture), without changing normal archive bytes?

## Competing controls and decision law
* Unchanged parent baseline: on deliberate `getxattr(EACCES)` after `listxattr` enumerated `user.o65`, original scan returns normally and omits metadata; on `listxattr(EIO)`, original scan likewise succeeds. This is a simulated failure-injection witness against the real Builder, not frequency evidence.
* Candidate: `getxattr` errors after successful enumeration MUST fail closed (including `ENODATA`, `ENOTSUP`, permission or I/O errors); `listxattr` EACCES/EIO MUST fail closed. `listxattr` EOPNOTSUPP / ENOTSUP / ENOSYS may preserve historical empty-xattr behavior when platform genuinely reports unsupported attribute enumeration.
* Strong simpler control: keep supported normal positive xattrs and genuine unsupported-filesystem fallback byte-identical with parent; do not add a separate xattr shadow or optional best-effort setting.
* Negative: reproducible mode explicitly drops xattrs by contract; its behavior must remain unchanged even if enumerator is denied.
* Verify intended existing output is not replaced when metadata cannot be fully captured.
* Account for CPU/I/O and portability: only exception paths change; no extra syscall in successful path, but failure semantics are stricter on filesystems that previously silently hid attributes.

## Cheapest truthful evidence
First run an original-source fault-injection falsifier on a clean installed package (exact parent blob asserted). Then apply minimal Builder change and run a separate source-locked hosted three-platform court: enumeration success with values, missing value, access denied/list failure, unsupported enumeration fallback, ordinary byte equality and reproducible-mode explicit-zero. No fixture identity used for heuristics. An instrument/Python monkeypatch proves deterministic error-branch behavior, **not** prevalence or full source lifetime/snapshot safety. Any negative control failing or originally supported byte mismatch kills this candidate.

## Alternatives and reasons
* Keep silent omission: incorrect for exact preservation with observable unreadable metadata.
* Reject all xattr enumeration failures: breaks unsupported filesystems and no-xattr environments without benefit.
* Always enumerate through a new fd-walk: different unresolved source-ownership architecture (O52), likely higher cost; cannot substitute for explicit error policy.
* Chosen: narrow fail-closed classification at the existing metadata capture boundary.

## Promotion debt
Independent positive real xattr roundtrip on Linux/macOS, native installed Windows unsupported fallback, general CI and 0-byte size/timing floor, resource accounting and O50/O63 composition remain mandatory. No format change, release, merge or Discovery Engine policy change authorized by this experiment.
