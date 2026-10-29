# J24G52 — explicit inode xattr conflict guard: exact-hosted result

**Observation cutoff:** 2026-10-29 21:38 UTC. **Result class:** experimental product correctness candidate, no merge/release. This note never replaces the source/CI/artifact authority. The prospective hypothesis was committed at `318ad1a608222a7de9c765eb556b5c64ae8a407b` **before** `validation.py` / `reader.py` changes. Parent #778 `47c9a4d61cd764aa4252cad741f4b22537106c60`. Independently confirmed negative #780, issue #781, run [40950852839](https://github.com/FCMO-AI/.CMPCT/actions/runs/40950852839).

## Principal question and answer

Can a shared, finite, canonical path-to-terminal-regular-inode proof refuse two **explicit** different xattr values for the same inode/key before output creation while accepting compatible hardlinks and independent equal-content files? **Yes within the physically and synthetically evaluated cases.** The new guard is called from `validation._validate_index` / `preflight_archive`, `CMPCT.verify()` and at the beginning of `CMPCT.extractall(metadata=True)`, before `dest.mkdir()`. For `metadata=False`, xattr restoration is intentionally not guaranteed and content-only extraction remains possible.

No claims are made that the fixed branch is released, nor that physical ownership/mtime/sparse-absence problems are solved. The historical negative evidence is not modified.

## Direct measurements: source-exact installed GitHub Actions

