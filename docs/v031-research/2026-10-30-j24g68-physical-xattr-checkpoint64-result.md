# J24G68 — Authentic 64th signed-xattr checkpoint after 63 mixed generations

Date: 2026-10-30 UTC. **Decisive research evidence, not product integration or release authority.** Parent [#810](https://github.com/FCMO-AI/.CMPCT/pull/810) `f9246d33748fb97532d711f0a81760c3505a7a4a`; immutable prospective preregistration `911fe68451dabb5ad8b238e8dc5ea8a798ce37fd`; measured source HEAD **`2baa1a6f551b0752fc0b534684a8043cf1c57af8`**, exact inherited replay blob `03743ca2a06c022c2ec64243a90fe373cf91e899`.

## Scientific decision

**J24G68_PHYSICAL_CHECKPOINT64_FIDELITY_PASS for Ubuntu 24.04 and macOS 14; NO PRODUCT PROMOTION.** Official [two-host GitHub Actions #41018894516](https://github.com/FCMO-AI/.CMPCT/actions/runs/41018894516) completed SUCCESS on both, including independently authenticated physical footers and metadata index. A separate third-root offline audit not importing CMPCT used the original Actions artifact ZIPs, Python `msgpack`, system `libzstd` via `ctypes`, raw struct framing and a distinct path-keyed replay: it also independently reproduced both physical checkpoint states and rejected a corrupted footer digest. Do not confuse this independent index/metadata evidence with a separate full codec/blob extractor.

## Exact archived source and costs

| Measured physical quantity | Ubuntu 24.04 | macOS 14 |
| --- | ---: | ---: |
| Public pre-checkpoint physical archive, bytes | 29,486 | 29,486 |
| Public post-64th-checkpoint archive, bytes | 31,320 | 31,308 |
| Checkpoint+footer added bytes | **1,834** | **1,822** |
| Final logical content bytes | 7,552 | 7,552 |
| Final logical files | 118 | 118 |
| Sparse xattr-tagged logical identities | 5 | 5 |
| Old signed footer chain (63 deltas + base) | 64 | 64 |
| New complete checkpoint footers visible in latest-reader chain | 1 | 1 |
| New checkpoint physical previous pointer | 29,418 | 29,418 |
| Public checkpoint Writer wall, ns (one sample) | 6,438,439 | 5,147,375 |
| Public checkpoint Writer process CPU, ns (one sample) | 4,405,444 | 3,720,000 |
| Archive prefix before update | Byte-identical | Byte-identical |
| Inode retained on public append | Yes | Yes |
| Prior chain recovered after newest footer digest flip | Yes | Yes |

Complete archive SHA-256: Ubuntu **`9837697d44a8001a93a890806e8d1fb74ea88445cab5acaaab3a27da9280445e`**; macOS **`10fc9ce6e57ed46ed7270049087faf5fbba1a4f73a49ec89dedb5bceb843b743`**. Physically signed exact final MessagePack SHA-256: Ubuntu `27a2a1d2cea11538f4d0116c20a198d37fb1784828b470517bae329de28f8382`; macOS `f3cd45071ab6853ed39e13900f8a100c123ee0457433f40883185f150838fa2e`. Host-specific actual physical archives and xattr representation need not be byte-identical across systems.

Source original retained GitHub Actions ZIP:
- [Ubuntu artifact 12960876166](https://github.com/FCMO-AI/.CMPCT/actions/runs/41018894516/artifacts/12960876166), full ZIP SHA256 `4183f8ce24454d14485bc107f7355eaa426fb5a6e9de20060c1e7984ffb0c2e9`.
- [macOS artifact 12960686837](https://github.com/FCMO-AI/.CMPCT/actions/runs/41018894516/artifacts/12960686837), full ZIP SHA256 `1b9494d028aafa0e6f83a190e8b1a51c4d4205fc3efdf8b3cbb80051c94aacc6`.

Both original ZIPs were downloaded separately, SHA256-authenticated, and their raw JSON and two physical archive members individually inspected. Third-root audit independently read/authenticated original primary index and all 64 prior footers; reconstructed 63 mixed public operations by *logical path*, including xattrs; applied operation-64 rename by identity; verified appended physical full checkpoint footer, previous-pointer linkage and final MessagePack byte identity. Two independent footer-corruption and xattr ordinal mutation controls in hosted referee passed.

## Scope, limitations and strongest negative

**Not an integrated Reader speedup:** this candidate modifies no `src/`, Reader, Writer, native code, format or released version. One Writer call's CPU/wall is not comparative performance evidence. No peak RSS, cold disk, full size/create/extract benchmark, ZIP/Zstd comparison, adversarial same-UID publication, full hardlink inode metadata alias, privileged `owner_overrides`, Windows native xattrs, or full recovery matrix. Do not infer generic cross-filesystem safety or full strong archive verification.

Original **FAILED** hosted [run #41018607985](https://github.com/FCMO-AI/.CMPCT/actions/runs/41018607985) had a documented **instrument cardinality mismatch**. It expected **117** members copied from a *different* J24G64 physical fixture, but the actual J24G66 parent has **118** (128 base − 21 deletes + 11 true new inserts, with other PUTs replacing existing paths). Both hosts stopped before the 64th Writer operation; this was never a negative checkpoint result. Corrected ONLY this fixture count in witness and detached referee, preserved original preregistered footer/xattr/MessagePack/hostile assertions. The initial run and observation document remain intact. The separate external third-root offline audit initially had a Python bytearray/ctypes mutation-type handling error *only in a negative corruption probe*, corrected by converting the disposable mutated input to bytes; positive physical reconstruction and original SHA verification were unchanged. Do not hide this independent auditor instrument negative.

## CI / promotion truth for measured code HEAD

- J24G68 exact-head Ubuntu/macOS scientific CI **SUCCESS 2/2**, source-attested original ZIPs and detached result included.
- Engineering Evidence **SUCCESS** after PR description supplied exact mandated headings; earlier failed runs preserved.
- CI Topology **SUCCESS** after adding mandatory top-level concurrency with cancellation; earlier failed run preserved.
- Version Discipline **SUCCESS**, R36 Attribution **SUCCESS**, Darwin xattr lane **SUCCESS**.
- General CMPCT Tests on measured HEAD **FAILURE — 875 passed, 5 failed, 2 skipped**. Exactly the same five inherited failing classes reported for parent #810: four historical custody/fingerprint/public-surface tests and one superseded expectation that sparse ordinal metadata stays wrongly bound after a deletion. **No evaluators changed or waived**. No official full-product release benchmark was executed.
- Any later documentation-only HEAD requires its own CI identity; do not carry measured-code green claims across source changes.

## Ownership / next action

Shared signed-journal product owner [#795](https://github.com/FCMO-AI/.CMPCT/pull/795) and mixed factored replay owner [#808](https://github.com/FCMO-AI/.CMPCT/pull/808) can now treat the exact 64th-generation physical signed-xattr checkpoint composition as **tested in research**, not as shipped safety or performance. The next highest-value executable product experiment is a controlled **true Reader integration** of #808's factorized mixed-generation replay against source-identical public Writer physical xattr archives, with matched same-runner cold-open CPU/wall and RSS, strict metadata/recovery/hardlink, checkpoint64, fallback, and full inherited release gates. Preserve independent publication-inode defect #749 and its separate security authority. Discovery State #574 belongs to another agent; this run did not update it. No policy change earned.
