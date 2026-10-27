# J24D01 — Direct-member output-write failure, result and scope

**Result 2026-10-27 UTC:** `DIRECT_MEMBER_OUTPUT_FAILURE_DESTROYS_EXISTING_TARGET` on two authentic hosted POSIX systems. This is **released-product negative evidence**, not a product repair. [PR #581](https://github.com/FCMO-AI/.CMPCT/pull/581), [Issue #582](https://github.com/FCMO-AI/.CMPCT/issues/582).

## Evidence identity and comparison

- Preregistration before instrument: `42b7d39dc841452cd7c2247780b2cfb7ef110988`.
- Released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, `reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Exact tested research HEAD: `6b8e8a995616db1511993caaaa3db3db2726c0c3`; no `src/` or frozen `tests/conformance/` file changed.
- [Original hosted workflow #40472001866](https://github.com/FCMO-AI/.CMPCT/actions/runs/40472001866), Ubuntu 24.04/CPython 3.11 and macOS 14/CPython 3.11 **both SUCCESS**.
- [Ubuntu artifact #12719565538](https://github.com/FCMO-AI/.CMPCT/actions/runs/40472001866/artifacts/12719565538), ZIP SHA-256 `8249ffae68b8359d08012648e5af8f44903d4818f9f8d93b23229be6ff700455`.
- [macOS artifact #12719440985](https://github.com/FCMO-AI/.CMPCT/actions/runs/40472001866/artifacts/12719440985), ZIP SHA-256 `db9d660ecd735944178463f8c774d4a84dd5938e437f58f8eefb718ace6e3d39`.

## Direct physical result

For each of five independent frozen revision-24 members, source archive SHA-256 and extracted logical SHA-256 are validated before the write fault. The output name starts with a nonempty distinctive pre-existing canary. During `extractall()`, the hook executes a **real successful 7-byte kernel `os.write`** and raises `OSError(ENOSPC)` on the second write call.

| Representation | Expected fault behavior | Ubuntu | macOS |
| --- | --- | --- | --- |
| RAW direct S_BLOB | ENOSPC, **previous target destroyed**, surviving inode contains first 7 new bytes | PASS | PASS |
| Zstd direct S_BLOB | Same | PASS | PASS |
| Deflate direct S_BLOB | Same | PASS | PASS |
| Fixed S_CHUNKS | ENOSPC, previous target/inode preserved, no residual stage | PASS | PASS |
| S_CDC | Same | PASS | PASS |
| All five clean, no injected failure | Exact logical SHA-256 reconstruction | 5/5 PASS | 5/5 PASS |

Across hosts: **20/20 experiment cases as preregistered**, 10 exact clean extractions; 6 direct existing-target destructive failures; 4 staged-chunk existing-target-preserving failures. Raw outcomes agree across hosts after removing process/platform inode identity fields.

The hosted independent referee passed **154 checks per host** and rejected **eight deliberately corrupted receipts per host**. The original ZIPs were downloaded and replayed with a *separate offline Python implementation*, independent of the hosted referee. Offline result: **234 checks PASS**, including archived ZIP SHA, inner checksums, original frozen vector identities, canary hashes, seven-byte physical output identity, syscall errno, inode preservation, stage cleanup, and cross-host normalized outcome equality. Offline audit is retained as an independent reproducible attachment of the activation; primary durable scientific truth is the GitHub artifact/source pair.

## Causal explanation

`S_BLOB` extraction authenticates source bytes first, but then executes `os.open(full, O_TRUNC)` on an existing destination and starts irreversible in-place writes. An output-write failure provides **no rollback**. `S_CHUNKS/S_CDC` uses a sibling staging file and preserves the prior destination on this same injected fault. This distinguishes **input authenticity** from **failure-atomic output publication**.

The falsifier confirms a scoped defect, not a forged SHA success. It says nothing about stochastic ENOSPC incidence, archive-wide transactional extraction, hostile post-publication path replacement, Windows portability, all remaining storage kinds, hardlinks/metadata preservation, or benchmark economics. The linked issue #582 owns repair; #572 sparse-SHA destruction and #528 mutable-stage namespace attack remain separate.

## Decision, negatives, and next bounded action

Do not promote the direct path unchanged as failure-atomic. Do not silently replace it with `mkstemp+os.replace` without assessing preexisting inode/hardlink/metadata identity, same-UID directory mutation, trusted namespace scope, full file I/O and RSS, and exact v0.31 composition/CI authority. Next cheapest actionable step for the owner: add a candidate direct-member transactional publication route on a dedicated branch, execute this *unchanged* scientific court as regression proof, run a hardlink/external-link preservation counterexample and complete same-input create/extract/performance comparisons. Separately test S_PACK and S_VZIP direct fallback paths before widening the claim.

No product/format/release/evaluator threshold changes, no `docs/discovery/STATE.json` write (separate active owner #574), no merge and no release. Counterfactual: inspecting the `read() → O_TRUNC → write()` ownership seam and one 7-byte fault before designing more complex publisher changes would have revealed this representation-specific recovery gap cheaply, prospectively and independently.