[Source-bound workflow run #40958969068](https://github.com/FCMO-AI/.CMPCT/actions/runs/40958969068) evaluated HEAD `7e28f864997a7b6357878dc9a2a0c0ab82b77c74`, with Python installed from the exact checkout and `reader.py`, `validation.py`, `builder.py` byte-for-byte compared with installed modules. Source SHA-256: Reader `79655a9e9d274cae7127e38a730f7e386fb273b453008460aa986db95371d974`, Validation `4dff8e4068479e1b7c3c8709c4f82ea1c4bffe3d246657aaddb02a176962cf59`, Builder `59e6787feb6ec9005b9ecea298bf39ff2434df81271b020f79f22e7314f18c9b`.

| Host | Specialized tests | Measured 8192-link chain guard | Independent physical wire audit |
| --- | --- | --- | --- |
| Ubuntu 24.04 | **6 PASS** | **0.022277 s** | PASS |
| macOS 14 | **6 PASS** | **0.034759 s** | PASS |
| Windows 2022 | **5 PASS, 1 SKIP** (native inode-xattr readback not available) | **0.037704 s** | PASS |

These chain times are **single-run isolated synthetic in-process guard durations**, not Reader cold-open/create/extract/RSS or whole-system performance. Do not infer a percentage improvement from them. A local prototype (not CMPCT installed) also completed a 12k-deep chain in ~0.022 s; it receives no product credit.

The separate referee imports `msgpack` and `zstandard` but **does not import CMPCT**. For each actual Builder-derived r24 physical specimen it verified header/tail/footer SHA-256 commitments, exact body placement, per-blob physical header alignment, the distinct owner/alias xattr values and different same-content regular-file identities. On all hosts, physical body SHA-256 was unchanged across compatible/incompatible candidates: `ad522aaaaf4b34d2bc096408a70d89236bbb08a19476d7412b433527ece49a6f` (108 physical payload bytes). Four independent referee perturbations (**primary index / tail / footer / blob header**) were rejected on every host.

Artifacts retained by provider:
- [Ubuntu #12934842554](https://github.com/FCMO-AI/.CMPCT/actions/runs/40958969068/artifacts/12934842554) — artifact ZIP SHA256 `1ed7f9a021d9cd83a4d6784730189b8837a86bf617157b8139150e949b8f0613`.
- [macOS #12934463150](https://github.com/FCMO-AI/.CMPCT/actions/runs/40958969068/artifacts/12934463150) — artifact ZIP SHA256 `7ebb0c5a1279310c747bce164f9fb326de71a3e1df817a5a572950b77fefbb73`.
- [Windows #12934164082](https://github.com/FCMO-AI/.CMPCT/actions/runs/40958969068/artifacts/12934164082) — artifact ZIP SHA256 `618e59a863ba8399c32773d7c0f4a1736914f6fbd1aec9340e6542e457b7bce5`.

Provider-reported artifact digests above were **not independently re-downloaded and audited** in this activation. The independent referee ran *inside* each source-exact hosted job and its JSON/log is in the hosted artifact.

## Controls, counterfactual and falsification

- The #780 inherited branch accepted a checksum-consistent conflicting physical xattr archive and overwrote owner metadata on Ubuntu/macOS. That negative remains authoritative at its own source SHA; it is **expected to change** under this candidate, not to be erased or relabeled.
- Compatible owner + alias with equal explicitly declared values passed native POSIX restoration.
- Two physically separate files with identical content retained distinct xattrs, proving no false equivalence based on SHA/blob.
- Sparse omitted xattr rows were admitted instead of inventing an absence semantics; an independent directory carrying xattrs was admitted despite an unrelated hardlink group.
- Byte and text xattr name encodings denoting one native key were compared consistently.
- Multi-hop alias chains and 8,192 aliases used iterative cached resolution; an explicit conflict at tail was rejected.
- Before any destination creation, both strict and portable metadata-enabled extraction rejected the conflicting archive. Content-only extraction with `metadata=False` stayed available.

**Disproof:** a future archive with equal explicit hardlink xattrs that is rejected, a contradictory explicit pair that is accepted, or a path whose content is equal but inode is independent that is conflated invalidates this narrow solution. A single green test or hash check is not full fidelity evidence. There is no claim of source authenticity by a digital signature: SHA-256 here commits to bytes within a physical archive, not the identity of its creator.

## Negative evidence, unanswered semantics, debt

1. Sparse *absence-versus-present* xattrs cannot yet be declared contradictory without revisiting historical r24 semantics and Builder records. The candidate intentionally compares explicit key/value pairs only.
2. UID/GID owner overrides, modes, timestamps, symlink xattrs, directory hardlink impossibility, physical APFS compression attributes and multi-generation journal/canonical preflight alignment are **not solved**.
3. `validation._apply_delta` and Reader `_apply_journal_ops` are separate generation replay paths. Source inspection suggests potential differing ordinal treatment for updates/deletes; this is an **unmeasured compatibility/fidelity risk** requiring a separate physical differential before promotion, not a verified new defect in this activation.
4. End-to-end CPU, RSS, cold-open, selective read, creation/extraction and release performance matrix were **not measured**; 8,192-alias microcost does not cover worst-case memory. Extra dictionaries and canonical path traversal cost resources where applicable.
5. Historical O69/O72 exact-source/fingerprint checks still fail on the stacked branch for previously documented divergent source assumptions; they were not weakened. Full General Tests remain a separate inherited gate, not evidence of this narrow xattr fix.
6. This branch composes onto an unmerged #778 candidate. It is not an independent run of published wheel v0.30.0. No merge or release is authorized.

## Decision and handoff

**Decision changed:** issue #781 advanced from physical reproduction to an additive source-level guard with source-exact three-host positive tests. This earns **experimental correctness progress only**, not release credit or a claim of universal filesystem fidelity.

**Coordination:** leave #778/#773 owners intact; invite them to review this stacked branch and decide integration. The cheapest next unclaimed decisive action is a journal-generation parity differential on an authentic, xattr-bearing hardlink archive (preflight versus direct Reader) with one delete/reorder and a full baseline-only control. After that, measure added CPU/RSS on a large xattr-dense archive, reconcile historical frozen tests without relaxing thresholds, and run actual release/portability gates.

**Discovery Engine:** used to choose smallest bounded proof rather than content-hash heuristic or new physical format. A single new physical result does not justify rewriting its research policy or the staleable `STATE.json`; its separate owner #574 continues reconciliation.
