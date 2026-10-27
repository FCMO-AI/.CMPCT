# J24D02 preregistration — direct-member per-file output recovery

Date: 2026-10-27
Status: FROZEN PREDICTION BEFORE CANDIDATE OR INSTRUMENT
Owner: Phased1, isolated branch `agent/phased1-v031-j24d02-direct-staged-output-20261027`
Base: released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
Related: confirmed J24D01 [PR #581](https://github.com/FCMO-AI/.CMPCT/pull/581), [Issue #582](https://github.com/FCMO-AI/.CMPCT/issues/582), independent sparse defect #572, staged-name threat #528.

## Primary question

Can the released direct S_BLOB/fallback output branch preserve a **pre-existing regular destination** when a real short write is followed by ENOSPC, without changing archive format, source-authentication semantics, or successful extracted bytes, by writing the already authenticated immutable `read()` result to a sibling temporary file before publication?

## Strongest existing control and alternative explanations

- Original released direct implementation: `read(rel)` authenticates the input, followed by `os.open(full,O_TRUNC)` and `os.write`, leaving a seven-byte corrupted output under deterministic ENOSPC (J24D01 source-exact Ubuntu/macOS).
- Released S_CHUNKS/S_CDC implementation already uses `mkstemp` → bounded write loop → whole-file SHA → `os.replace`; under identical fault it preserves prior target.
- Hypothesis: moving destructive writing off the destination inode suffices for **ordinary output I/O failure atomicity**, *not* for hostile same-UID namespace custody, power-loss durability, or whole-archive transactions.
- Alternative explanation/failure: source vector or writer interception not actually exercising the changed branch; the injected write could fail before a real kernel write; cleanup could leave a stage; platform-specific permission APIs could prevent extraction; metadata/inode/hardlink semantics could regress.

## Candidate and genuine alternatives

1. Candidate: single small `_extract_direct_staged` helper; existing `self.read(rel)` authentication; fresh sibling temporary; no final name publication until all bytes were written; close and `os.replace`; best-effort `fchmod` only on platforms that provide it; guaranteed stage cleanup on exceptions. No changed wire/ABI or codec.
2. Stronger but costlier ownership: descriptor-to-name `O_TMPFILE/linkat` for absent destination (J24F11) is Linux-only, and `linkat` cannot overwrite occupied names. J24P03 falsified named-stage+second rename under same-UID attackers. Not a substitute for portable failure-atomic ordinary writes.
3. Fail-closed on existing target or permanent in-place backup would introduce incompatible semantics or more state; research-only alternatives, not selected for this binary experiment.
4. Unified all-representation staged writer may later be warranted but changes concurrent sparse and chunk owners; do not start broad refactor here.

## Locked evidence and disproof

Use exactly the existing Builder-independent r24 conformance JSON at `tests/conformance/v24-direct-codecs.json` and `tests/conformance/v24-chunk-maps.json`, tested via an installed package outside source checkout. Five original members per host: three direct codecs, two inherited chunked controls.

On Linux/macOS (Windows as a separate portability falsifier where hosted capacity permits): run five normal extracts and five injected failures. Each failure intercepts the Reader's `os.write`: perform an actual kernel short write of up to seven bytes on first call, then raise ENOSPC on call two. Prior destination has a nonempty SHA-tracked sentinel. On direct fault **expected**: raised ENOSPC, prior SHA unchanged, prior inode unchanged where stable, no `.cmpct-part-` remnants. Chunked remains unchanged. Clean controls reconstruct exactly. Report source blob SHA, archive SHA, row SHA, before/after SHA/inode, injected count, stage cleanup, and OS. Reject fake receipt mutations independently.

**Kill/narrow** if any direct fault mutates its original destination, no real short write is observed, any clean member mismatches, chunked loses inherited preservation, stage remains, any tested host cannot use candidate, or metadata/final destination semantics become unacceptably incompatible. A source/blob mismatch invalidates evidence rather than awarding failure/success. Do not move these criteria post hoc.

## Explicit cost and security debt

- Before failure: temporary physical bytes up to full decoded member size, write bandwidth and syscall count, rename, disk space; existing `read()` already materializes the direct member in RAM. A clean overwrite changes destination inode, external hardlink alias semantics, and perhaps ACL/xattr/mode; test and disclose rather than hiding it. A staged new leaf may replace a symlink instead of following it; positive security direction but a behavioral difference.
- Same-UID writer can substitute a named temporary before `os.replace` (#528). This candidate does **not** solve authenticated physical inode publication under hostile directory concurrency; it must remain DRAFT and cannot supersede J24F11/J24P03 security law.
- No stable final pathname guarantee after replacement (J24P04); no fsync/crash-durability or global archive rollback guarantee.
- No product promotion until end-to-end wall/CPU/RSS/temp-I/O, mode/xattr/hardlink/symlink, three-host correctness, hostile publication and official parity are closed.

## Decision

If the frozen fault gate passes: classify **DIRECT_NORMAL_IO_FAILURE_ATOMICITY_CANDIDATE_WITH_NAMESPACE_AND_SEMANTIC_DEBT**, not merged/published product. If it fails: report specific measured failure and retire or narrow this transport mechanism. Preserve all negatives. No modifications to frozen tests, canonical comparators, `STATE.json`, benchmarks, release format/version or other owner branches.
