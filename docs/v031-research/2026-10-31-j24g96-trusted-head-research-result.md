# J24G96/J24G96b — True ancestry scope, zero-extra-byte alternative, and stronger whole-file control

**Status:** research-only, O0. Observed local detached results on 2026-10-31 UTC; latest exact-head hosted verdict recorded separately below after it actually finishes. No product change, release/version/format/ABI modification, merge, benchmark comparator/threshold change, or Discovery policy/state edit.

**Repository base:** `main@80c358f8824ec1b20d349c92ed94c898090969b0`, published v0.30.0, on-disk r24. Source authority: current `AGENTS.md`, `docs/discovery/DISCOVERY_ENGINE.md`, original provider artifacts #856 and #853, issue #857. The first prospective preregistration was committed at `79dff022` before code. The second new, narrower *zero-extra-byte alternative* preregistration was committed at `8402d99` before its code. The stream-SHA control is **POSTHOC**; never mislabel it as blinded or prospective.

## Question answered and strongest original control

A footer hash that commits to `prev` and past hashes, externally pinned to an independently trusted current head, can reject selected predecessor rewires for an append history. A self-contained unkeyed hash is not enough: an attacker can recompute the local hash. A whole-file SHA with independently trusted anchor detects **more** alterations and is therefore a stronger safety control; this experiment must not claim same-semantics security or a product win from reduced metadata work.

Eight unchanged, original r24 physical archives were read from the **actual** GitHub-hosted CI ZIPs (both Ubuntu and Windows file sets):
- #856 GitHub Actions 41128984486: `small-ubuntu` provider SHA `d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d`; `small-windows` `f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e` (original source HEAD `f29561c5`).
- #853 GitHub Actions 41120248525: `deep-ubuntu` `19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b`; `deep-windows` `c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab` (original source HEAD `129edec9`).

These **are** real physical CMPCT source files, not new product archives. Each test independently authenticated the original revision-24 footer payloads before the hypothetical digest model; it did not verify the physical CMA4 payload under the new metadata-only head. The next test explicitly attacks that gap.

## Primary preregistered additive model — 8/8 local O0

For each footer, append a hypothetical 32-byte hash of domain, prior hash, physical footer position, full 36-byte header including `prev`, and SHA-256 of decoded payload. Independently trust the latest 32-byte head. With a pinned original head, all one- and two-link ancestor bypasses tested on the eight authentic histories are refused. Recomputing a modified **untrusted** local root succeeds if the attacker can also replace the external pin: **mandatory negative**, not a guarantee.

| Actual physical r24 archive | Footer count | Original archive B | Added archive bytes | Archive overhead |
|---|---:|---:|---:|---:|
| Ubuntu / 16 | 4 | 3,027 | 128 | +4.229% |
| Windows / 16 | 4 | 2,893 | 128 | +4.424% |
| Ubuntu / 128 | 4 | 15,625 | 128 | +0.819% |
| Windows / 128 | 4 | 14,643 | 128 | +0.874% |
| Ubuntu / 4,096 | 64 | 472,905 | 2,048 | +0.433% |
| Windows / 4,096 | 64 | 441,263 | 2,048 | +0.464% |
| Ubuntu / 8,192 | 64 | 938,521 | 2,048 | +0.218% |
| Windows / 8,192 | 64 | 873,437 | 2,048 | +0.235% |

All eight pass their preregistered 5% small / 1% other *archive* overhead ceiling, **excluding** the additionally charged 32-byte independently trusted latest head and optional historical heads. On the exact eight inputs, a one-byte mutation in an authentic CMA4 physical blob **leaves the footer ancestry root identical**, while independently calculated complete-file SHA changes. The metadata-only head therefore fails as a substitute for authenticated full-file contents. The independent referee reproduces the original root, byte costs, and eight forged receipt refusals. No installed Reader performance measured.

## Posthoc PARETOBONK — stronger whole-file retained SHA is simpler and cheaper

After the primary additive test, a simpler alternative was recognized: retain a streaming whole-file SHA-256 state between appends and issue independently trusted whole-file heads as needed. On **frozen historical prefixes** from these same physical archives, `hashlib.sha256.update(new_suffix)` matches full `SHA256(raw[:end])` for every actual footer. Total input bytes processed by the continuous state are one full final archive; independently stateless full SHA for every successive generation reads 3.80–3.96× that amount on four-footer histories and 63.56–63.79× on 64-footer histories.

This evidence is a deterministic **work-count proxy**, not an implementation of persistent Writer hashing, an immutable source, an atomic trusted anchor or a product CPU/IO gain. Python's in-memory SHA object is not crash-serializable here; a restarted Writer must either recover the state through a trusted mechanism or rescan. Concurrent mutation/split-head issuance remains unsolved. Nonetheless the control is a decisive warning against claiming the new per-footer digest is necessary for *incremental complete-file verification*.

## Prospectively distinct J24G96b: digest-slot substitution — 8/8 local O0

