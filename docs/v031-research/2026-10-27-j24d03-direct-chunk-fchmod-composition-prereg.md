# J24D03 — Direct-output rollback × missing-fchmod chunk portability (preregistration)

Date: 2026-10-27 UTC
Status: **FROZEN before J24D03 source implementation or hosted evaluation**
Owner: Phased1 independent composition; no mutation of owner PR #585 or PR #536.
Starting commit: J24D02 #585 `8b171362abf93d778b7f2e7100c8e1a2aa94ca60`
Inherited Reader blob: `8b74c3994b59af63528acff960cd7f59f535bf8f`
Independent upstream J24W02 #536: `7973dbf904ff0660971d2e112d9f77b38f37019a`

## Primary falsifiable question
Can the *existing validated* J24W02 optional descriptor-mode availability repair be composed without modification into J24D02's ordinary direct-member staged writer, so that all five frozen revision-24 direct/chunked output-failure controls pass on Ubuntu, macOS **and Windows**, preserving SHA-exact good output, both destination-preservation guarantees, POSIX fd-only chmod, absence-of-fchmod portability and narrow exception semantics?

## Baseline and strongest controls
- Released v0.30.0 r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0` is the published reference; none of the candidates is released.
- Original J24D01 #581 proves ordinary direct `O_TRUNC` destroys pre-existing output after a seven-byte real write then ENOSPC.
- J24D02 #585 (source above) demonstrated direct staged success on Ubuntu/macOS, Windows *direct-only* success, and an **inherited** Windows chunked `AttributeError: os.fchmod absent` in the full 5-vector court. Preserve that red as historical evidence, not product regression of direct staging.
- Upstream J24W02 #536 already passed authentic three-host installed chunked vectors with a four-line optional `getattr(os,'fchmod',None)` + `OSError` boundary. This is **composition of a proven owner patch**, not an independent invention.
- Frozen Builder-independent `tests/conformance/v24-direct-codecs.json` (3 records) and `v24-chunk-maps.json` (2 records) remain unchanged.
- Original J24D02 scientific code/referee and original historic identity-gated workflows must remain byte-for-byte unchanged; a new source-coupled referee/workflow owns the *composed* result.

## Competing actions / BONK decision
1. Chosen: transplant **only** J24W02's fd-mode patch to J24D02's chunked helper and independently re-run all ten clean/error control cases on three OSes. Minimal reversible change, high information gain; disproof could block product portability.
2. Run direct-only Windows again: evidence already exists, cannot decide full three-host composition.
3. Rewrite all extractor representations or adopt existing J24C02 #569: expands owner/safety/convergence surface; current #569 has confirmed cold-open performance debt. Do not duplicate.
4. Introduce pathname `os.chmod(tmp)` fallback: rejected because #528 established staged-name substitution; do not widen the attack surface.
5. New format/decoder/native implementation: no evidence justifies the cost for one missing optional POSIX API.

## Locked prediction and disproof
- `S_BLOB` RAW/Zstd/Deflate and S_CHUNKS/S_CDC: per host five exact normal files; five fault-injected files preserve destination bytes+inode; real short kernel write followed by ENOSPC, no leaked temporary paths.
- Windows has no `os.fchmod` and nevertheless all ten cases pass. macOS/Linux retain descriptor-bound chmod.
- Simulated absent `os.fchmod` on every host must preserve chunked extraction. `OSError` while applying an optional mode remains narrowly tolerated; unexpected `ValueError` must propagate with old output intact.
- Falsify on ANY altered frozen bytes, erroneous source identity, successful short-write test that did not truly write, bad file SHA, missing/duplicated case, lost sentinel, stage leakage, swallowed ValueError, or any host's positive extraction failure.
- The independent receipt referee must reconstruct declared sentinel and fixture SHA expectations and reject deliberately mutated JSON receipts. Preserve original historic J24D02 referee's hard-coded blob as immutable, **do not update its expected source hash**.
- Preferred evidence: one three-host installed-package Actions court with checkout/current source SHA and stable raw artifact identities; original historical red check may reject source identity after composition and is not to be bypassed.

## Costs / limits / product decision
No new format, core version, release gate, archive-size win, or performance claim. Incremental cost is a feature lookup per chunked extraction, not independently timed. POSIX mode application remains fd-based; Windows best-effort mode restoration unchanged. Staged output continues to change hardlink aliases/inode on successful overwrite; same-UID pathname replacement after SHA (#528), postpublication namespace rebinding (J24P04), source truncation SIGBUS (#460), sparse logical SHA (#572), global transaction atomicity and crash durability remain separate debts. A passing targeted court earns candidate **composition evidence only**, not release readiness.

## Durable next action
After frozen code + hosted case validation: report exact branch/HEAD and PR to #585/#536 owners. Do not force-merge, change owner branches, edit shared discovery state (#574 owner), or relabel historic controls.
