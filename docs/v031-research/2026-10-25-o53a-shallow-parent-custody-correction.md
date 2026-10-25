# O53a — Exact historical Writer A/B in shallow general CI: failure, diagnosis, guarded fallback

**Date: 2026-10-25 UTC.** Append-only methodological correction to the original immutable O53 preregistration and positive results; this note does not change their predictions or rewrite the failing observation.

## Direct negative — final documentation HEAD bdb525a9

[General Tests workflow 40162066575](https://github.com/FCMO-AI/.CMPCT/actions/runs/40162066575) on exact HEAD `bdb525a91507c8905b699d390bcd48eda963235f` finished **FAILURE: 1 failed, 885 passed, 8 skipped** (209.22 seconds). The single new O53 test `test_exact_immutable_parent_and_combined_writer_emit_identical_supported_archive_bytes` tried `git show c1e75370281ca6b721ef10edf1ed15e6c5ef48f7:src/cmpct/transactions.py` in **general CI's shallow checkout**, which lacked the historical parent commit object. `git show` exited 128 before any parent/candidate A/B ran. The test did not demonstrate a CMPCT product regression; the general suite nevertheless remains formally FAIL. Do not label the original general workflow PASS or delete its red receipt. This contrasts with the focused O53 3-host source-bound workflow, which deliberately checks out full history and passed the very same actual-source A/B.

## Repair hypothesis and strongest honest control

The strongest comparator is still the *entire immutable #311 original Writer source* (Git blob SHA `a3b9c3375ed19f0b37d40ee47ead7b5d5b8905ee`), not a synthetic implementation of only `Path.read_bytes()`. Merely marking the test SKIP on shallow checkout would reduce proof coverage; fetching history over network during a general test makes a correctness gate depend on provider networking.

Fix: vendor that complete historical Writer source in a transparent test fixture `tests/o53_frozen_311_transactions.py`, whose **Git blob is independently checked against the frozen SHA** before compiling. First try literal `git show` when the historical object exists; otherwise use the exact fixture. In either path recompute Git's `SHA1("blob " + byte_length + NUL + raw_bytes)` and reject a mismatch. The same test still independently executes historical and combined complete Writers against identical input and checks full physical r24 bytes for regular and two CDC generations; no test assertions, thresholds or comparator semantics were removed.

The standalone frozen fixture was created from GitHub's exact #311 source, and a new source-bound O53 workflow pins both that source blob and the updated test blob `bf58817ec76812ac8552d523c89325b5b3de33f4`. The focused CI explicitly copies the fixture next to isolated tests; general checkout already has the fixture locally. No product source changes beyond the existing O53 Writer blob `79ea9e423d155b106f40cd0811075c69ff04f105`, no format changes and no promotion credit.

## Decision and disproof

**Infrastructure/evidence-custody regression found and repaired in candidate source, verification pending at this record's commit.** Kill/repair if the fixture's Git blob differs from the frozen parent, if either CI mode fails to actually run the historical A/B, if a candidate r24 archive differs in complete bytes, or if follow-on general CI still fails. Preserve both the actual failing [general run 40162066575](https://github.com/FCMO-AI/.CMPCT/actions/runs/40162066575) and future corrected run receipts. General scientific evidence is not retroactively upgraded. This is a **local reproducibility fix**, not evidence of new compression, decode, safety or release performance.
