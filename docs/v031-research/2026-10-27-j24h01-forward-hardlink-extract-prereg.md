# J24H01 — Prospective forward-hardlink extraction-order court

**Date:** 2026-10-27 UTC. **Status:** preregistered before instrument and outcome. **Lane:** research / independent correctness falsifier, not a product fix.

## Authority and concurrency
Published CMPCT main source `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, revision-24; Reader `src/cmpct/reader.py`, strict admission `src/cmpct/validation.py`. Source owners: #569 composite Reader geometry, #609 direct blob size, #615 hardlink alias-size validation, #613 streamed sparse verification. None owns this exact extraction-order question in the current open PR scan. Work exclusively on this isolated independent test branch; no source-owner modifications. Discovery `STATE.json` remains a staleable cache, never a claim.

## One falsifiable question
Can an independently authenticated revision-24 image with a **valid forward K_HARDLINK alias** pass strict preflight, regular Reader read/verify, yet fail an empty-root `extractall` because the extractor demands the target already exist on disk?

## Observed baseline mechanism
The Builder walks paths lexically and ordinarily chooses the first observed inode path as physical owner. It does not establish a format rule forbidding aliases that lexically precede targets. Strict `_validate_index` records hardlink references after loading every row, checks target existence and cycles, but imposes no lexical order. `CMPCT.read` recursively resolves target logical paths; `extractall` makes a single lexical pass and fails if a hardlink target is not yet materialized. This is a predicted control-flow contradiction, not yet product evidence.

## Controls and test method
1. Create an ordinary Builder archive containing two real filesystem hardlinks; verify preflight, full read/verify, extraction, same inode and exact SHA.
2. Construct a **new fully signed/index-hashed image**, not a byte-tampered forged checksum, using unchanged Builder-created blob records, rebuild both compressed index copies and the footer, and swap logical owner/alias names so `a-alias` points forward to `z-owner`. Require strict preflight, complete reads and `verify()` on that image before attempting empty-root extraction.
3. Repeat with a three-name two-hop forward chain `a-alias → b-alias → z-owner`, preserving row sizes and owner payload.
4. Preserve all exact source SHA/physical output hashes, stdout/pytest observations, environment, observed outcomes and dependency identities. No change to frozen workloads or Reader/Builder/Validator. An independent Python oracle checks the input source SHA and canonical header/index/footer integrity before applying Reader APIs.
5. Run hosted Linux, macOS, Windows where native installation supports tests; hardlink POSIX and Windows ability to create real links is environmental, so do not silently relabel host permission failures as product regressions.

## Predicted result and kill/narrow conditions
**Prediction:** Builder control passes; the fully signed forward-reference archive passes strict preflight, `read()` and `verify()`; then extraction rejects the forward target with `hardlink target not yet extracted`. A second chain is accepted by strict preflight but fails extraction. Distinct error, material content corruption, or strict refusal changes the conclusion.

**Falsification:** any exact-source host extracts correctly, preflight rejects the signed forward reference, or Reader read/verify rejects it invalidates or narrows the predicted mismatch. Do not weaken the control or rewrite this preregistration after result. Environmental CI failure is unmeasured.

## Decision and productization boundary
If reproduced, register a narrowly scoped issue with original artifact identities and hand off to the actual extraction owner #569 for semantics/ordering. A repair must consider link chains, cycles, link targets that are symlinks/directories, cross-platform inode identity, symlink pivot and destination-race safety, partial writes, bounded traversal and complete release parity. A simple pre-sort is not assumed sufficient. If not reproduced, retire the hypothesis and preserve the negative.

## Cost and comparator law
The test is a bounded correctness oracle with trivial logical bytes. It confers **zero** archive-size/performance/release credit. No claim of remote attacker exploitation; authenticated metadata can be created by an encoder, but end-user trust boundaries depend on the application. The strongest simpler control is unmodified Builder output. Evidence of disagreement between strict-valid/read-valid and extraction failure is the causal target.

## Counterfactual discriminator
The cheapest prospectively recognizable predictor is whether preflight enforces dependency/topological order matching extractor traversal. That distinction generalizes to all logical-reference storage kinds and should be preserved if decisive.
