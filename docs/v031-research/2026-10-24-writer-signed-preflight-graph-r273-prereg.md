# R273 — Writer/recovery × signed ancestry × bounded hardlink preflight (preregistration)

Date: 2026-10-24 UTC. Independent, stacked **integration experiment**, not a release, not a new on-disk revision. Source base `FCMO-AI/.CMPCT` PR #328 exact `36c5c737c2896b9ad9ee68c491ff921fbd36aaa4`. The owner of strict authenticated structural preflight is #339/#341; the owner of hardlink traversal amortization is #342 exact `a480d7ae2f1480f15e73eda2b04e48b1a75e66b1`. Do not modify any owner branches. The eight custody blobs and Writer/Reader recovery guarantees on #328 must survive unchanged except an exact narrow prewrite ancestry guard in Reader.

## Baseline and primary question
#328's Reader retains Writer/recovery, resource teardown, physical PACK commitment and hardlink owner-order behavior, but does not have #341's prewrite non-directory ancestor trie; its strict validator also re-walks valid hardlink chains in potentially O(N²). #341/#342 prove these safety properties independently but do not include #328's integrated Writer/Reader.

**Question:** Can a minimal, source-exact validator blob from #342 plus one source-exact Reader prewrite ancestor guard from #341 and their authentic tests be grafted onto #328 without losing any inherited functionality or its release-parity rules?

## Falsifiable prediction
1. Exact graft preserves #328 Reader content outside the small guard; its inherited transaction/recovery/resource tests remain green.
2. All signed impossible file/hardlink ancestors are rejected before member writes in ordinary extraction and strict preflight; valid implicit directories and valid hardlink graphs remain accepted.
3. Signed valid 1024-link chain and star graphs are preflightable without quadratic owner rewalking; malformed terminal, cycle, wrong-kind and indirect missing-owner chains fail closed with ValidationError.
4. Full general suite, actual r24/ZIP performance job and infrastructure gates remain uncompromised. Any core-source/format/threshold change outside the stated guard invalidates the experiment.

## Controls, alternatives and disproof
Simpler control: leave features split across PRs with clean independent results; that avoids integration complexity but leaves product incomplete. Replacing Reader wholesale with #341 would silently discard #328's validated recovery and resource-owner guarantees; prohibited. Replacing Reader wholesale with #326 would also lose newer guards. A source-exact validator is warranted only after verifying that #328 and #342 share all validator text except the signed-tree and hardlink traversal block.

**Disproof:** any inherited test fails; any hostile signed tree is partially published; a valid control becomes unreadable; material source outside target guard drifts; benchmark is skipped or red; or evidence/CI cannot be bound to exact HEAD. Preserve negatives and stop promotion even if a subset is green.

## Cost and scope
Expected implementation touches `src/cmpct/validation.py`, a narrow block in `src/cmpct/reader.py`, and the exact independent owner tests. No Builder/native/format/version/corpus/release-lock or comparator changes. The validator trie is O(total path components), and owner memoization O(hardlink edges) expected; measured performance and RSS require independent evidence. An unchanged Builder means an official timing green is conformance, not an earned speedup.

## Decision status
PREDICTION_LOCKED_BEFORE_CODE. Await source-exact graft, installed-package tests, hosted parity and adversarial review. No product/release credit yet.
