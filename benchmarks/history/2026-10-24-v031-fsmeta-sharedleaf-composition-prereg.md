# v0.31: filesystem-metadata preflight × atomic shared-leaf publication — prospective court

Date (UTC): 2026-10-24
Status: PREREGISTERED / NO PRODUCT CREDIT
Owner surface: isolated composition of existing PR #297 (`811722a0726af3de9b2c6fdcb67c3c4392ec5015`) and PR #303 (`dcc7371b4a34ad9c6cc666f96368324041a1f1ea`).
Released reference: v0.30.0 / format revision 24. This is not a format or release proposal.

## One narrow scientific question
Can the fail-closed revision-24 filesystem-metadata validator from PR #303 be composed with PR #297's optional fresh-inode destination publication, preserving both ownerships rather than accepting an authenticated-but-malformed metadata control plane and then modifying target entries?

## Falsifiable predictions
1. With an *index-digest-consistent* r24 archive whose `fsmeta.xattrs` contains a malformed nested value, baseline PR #297 permits construction/open or preflight but `extractall(...,atomic_shared_leaf=True)` reaches the invalid metadata only after materialization (baseline negative). The corrected integration rejects before any destination modifications, including before unlinking a shared destination leaf; `metadata=False` must not bypass archive-structure validation.
2. With valid archived xattrs and POSIX hardlink aliases already in the destination, `atomic_shared_leaf=True,metadata=True` publishes exact bytes on a fresh inode, applies the original xattr to the new leaf, and preserves the outside sibling's inode, bytes, mode and its old xattr. `metadata=False` still publishes exact bytes without pretending to restore source xattrs.
3. Existing PR #297 static protections (9 parent + 15 opt-in focused tests) and PR #303 fsmeta validation controls (including malformed self-checksummed cases, owner overflow) remain unchanged and pass together.
4. The original source and exact test ancestry remain traceable; no weakening of `ValidationError`, `verify`, size/performance comparators, source identity, or release requirements.

## Controls / alternatives
- Stronger simpler control: keep the implementations separate and do not claim a multi-owner Reader; if integration fails, preserve both branches unmodified.
- Input proof: digest-consistent index mutation (not a corrupt random archive), authentic Builder + Reader, and physical `stat`/SHA/xattr checks.
- Alternative explanation: any apparent early rejection might be `preflight_archive` called externally rather than Reader's own boundary; the interaction court must call `CMPCT.extractall` directly without explicit preflight.
- Disproof: any target/external inode mutation before rejection, dropped restored xattr in the valid opt-in case, changed old default behavior, an inherited test failure, or a different logical archive validation contract.
- Minimum evidence: baseline negative on PR #297; exact-head hosted same-source true-product tests after merge of code; classify entire CI and economic debt. Initial focused green alone is not a release gate.

## Scope / cost
Preserve current Python Reader logic in #297, transplant exactly PR #303's shared fsmeta validator and entry-point checks (not a new format). Expected added work O(fsmeta rows + xattr pairs) on each `extractall` / `verify`. Compare cold open, regular extract, and malformed rejection where useful. Index memory, full product CPU/wall/RSS, portability, adversarial concurrent parent swaps, and Public Proof remain separate gates. No writes to `docs/discovery/STATE.json` absent a decision-changing scientific result. Never merge/release as a side effect of research.

## Concurrency boundary
Independent integration is explicitly stacked on #297; #303 remains its own upstream owner. Reconcile any changed head before later shared writes. Test and source blob provenance are immutable evidence; no blind overwrites of owner files.
