# J24G75 — source-exact full-PR parity admission × signed hardlink integration (preregistration)

UTC date: 2026-10-30. Evidence parent: PR #817 at `adc070f763a93f2bc93726fc8f89308af77f9bc7`; independently proven control owner: PR #320 at `c7e3a101836c01363d69a5507bae1f628c39be9b`. Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` is unchanged. This is **evidence admission/integration**, not codec, format, version, benchmark or product-speed work.

## Baseline and decision
The current #817 stack passes 901 general tests / 2 skip and has valid physical hardlink+xattr evidence, but the inherited `.github/workflows/zip-parity.yml` still scopes by `git diff-tree ... -r HEAD`: a multi-commit material PR followed by a docs-only head may display aggregate workflow success with the actual performance job **skipped**. This is a real class, proven independently as Issue #318 / PR #316. The mature source-exact repair and a real Git-DAG court already exist in PR #320; inventing another classifier would duplicate an owned solution.

## Prospective prediction
A **blob-exact transplant** of PR #320's proven classifier, workflow gate, CI topology ratchet and tests onto the exact #817 base will:
1. make the classifier RUN for the known historical #316 source-first/workflow-last witness and synthetic multi-commit product-first/doc-last DAG;
2. preserve SKIP on truly irrelevant net PR trees and net-reverted source, and RUN on source deletion/rename, inaccessible or ambiguous history;
3. make the full `zip-parity.yml` admission execute at PR exact head with full Git history and unchanged ABBA comparator/thresholds;
4. pass the original 12/12 deterministic Git-DAG and 2/2 inherited native materializer tests (plus current topology); no change to r24 archive bytes, Writer, Reader, native, Builder;
5. preserve inherited #817 correctness and physical hardlink/xattr/rollback evidence. The new PR **does not itself earn release parity**: comparison against #817 parent will test only this CI-only delta, not independently re-prove the complete ancestor stack against released main.

## Simpler control, alternatives and kill conditions
The cheapest control is the old last-commit classifier on the same historical #316 HEAD (predict SKIP) and exact PR #320 classifier on that HEAD (predict RUN). Outer GitHub `pull_request.paths` is insufficient alone; changing comparator or failure thresholds is prohibited. Rewriting the classifier independently loses provenance. Reject or narrow the composition if any source-exact blob differs without explicit reason, if the wrong HEAD is admitted, any relevant source-side deletion becomes SKIP, any inherited regression/error appears, or if a completed workflow is misrepresented as timed-performance evidence when its substantive job is skipped.

## Concurrency, carrying cost and scope
#320 owns the classifier implementation; #817 owns the hardlink+journal composition. This branch is an **explicit integration** of the existing owner code, not a competing implementation. Original owner PRs remain untouched; source SHA and integration SHA are recorded. Full-history fetch and potentially repeated 45-minute parity receipts are real compute costs, preferable to false-green omission. No changes to `docs/discovery/STATE.json` (owned by PR #574). No release, merge, public version or benchmark promotion authorized.

## Discriminator after CI
First require a focused exact-head classifier/CI-topology court. Then inspect the substantive r24/ZIP parity job identity at the exact HEAD; `workflow success` alone cannot authorize a performance claim. If general correctness fails, classify root cause against inherited parent before modifying product.
