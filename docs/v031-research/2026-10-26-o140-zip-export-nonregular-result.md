# O140 — ZIP export static nonregular destination: installed two-host differential result

**Decision as of 2026-10-26 03:15 UTC:** `O140_ORIGINAL_POSIX_FIFO_BLOCK_CONFIRMED__STATIC_CANDIDATE_REFUSES`. Research and source-bound product-candidate evidence only; **no merge, release, universal TOCTOU, Windows or full-performance credit.**

## Question, preregistration, ownership
- Preregistered before all O140 test/product mutations at commit `7fae82c41a23db619e200513b30f72dab775f0cd` in `docs/v031-research/2026-10-26-o140-zip-export-nonregular-prereg.md`.
- Baseline: authentic O135 PR #483 at `24fcc2897578c9628819971fe85d1fd264b885e2`, historical Reader blob `f1c945ac3bd93d73226c81099e95ff1a2d0a0f9d`; current O140 surgical Reader blob `e46e6121842d485cb209118576ebf3ba3719080d`.
- O135 retains ownership of own-source inode aliases; O137 #487 owns `extractall()` static FIFO leaves. **O140 isolates `export_zip()` to existing nonregular output objects.**
- Input: independent hand-generated revision-24 RAW and Deflate archived golden, immutable `tests/conformance/v24-direct-codecs.json` blob `d10b7dab9126d39e819a74279c186363a163f2ef`.
- Two writer routes: actual direct ZIP32 and actual stdlib `ZipFile` code, selected in the instrument by overriding only the source Reader's `_zip64_offset_fallback_required` predicate. This tests route behavior on small files, **not >4GiB ZIP64 economics**.

## Actual installed-product experiment
Hosted GitHub Actions **run [40262923385](https://github.com/FCMO-AI/.CMPCT/actions/runs/40262923385)**, HEAD `f478b391d3e7880177b9af2fecd174e82054bda7`. Four jobs succeeded:
- Ubuntu original `121378947680`: **32 passed**, raw 24 O140 + eight inherited O135 controls. Eight O140 FIFO/symlink-to-FIFO processes reached a flushed `O140_READER_OPENED` + route sentinel, then timed out at the strict 3s bound.
- macOS original `121378947726`: **32 passed**, identical eight original FIFO/symlink-FIFO timeouts.
- Ubuntu candidate `121378947566`: **32 passed**, all eight O140 FIFO/symlink-FIFO cases returned managed `OSError: ZIP export destination is nonregular`, no timeout.
- macOS candidate `121378947787`: **32 passed**, identical managed refusal without timeout.

**Aggregate: 128 directly observed test cells, 128 PASS in the preregistered differential assertions; 16 independent original FIFO timeout observations; 16 corresponding candidate managed refusals; 32 ordinary ZIP output positive controls; 16 existing-directory rejection controls; 16 own-source alias controls and 32 original O135 inherited export controls.**

Every ordinary output was independently opened with Python `zipfile`, checked by `testzip()`, enumerated, and verified against the golden logical SHA-256. Every O140 child-source SHA-256 matched before and after, including timed-out controls. Existing FIFO/symlink/directory/source-alias mode/inode did not change in any case. Authentic original and candidate installations were distinguished by `cmpct.reader.__file__` within the subprocess, and exact source blobs by CI `git hash-object`.

Original result is a **3-second bounded blocked observation**, not a mathematical assertion of endless deadlock. Successful test status on the original cases means the **expected defect was observed**, not that historical product was safe.

## Causal interpretation and cheaper control
The two source-authentic Readers differed at only the already-paid `target_stat` kind gate; the same golden ZIP input was used for both engines. The original Reader correctly rejected own-archive aliases, but permitted a FIFO leaf to reach its output `open`; the candidate rejects prior to opening. Ordinary ZIP creation remains valid on both writing routes.

A POSIX `open('fifo','wb')` micro-probe would have predicted the mechanism cheaply, but cannot replace this source-authentic end-to-end evidence: both branches and both codecs were necessary to prove the correct ownership boundary. A flushed Reader sentinel ruled out misattribution to index opening or process setup. This is a transferable static output-kind admission lesson, **not** a change to the Discovery Engine policy.

## Negative results, limits and exported costs
- The guard is static, with a race between `os.stat` and the eventual `open` or `ZipFile` path. Another process can replace a regular target with a FIFO after the check. No descriptor-bound or atomic publication guarantee.
- Intentional special sinks (device files, FIFO writers) are now refused; this is an explicit behavior change, justified for a regular ZIP file export destination and requiring product review.
- Symlinks to a regular file are still followed unless they alias the source CMPCT; no new general destination-containment security is claimed.
- Golden vectors are tiny and synthetic; no actual >4GiB ZIP64 input, Windows pipes, remote filesystems, in-place source mutation or adversarial concurrent path-swap court.
- Reuses existing `os.stat` result and adds one mode predicate, with no new stat calls or output bytes; this is derivation, **not** measured CPU, wall, RSS, p99, temp I/O, or full-product benchmark credit.
- This result is distinct from the inherited #485 four-guard extraction/Reader and O135 source alias product-fix claims. No new format revision or version.

## CI and promotion truth
At `f478b391d3e7880177b9af2fecd174e82054bda7`:
- O140 installed scientific court: **SUCCESS**, four hosts/engine matrix jobs, 128 passing observations.
- CI Topology, Version Discipline, Native Core, Continuous Fuzzing, R36 Attribution: **SUCCESS**.
- Engineering Evidence initial: **FAILURE** due to PR body heading requirements, **corrected in PR #488 metadata without validator modification; subsequent check run 40263054878 SUCCESS**.
- General Tests: **in progress at evidence-writing cut**, cannot assert pass.
- ZIP performance workflow: status **SUCCESS administratively**, substantive `performance` job **SKIPPED**; there is **no exact-head parity benchmark evidence** for O140.
- The current documentation-only follow-up HEAD may trigger new checks; their eventual statuses must be verified separately. The tests above were performed on the source-identical predecessor HEAD.
- Not merged, not released, no v0.31 promotion credit.

## Handoff / next executable decision
1. Notify O135 #483 owner of this separate static output-kind defect and the branch-sized surgical guard; do not overwrite their export implementation.
2. Review live CI and peer changes; compose this specific `stat.S_ISREG` gate into the single ZIP-export owner only if complete inherited gates accept it.
3. Subsequent independent lane: descriptor-bound output open/publication, only if a bounded credible path can preserve ordinary overwrite, inode/hardlink compatibility and stdlib ZIP64 semantics. Address Windows object types and official size/timing on the integration HEAD.
4. Do not repeat nearby FIFO cases without a new causal discriminator; baseline is allowed to win on special sink compatibility if the product deliberately changes its API.

**Scientific status:** `CONFIRMED`. **Candidate product status:** `POSIX_STATIC_FIX_VALIDATED`. **Published-product status:** `UNMERGED / UNMEASURED`.
