# J24G57 — Prospective signed-journal admission parity

Date: 2026-10-30. Base: PR #789 exact `83e9f2eb277f023186b646f667cd443b7108f268`. Research source: J24G56 PR #791, issues #792/#793. **Preregistered before writing code.** Stacked child; parent owns integration. Not a release.

## Primary falsifiable question

Can the shared r24 journal-replay helper refuse unsupported or malformed opcodes, and can the Python Reader reject nonzero r24 footer flags/reserved, using the same recovered committed generation as bounded preflight, without changing any valid r24 archive semantics or the historical corruption fallback?

- **Baseline physical negative:** #791 Actions #40980303984 observed unknown-op partial replay and invalid flag/reserved footer acceptance on Ubuntu, macOS and Windows. The provider's green result means reproduction of a bug, not correctness.
- **Prediction:** exact candidate Reader and preflight enumerate identical members for valid `del` and select the previous committed generation for (a) unknown op alone, (b) mixed unknown+known ops in either order, (c) nonzero flags and (d) nonzero reserved; valid generation remains accepted.
- **Falsifier:** any candidate opens/partially applies a malformed candidate that preflight discards, or a valid older r24 generation becomes inaccessible, or checksum-corrupt tails cease to recover. A new test that only unit-tests a helper without a real footer earns limited coverage.
- **Simpler control:** one `else: raise ValueError` in replay plus cheap footer-field validation before decompression. No new on-disk field, format revision, resource-policy threshold or external dependency.
- **Alternative explanation:** mismatch could originate in footer scanning/recovery rather than opcode dispatch alone; test must distinguish the two with both valid and invalid SHA/footer controls.
- **Adversarial cases:** unsupported opcode before and after a valid deletion; invalid list shape; nonzero reserved/flags; valid known operation; checksum-corrupted tail; later a depth/checkpoint control if integration requires it.
- **Budget:** no new compression or materialization; constant footer field checks, one opcode branch. Record any observed create/open/extract cost and avoid full-product credit from micro-only or static proof.
- **Ownership/concurrency:** PR #789 owns shared replay. This child exists only as a bounded proposed fix, with no writes to #789, #791, main or shared discovery STATE. Review parent status and source HEAD before any late mutation.
- **Evidence ladder:** source diff + independent comparison to existing preflight guards → targeted unit/physical tests → hosted exact-head CI on Linux/macOS/Windows → broader General Tests and recovery. If CI provider is unavailable, report unmeasured rather than green.
- **Promotion law:** keep v0.30.0/r24 published; no merge/release/version claim from this child; preserve O69/O72 and all historical benchmark/fingerprint gates.

Expected engineering decision: if the small shared-boundary fix survives physical and platform tests, hand it to #789 owner as a composed candidate with exact source/check receipts. Otherwise retain J24G56 as a negative and isolate the conflict.