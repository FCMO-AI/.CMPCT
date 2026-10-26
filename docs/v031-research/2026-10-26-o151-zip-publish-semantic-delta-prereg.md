# O151 preregistration — ZIP staged-publication semantic delta

Date: 2026-10-26 (UTC). **Research/test only; no product source mutation.**

## Authority / collision
Released CMPCT v0.30.0, on-disk revision 24; development branch `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Common source parent is O140 #488 at `d8b69758dbcbb66fe28fa7cf59598916df160d2d`. Existing *same-question owner candidates* O150 #491 `48bbb41661f8b19d369c50b06bec1018cd4400e9` and O149 #492 `ca01d885fedc8ffc343b9c3c624eddd134158452` both stage ZIP output and then replace. This independent cross-candidate court **must not rewrite either owner**, create a third implementation, or treat source-identity frozen O140 CI failures as behavioral counterexamples.

## Primary scientific question
Do ordinary successful `CMPCT.export_zip` operations retain the released *destination filesystem semantics* (new output permissions and pre-existing symlink-following behavior) after the O149/O150 stage-and-replace repair? Is there a nontrivial distinction between the two independent remedies that can guide convergence?

## Falsifiable predictions (before experimental execution)
Against the same frozen authentic r24 RAW archive, on POSIX filesystems under process umask `0o022`:
1. O140 original `open(out,'wb')` generates a previously absent regular ZIP with mode `0644` and writes through a pre-existing output symlink, preserving the symlink while changing its regular referent; no staging rename.
2. O149's explicit `os.open(..., O_CREAT|O_EXCL, 0666)` staging generates a new published ZIP with mode `0644` and stage already mode `0644` before rename; replacing an existing symlink changes the *link itself* to a new regular file and leaves its old referent untouched.
3. O150's `tempfile.mkstemp` staging generates a new published ZIP with mode `0600` regardless of umask; its stage is also `0600` for an absent public target. For a pre-existing symlink to a regular file, its successful `os.replace` also replaces the symlink and leaves the referent unchanged.
4. All engines must still produce a valid complete ZIP containing exactly the frozen `raw.bin` (0..63) and leave the CMPCT source intact. O149/O150 staging can win failure-atomicity without preserving all previously documented successful-output semantics.

Disproof: any mismatch of above predictions on an authenticated installed engine, an unexpected export failure, source byte change, ZIP semantic mismatch, broken exact candidate source identity, or independent host divergence. If a host cannot represent the symlink scenario, mark that cell unsupported rather than pass.

## Alternatives / BONK
The main practical alternatives are to (A) keep either stage-and-replace candidate unchanged, (B) reconcile mode and symlink semantics explicitly, (C) adopt an opt-in transactional export contract, or (D) preserve in-place write semantics and accept known failure-atomicity debt. Reimplementing the same stage algorithm in a third branch fails duplication/opportunity BONK. Re-running O143 CRC corruption offers little new information; lower-rung same-input ordinary-success filesystem counterexample is cheaper and can decide whether these implementations have an unaccounted release contract change.

## Test design and cost
Run standalone identical test script (its Git blob recorded) against the *actual installed* original/O149/O150 source SHAs on Ubuntu 24.04 and macOS 14, using the frozen `tests/conformance/v24-direct-codecs.json` RAW `raw.bin` bytes. Checkout each exact engine SHA separately with nonshallow git history; assert Reader Git blob; install outside the checkout. Capture a pre-`os.replace` stage-mode witness by passive spy (forwarding to real os.replace) and compare ZIP logical bytes, output mode, source bytes, referent bytes, symlink identity, inode disposition. Use the same script and fixed umask; emit auditable JSON and individual raw stdout. No evaluator thresholds, historical source lock, format, product bytes, or frozen benchmark changes. This is **compatibility research**, not an official performance gate.

## Accounting and boundaries
Mode change is not itself a proof of an externally exploitable data leak; symlink detachment is not automatically a security bug. Both may be deliberate API-contract choices and require owner adjudication. Stage naming, temp-storage capacity, ownership/xattrs, actual world-accessible directory permissions, crash durability, concurrent path swaps, Windows semantics, and archive-sized I/O remain separate. Report all negatives and repetitions. No policy modification absent repeated durable lessons.

## Handoff
If cross-candidate observations match predictions, publish the exact-head court and advise #491/#492 to converge on one owner after declaring success-path permissions and symlink policy. If evidence falsifies the predictions, preserve the unexpected behavior and provide the smallest decisive follow-up. No merge/release or v0.31 promotion is authorized by this experiment.
