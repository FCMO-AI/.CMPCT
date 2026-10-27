# J24D07 — direct staged extraction at POSIX NAME_MAX (prospective)
Date: 2026-10-27 UTC. Status: FROZEN PRIOR TO PRODUCT CHANGE OR CANDIDATE RESULT.
Owner: Phased1; isolated branch stacked on J24D05 PR #591, exact head `931caff9a03c80bafaddec21864ae55e7e2314c0`, Reader blob `18fe5721cbe2ae32a907288008a537c731413be5`.
Published base remains v0.30.0 / physical revision 24. The branch is scientific/product draft, not release or merge authority.

## Primary question and baseline
J24D02/J24D05 introduced `_extract_direct_staged` to preserve preexisting files after post-authentication ENOSPC, using a sibling `tempfile.mkstemp(prefix='.' + basename + '.cmpct-part-')`. A perfectly legal 255-byte POSIX basename makes this temporary component > NAME_MAX and fails with ENAMETOOLONG even when the final output name itself is valid. The previous published direct writer used `os.open(full, O_CREAT|O_TRUNC)` and admitted that basename, but lost the prior file on later write faults. Chunked NAME_MAX has an independent known owner #256, composed with sparse in #270; do not rewrite those owners or claim their issue solved.

## Independent cheap kernel falsifier (before patch)
Linux local temporary directory: source filename of 251 ASCII n bytes plus `.bin` is exactly 255 encoded bytes. A mkstemp with the existing 268-byte prefix fails errno 36 (ENAMETOOLONG); a sibling with the 12-byte `.cmpct-part-` prefix succeeds and yields a 20-byte component. This only proves the syscall filename mechanism, not that a CMPCT Reader recovers correctly.

## Prospective hypothesis and controls
Change only the direct staged helper prefix to a constant short sibling prefix; retain randomness, same-directory atomic publication, verified source bytes, fd-only optional chmod, ENOSPC rollback and final cleanup. Build an authentic revision-24 single S_BLOB .bin archive from a deterministic 255-byte POSIX filename, check the exact Reader representation and entire file SHA against its source, then test:
1. fresh-target extraction succeeds and creates *exactly* the long name;
2. existing-target extraction replaces bytes correctly;
3. after an actual kernel short write of 1–7 bytes followed by injected ENOSPC, the old target SHA and inode remain unchanged and no short-prefix staging leaf remains.
The original long-prefix Reader should fail at creation of the stage (ENAMETOOLONG). Candidate must pass all three states on installed or genuine Reader. POSIX Linux and macOS are the target platforms; Windows is not credited with a POSIX NAME_MAX claim. Test both malformed and honest inputs wherever already covered by inherited J24D02/J24D05 unchanged courts; preserve historical source SHA validators.

Kill/revert conditions: any path truncation/renaming, wrong SHA, loss of previous target after ENOSPC, unexplained stage residue, collision overwriting an existing file, new pathname-mode mutation, or new mismatch in inherited behavior. Do not change the test/fixture, release gate, threshold, public scores, format, or original owner PR to rescue it.

## PARETOBONK / alternatives
- Truncate the original basename: destroys exact filesystem identity, reject.
- Stage in system temporary directory: risks EXDEV and weakens atomic replacement, reject.
- New descriptor-root / Linux O_TMPFILE publication: can be stronger against same-UID attackers but doesn't provide portable existing-target atomic replacement; another owner #528 and #557 explores this, not this narrow question.
- Short same-parent private sibling name: proven in independent chunked NAME_MAX owner #256; minimal reversible local fix. Still a mutable name, and **not** a hostile directory-writer security solution.

## Costs, scope, and decision
No archive bytes, codec, index, ABI, version or Builder policy mutation. Constant-length prefix should have negligible ordinary cost; ordinary whole-system wall/CPU/RSS and temp I/O, symlink/ACL/mode/hardlink semantics and exact-head full parity remain unmeasured. A hosted test failure may be due to platform path support; preserve negatives and localize.
No Discovery Engine global-policy or STATE.json change absent repeated decision-changing evidence. An unmerged scientific PR may credit only a source-bound candidate; release requires owner composition and all gates.
