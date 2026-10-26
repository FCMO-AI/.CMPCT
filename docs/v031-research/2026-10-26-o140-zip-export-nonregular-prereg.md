# O140 preregistration — ZIP export nonregular output admission (2026-10-26 UTC)

Status: **PREREGISTERED, BEFORE EXPERIMENTAL SOURCE/TEST MUTATION.** This is not evidence of a product win or release authority.

## Exact starting authority
- Repo `FCMO-AI/.CMPCT`, published v0.30.0 and revision-24 storage grammar unchanged.
- Prospective product baseline: O135 PR #483 exact commit `24fcc2897578c9628819971fe85d1fd264b885e2`, Reader Git blob `f1c945ac3bd93d73226c81099e95ff1a2d0a0f9d`.
- Upstream O135 owns ZIP export own-source inode alias checks. This O140 independently investigates a **different** static output-kind hazard. O137 #487 owns direct `extractall` FIFO leaves and must not be duplicated.
- Immutable input vectors: `tests/conformance/v24-direct-codecs.json`, Git blob `d10b7dab9126d39e819a74279c186363a163f2ef` (RAW and Deflate).

## Question and mechanism hypothesis
Can `CMPCT.export_zip(out)` on actual installed O135 Reader block in the presence of a **pre-existing output FIFO with no reader**, or a symlink to such a FIFO, despite O135's source-inode alias protection? The source code uses a followed `os.stat(out)` solely for source alias identity and then `open(out, 'wb')` or `zipfile.ZipFile(out,'w')`. POSIX blocking FIFO open may wait for a reader.

**Prediction:** on Ubuntu and macOS both original export routes (direct ZIP32 and `ZipFile` fallback, reached using a route-specific test override without changing the on-disk CMPCT input) will hang at least three seconds on existing disconnected FIFO leaves; disjoint/regular targets will succeed and preserve exact unmodified input. The experimental candidate will reuse the existing stat result, reject existing nonregular leaves **before opening** and without touching their identity, while still allowing ordinary regular/disjoint ZIP output. It must retain O135 source-inode hardlink/symlink refusal.

## Alternatives, controls, disproof
- Simpler control: `open('fifo','wb')` in a killable child demonstrates OS blocking physics but **cannot** establish CMPCT product behavior or which path blocked. Instrument a flushed `READER_OPENED` sentinel in the child immediately before `export_zip` after authentic Reader construction.
- Stronger control: actual original O135 installed package, exactly identical authenticated r24 inputs; separate installed candidate package; two actual operating systems.
- Compared targets: nonexistent disjoint path; pre-existing regular file; existing FIFO without reader; symlink to FIFO; existing directory. Two independent codecs RAW/Deflate and two ZIP-export writing routes.
- Plausible alternative explanation: the direct route blocks but the stdlib fallback refuses; or all attempts fail earlier at reader/source verification. Sentinel and route markers discriminate.
- Kill/narrow: either source-authentic FIFO case returns a controlled refusal in original O135, or patched Reader blocks, creates a partial file, modifies the FIFO/symlink, breaks regular output, violates O135 alias protection or r24 exact reconstruction. If host cannot create FIFO, label unsupported, never claim success.
- Any parent timeout is a measured `>=3 s` blocked observation, not a claim of infinite deadlock. Child processes are killed on timeout; no open FIFO writers in the parent.
- Decision: if original loss and candidate protection are demonstrated across both output routes and hosts, recommend composition to O135 owner; otherwise preserve the negative and avoid product credit.

## Budget, costs and nonclaims
- Small surgical guard: `stat.S_ISREG(target_stat.st_mode)` after existing `os.stat(out)`, no added filesystem syscalls; logical operations still may have an extra branch and risk changed behavior for intentional special sinks.
- Static path check remains TOCTOU-vulnerable; no descriptor-bound/atomic publication claim. No Windows named-pipe claim. No verified CPU/wall/RSS claim until full official same-input release court; `ZipFile` fallback forced in test is branch coverage, not a true >4GiB benchmark.
- Do not mutate source format, frozen vectors, historical fingerprints, comparators, gates, validators, version or `docs/discovery/STATE.json`.
- Only promote once independently validated by source-bound test suites and official performance/release law. No merge/release authority.

## Research-evidence discipline
Preserve exact original/candidate revisions, source blob identity, full archive SHA, target type/inode and subprocess result or timeout per case; retain failures, do not disable historical O135 negative control. Record source/time boundaries, outstanding CI, concurrency owner, and whether any counterfactual lesson is transferable. A green CI workflow alone is not evidence until substantive tests actually execute.
