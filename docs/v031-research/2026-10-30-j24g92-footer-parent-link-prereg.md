# J24G92 — Prospective installed Reader versus strict preflight on a one-field footer predecessor rewire

**Date:** 2026-10-30 UTC. **Status:** prospective for installed Reader / preflight; **scientific research only**, no product/format/version/release credit.

## Authority / exact origin
- Released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, r24.
- Parent **J24G91 #853** exact `129edec976efe8bb604584517de39553487fec34`; installed Reader `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Parent research implementation is **not** imported as proof of this question.
- `docs/discovery/STATE.json` remains stale and owned by PR #574. No shared state write.
- No known concurrent narrow owner found in open PR search. #649 owns orphan-chain CPU amplification; this experiment is about **one changed parent pointer and logical-state selection**, a different failure class.

## Baseline / existing oracle evidence
The prior J24G91 two-host physical archives (GitHub Actions #41120248525, exact #853) contain authentic 63-DELETE r24 histories. A **new local detached parser preliminary result, observed BEFORE this preregistration**, rewired exactly the latest footer's 8-byte `prev` field to its grandparent on Ubuntu/Windows, 4,096/8,192 member samples. In all four isolated byte-level tests it preserved the latest payload SHA-256 and resurrected exactly one deleted path, while full-file SHA-256 changed. That is an **oracle about the raw format parser**, not proof that installed `CMPCT` or `preflight_archive` accepts such bytes.

## Primary question
Does the **unchanged installed released Reader** select the tampered latest footer as valid and return a logically different set from the original archive, even though no footer payload or stored SHA-256 changed? Does `cmpct.validation.preflight_archive` select the same state or fail closed?

## Mechanism and falsifier
r24 footer uses `<8sBBBBQQQ32s`; `prev` is outside the SHA-256-protected uncompressed payload. Changing only `prev` from the immediate predecessor to the predecessor's predecessor may cause the Reader to skip a legitimate DELETE while accepting the latest payload. Separate control: corrupt one payload byte without changing its digest; correct recovery should fall back to an earlier complete signed generation. Negative out-of-bounds pointer must be treated defensively.

**Prospective H1:** Installed `CMPCT` accepts the rewire, retains the latest footer position, and resurrects exactly one otherwise deleted path; the file's own footer SHA stays identical, but whole-file hash changes. **H1 is falsified** if it rejects the latest footer or still returns the original complete logical index. The experiment is decision-changing regardless of direction.

**Prospective H2:** Strict preflight also accepts or produces a *different* result; separately record whether Reader/preflight parity holds. It is a **correctness split** if they disagree. Do not assume preflight will accept.

## Simpler controls / alternatives
- Normal unchanged archive; one-field rewire; one latest-payload corruption; one out-of-bounds prev; zero-previous parent; valid checkpoint with prev changed (should not change latest snapshot semantics).
- Direct detached interpretation of the exact changed bytes (not just comparing printed Reader lists).
- Stronger alternative to patching current parser would be a future explicit generational commitment/binding; such a wire-format change is **not authorized here**. A caller-anchored whole-file SHA or authenticated external manifest also detects the edit: the experiment must not claim a MAC/signature forgery, bypass of external attestation, remote exploit, or key compromise.

## Scope and experimental rung
Two CI hosts, Ubuntu 24.04 and Windows 2022, generation of fresh Builder archive with 16 and 128 deterministic regular files and three authentic `append_delete` commits. Run actual installed product via `pip install .` and use source blob identity. Use read/verify, index paths, latest footer/depth, strict preflight and physical SHA evidence. No public product source change. Evidence is **hosted source-exact product API behavior on engineered hostile input**, not a benchmark or release gate. Stop this narrow question after the outcome is measured; do not mutate comparator or thresholds.

## Admission / interpretation
If Reader accepts the rewire, record exact semantic divergence and opened state as a **scoped integrity claim limitation** on r24. If preflight disagrees, elevate the correctness split. If Reader rejects, falsify the local-oracle-to-product hypothesis and preserve the negative. An attacker who can rewrite whole archive bytes also can forge unkeyed SHA-256; the specific *new* mechanism is unprotected predecessor topology despite otherwise unchanged hash-protected payloads. Treat v0.30 origin-authentication claims conservatively.

## Costs / limits
No create/extract/RSS performance claim. Only three DELETE generations on two synthetic regular-file families; no native, hardlink, sparse, xattr, multiwriter, macOS or remote consumer coverage. No release, no merge, no version, no benchmark change. Raw CI evidence to be persisted separately with SHA receipts. Record any unexpected exception without turning a failed verification into a green safety claim.

## Expected decision unlocked
Decide whether r24 parent-pointer topology is accepted unbound by both public Reader and strict preflight, and if so identify the smallest backward-compatible safety invariant (where available), or explicitly bound the specification's integrity wording. Coordinate findings to #853 and the existing recovery/integrity owners; do not duplicate their implementations.