A future **new format revision** could repurpose the existing r24 footer's 32-byte SHA slot to carry `SHA256(domain-v2 || prior-digest || footer-position || footer-header || decoded-footer-payload)`. Its Reader must validate this different grammar and independently anchor the latest head; the **existing r24 Reader must reject it**. On all eight original physical inputs, a private hypothetical recoding changed only the existing SHA slot bytes and maintained **exactly the same complete archive length**; it passed its own full new-chain validation. A predecessor rewrite failed validation unless the adversary recomputed its local digest, which then differed from the independently trusted original pin. Altering original decoded footer payload failed; changing a separate CMA4 blob still evaded the ancestry-only root. The independent second referee recomputed all roots from original compressed footer payloads and rejected four forged report fields.

This is an O0 information-model ceiling, not a valid r24 file or a newly implemented r25+ Reader. The 0 **additional archive-byte** projection does not include the additional 32-byte trusted external head, durability, provenance, version-transition semantics, recovery, native interoperability, CPU/RSS/I/O or maintained security contracts. It falsifies the claim that a **second 32-byte footer field** is information-theoretically necessary for a versioned ancestry digest.

## Decision and counterfactual

**Result: `EXTERNALLY_PINNED_ANCESTRY_O0_PASS / FULL_BLOB_COVERAGE_FAIL / EXTRA_FOOTER_BYTES_SUBSUMED_AT_O0 / PRODUCT_NOT_PROMOTABLE`.** This is a narrow result, not a universal authenticated append-log design or a release.

The cheaply recognizable earlier discriminator would have been testing the existing digest-slot substitution **and** retained whole-file SHA before introducing a second 32-byte footer field. The alternative was prospectively frozen only after the first additive result. This yields a local prioritization lesson, but the existing BONK simplicity/control/exported-cost rules already require it; no evidence-backed *new policy* is earned.

No more additive per-footer digest variants should be pursued without a decision-changing physical custody/atomic trusted-head protocol. The next logical boundary is proving the externally trusted root can be updated atomically with the archive under interrupted writes, legitimate orphan recovery, rollback and concurrent Writers; #860/#861 and O30 already show why a simple nearest-valid-footer rule or pre/post source SHA cannot suffice. Prioritize existing Reader/Writer hardening and product bottlenecks #857, #290, #749, #823 rather than treating this O0 as an immediate feature.

## CI and evidence honesty

- **Locally**: original source provider ZIP SHA checks 4/4; authentic archive cases 8/8; additive referee 8/8 with 8 deliberate forged-report refusals; after-the-fact streaming full-hash control 8/8; distinct J24G96b prospective alternate decoder 8/8 with independent 4 forged-report refusals.
- **Original hosted J24G96 run #41148609085** returned FAILURE at final manifest creation due to a shell newline-continuation error **after** the additive oracle, its detached referee and the streaming SHA control actually passed. That artifact is a partial result, not a GREEN workflow. The exact source-level and CI-topology fix preserves this failure in GitHub history.
- **Latest HEAD hosted status** must be checked from GitHub's actual run and artifacts. Do not infer success from prior runs, current code, or simulated local output; this document does not mark latest CI green.
- General tests, exact-source comparator, official product benchmarks and release/final-form evidence are **not** settled by these detached experiments. No source, native, benchmark, format or version files changed.

**No discovery state mutation:** shared `docs/discovery/STATE.json` is owned by PR #574 and remains staleable. No collision on this narrow model with existing owner #866's whole-file SHA test; a comment/issue handoff may link this result, but it must not relabel their evidence.

## J24G97 — Prospectively frozen actual-prefix two-store fault matrix (2026-10-31 UTC)

After completing the first two O0 forks, a **new preregistration before J24G97 implementation** was committed at `dd4400d2f006b118cc4b8ad761d0d1ac164016d0`. The [J24G97 instrument](../../research/j24g97_trusted_head_fault_matrix.py) uses the *same genuine eight archived footer chains*, explicitly takes the penultimate genuine physical footer and the newest footer as adjacent archive states, and computes independently trusted hypothetical heads for both.

**Local direct source result:** eight archived histories, four archive/head pairings each (**32 pairings**), 16 consistent pairings PASS and **16 inconsistent archive/head pairings REJECT**. Every actual last-DELETE append added **97 bytes** to the original physical archive, and two independently retained trusted-head digests would cost **64 external bytes**. The archive-current/head-stale case preserves a reconstructible older prefix; archive-old/head-future has no file generation matching the trusted latest head. An adversary who can control both bytes and the external trusted head trivially obtains a consistent but unauthorized rollback; that boundary was explicitly preserved.

This is *not* a performed crash, real same-process/OS atomic update, durable head service or exactly-once commit proof. It is a direct physical-history **two-store fault-state falsifier**. It narrows the actual productization veto: publishing an archive footer and publishing an independently trusted head must be reconciled across crash cuts and concurrent Writers. No new hash grammar, even one with zero archive bytes, solves that two-store atomicity alone. The next intervention belongs to a genuine distributed/durable commit protocol and physical fault-injection court, not another footer hash variant. Hosted exact-head CI still requires separate receipt confirmation.
