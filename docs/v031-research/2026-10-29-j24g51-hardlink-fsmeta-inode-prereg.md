# J24G51 — hardlink inode-level filesystem metadata consistency: prospective falsifier

Date: 2026-10-29 UTC
Status: PREREGISTERED BEFORE TEST/WORKFLOW IMPLEMENTATION — science only, not a patch or release claim.
Source: canonical `FCMO-AI/.CMPCT` main `80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0/r24); exact stacked source parent #778 `47c9a4d61cd764aa4252cad741f4b22537106c60`. This test neither modifies #778 product nor overrides release/format/frozen suite authority.

## Primary question
Can an authenticated revision-24 archive contain two physical-hardlink names with contradictory signed `fsmeta.xattrs` while `preflight_archive` and `CMPCT.verify()` accept the archive, and does strict `extractall(require_xattrs=True)` silently publish one inode whose two names cannot match both signed metadata values? This is inode-level metadata consistency, distinct from J24G47 path/ordinal journal identity.

## Observed basis and controls
Source inspection on the exact parent: `validation.py` checks hardlink target existence/cycles and sparse metadata indices separately; `reader.py` materializes hardlinks using `os.link` and then independently sets xattrs by row ordinal in `_restore_extra_metadata`. In POSIX, two hardlink names refer to the same inode and cannot independently hold conflicting xattrs. This is a hypothesis, not a confirmed product defect. The existing first-party Builder can create a real hardlink archive, on which an independent wire rewrite can safely modify only self-checksummed index metadata.

## Predictions before hosted result
P1: A genuine Builder-created two-name hardlink archive with equal signed xattr values will pass native strict extraction and both paths will return the equal value.
P2: If a wire editor injects distinct xattr values at owner and alias ordinals and recomputes all r24 self-checksums, the current preflight and strong content verification will accept it.
P3: Strict extraction will either report an error or finish with one shared inode carrying only the final value, so at least one path disagrees with signed metadata. A clean success despite disagreement is a semantics weakness; refusal on contradictory metadata is correct.
P4: A **non-hardlinked same-byte pair** with distinct xattrs must remain independently representable: do not ban distinct metadata merely because file content hashes match.

## Stronger controls / alternative explanations
A preexisting validator may already reject inconsistency (falsifies P2); Builder might not recognize the OS hardlink on a host (admission failure, not negative product result); the host may prohibit user/com xattrs (unsupported environment, not proof); hardlink materialization could fail before metadata restoration (narrow observed scope). Verify actual inode identity and host xattr readback with host-native API. Run on Ubuntu 24.04 and macOS 14, source/installed product identity, strict mode; record exact specimen SHA-256 and independent wire analysis without importing CMPCT. Use source-produced authentic r24 records, not entirely fabricated archives.

## Cheapest decisive evidence / kill criteria
One equal-metadata hardlink control + one contradictory-metadata hardlink input, signed-wire independent referee, first-party installed preflight/verify/strict extract, OS-native inode/xattr after extraction. Stop/narrow if validator already rejects, if no true hardlinks, or if xattrs unsupported; do not add new product code or claim release based on synthetic adversarial data. Do not reinterpret green experimental CI as product correctness. Preserve original archive, modified archive, raw logs and both positive/negative host observations.

## Scientific disposition policy
If P2/P3 hold, report a logical exact-filesystem fidelity gap and open a narrowly scoped issue with reproduction; do not implement in another owner's Reader/validation surface. If rejected before publication, close this family as already defended by the inherited control. A future fix would require consistency based on terminal inode/hardlink owner, not per-path content equality; reject contradictions before filesystem side effects. Measure only validation and extraction timings if naturally produced, no generalized benchmark credit. Pending specialized CI is not a decision.
