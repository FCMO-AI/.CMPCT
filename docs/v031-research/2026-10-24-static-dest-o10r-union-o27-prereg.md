# O27 — Static destination containment × signed-generation bounded Reader (preregistered)

Date: 2026-10-24 UTC. Status: PREDICTION, BEFORE PRODUCT MODIFICATION.
Repository: FCMO-AI/.CMPCT. Released v0.30.0/r24 is unchanged.
Exact base: PR #365 HEAD `54c998200b1908b696ade049fe94df71a736c284`.
Independent original mechanism: PR #269 HEAD `0273c628872dce672936aa0ddd555ed10a900bf7`.
Independent stronger alternate: PR #272 fd-root research (not a full filesystem-containment proof).
No concurrency-protocol file exists in the canonical development path as of orientation.

## Problem / evidence boundary

Issue #265 and PR #264 reproduce an authentic revision-24 extraction that follows a
**preexisting** destination symlink to overwrite an outside sentinel. O9/O10R
protects archive-created pivots and signed targets before member writes but
does not call PR #269's static destination lstat guard. PR #269's owner branch
has a direct adversarial product court, yet it is based on an earlier Reader.
Current O10R inherits signed generation resource ceilings, journal replay,
installed-wheel safety and cross-platform archive namespace behavior.
Convergence is more valuable than another owner-specific heuristic.

## Hypothesis / causal mechanism

Source-exact transplant of PR #269's narrow `_preflight_existing_destination_links`
and its call **after** all signed-path/symlink-target prechecks but **before**
any member/directory publication closes the *static* preexisting destination
symlink pivot in O10R, without replacing O10R Reader or changing the r24 format.

Primary test: authentic O27 corpus exercises both hazards on a **single** archive:
a prior innocuous member, a preexisting later symlink ancestor and a hardlink
graph (owner and alias). Assert outside sentinel byte+inode unchanged, first
member not created, and O10R still resolves safe hardlinks. Replay the original
PR #269 owner's eight authentic tests unweakened, including explicit
`safe_symlinks=False` opt-out, valid symlink-leaf replacement and user-selected
symlinked root. Retain O10R resource and safety controls, general suite, exact-head
native/CI, installed package and official performance gate.

## Competing frames

1. Do nothing: the proven static outside-write remains open.
2. Full fd-root/O_NOFOLLOW redesign: potential stronger race boundary, but PR #272
   owns research and already records a moved-directory inode limitation.
3. Bounded source-exact static preflight: modest interim safety with explicit
   concurrent-destination TOCTOU debt; smallest cross-owner integration.

## Prediction, disproof, losses and admission

Predict original eight owner tests plus new cross-mechanism test pass and existing
O10R courts remain green; no outside sentinel changes. Reject the hypothesis on
any external write, false rejection of an allowed owner/alias/root, change in
archive bytes, resource limit or signed target policy, or weakened test oracle.
Measure potential preflight overhead via unchanged official CI against correct
base; retain every negative. Do **not** claim race-safe extraction, atomic
publication, provenance, source lifetime stability, storage-size win, or full
Windows/macOS symlink semantics from a POSIX court. Do not merge or release without
full exact-head evidence and the repository release decision.

Expected decision: whether a previously proven **static** containment correction
can coexist with the more advanced Reader without losing its existing capabilities.
Ownership remains with PR #269 for the original fix; this branch owns composition only.
Detailed outcomes will be appended, never rewrite this prediction.
