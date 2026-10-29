# J24I14 — exact-donor sparse verification transfer into genuine compaction (prospective contract)

Date: 2026-10-29 UTC. **Research-only independent composition. Not a product fix, benchmark pass or release permission.**

## Authority, original source and ownership
- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, r24), unchanged.
- Active private compaction implementation owner [#723](https://github.com/FCMO-AI/.CMPCT/pull/723) at `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`.
- Source-exact memory attribution [#731](https://github.com/FCMO-AI/.CMPCT/pull/731) at `7544b25bf455ff02c8a168b441afcf2edfe008a2` is the **stacked research parent**. Do not edit its original tests or the three source files.
- Previously hosted streamed sparse verifier donor [#613](https://github.com/FCMO-AI/.CMPCT/pull/613), immutable commit `3b2bf3c2e033fa27d77b2355821dc0087aa46873`, `src/cmpct/reader.py` Git blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710`. Reuse precisely its existing `_blob`, `_verify_sparse_streamed`, and `verify` implementations as isolated research-time method transplants. Do not reimplement a competing streaming verifier.
- Separate security veto [#726](https://github.com/FCMO-AI/.CMPCT/pull/726): stage-path rebind. Remains a veto regardless of memory improvement. Sparse hardlink aliases require [#620](https://github.com/FCMO-AI/.CMPCT/pull/620) and are deliberately outside this question.
- Shared `docs/discovery/STATE.json` is staleable and owned by #574. No write to it; no concurrent owner file write.

## Primary causal question
Will the **exact existing** #613 Reader method donor, applied only in a fresh-process research experiment to unmodified #723 compaction, remove the O(logical sparse bytes) peak RSS discovered by #731 while **preserving identical physical archive bytes and strict logical semantics**, compared with the same installed #723 source/fixture without the donor?

Prediction: for 128 MiB S_SPARSE input with two 4 KiB extents, donor B uses less than 128 MiB peak RSS and at least 128 MiB less than original A in 2 of 2 predeclared A/B pairs, with identical resulting archive SHA-256, index metadata and source preservation. Original A should still exceed 128 MiB. If any condition fails, classify ambiguous or falsified without changing thresholds. These cutoffs are *scientific discriminators*, not release gates.

## Control, attribution and cheapest evidence
- Use #731 genuine Builder-generated r24 file and append an actual journal update, with 2 MiB negative-size control and 128 MiB decision case. Save original input once; run **A/B/B/A** in four fresh Python child processes on **exactly that input**, same installed wheel, same filesystem and runner.
- A: unmodified #723 `CMPCT.verify` and `_blob`.
- B: AST-copy **exact method source** from immutable #613 Git blob in the checkout, compile the three Python methods into the installed `cmpct.reader` module globals, assign them to its class. No source file edits and no change to `read`, `file_sha256`, Builder or transactions. Identity of installed source, donor SHA, and exact AST method node hashes are retained.
- Each child records wall, process CPU, Linux `ru_maxrss`, physical I/O counters, input/output complete SHA/bytes, source row/index metadata (including hardlinks when present), independent read-range head/tail checks, and exact source preservation. Capture raw stdout/stderr and artifacts.
- Verify the resulting **A/B archive byte equality**, not merely `read()` identity. Preserve any nondeterminism as a red or ambiguous result, never erase.
- Damage one physical sparse blob in a copied input and require both A and B to fail before publication, leaving the destination sentinel unchanged. If source corruption prevents parser admission, distinguish that from streamed SHA proof; never claim a proof it did not run.
- Stronger control is the exact A run, not a naive `shutil.copyfile` of the archive (which retains journal history and cannot prove semantic parity).
- Run on Ubuntu 24.04 with Python 3.11, source installed outside checkout and exact SHA bound in CI. No new release benchmark, no multi-host claims.

## Kill, scope, debt and counterfactual
- Fail the transfer if donor legitimate case rejects, archive differs physically, sparse representation is lost, an invalid source reaches publication, source bytes mutate, donor path retains logical-size RSS, or A/B measurement is not same-input/same-source.
- If winning, deliver a **productization pointer** to owners #723/#613/#620, not a second Reader implementation. Stage-name race #726, cross-platform correctness, temp I/O, full CPU/wall regression, all archive storage kinds, hardlink sparse and complete promotion CI remain open.
- If losing, retire this particular three-method transfer and diagnose the measured alternative cost owner before editing code.
- Counterfactual question: Could the exact-reader method composition have identified remaining compaction memory owners with fewer hosted executions than constructing new streaming logic?
- No Discovery policy mutation absent repeated causal process evidence. Do not weaken evaluator, files, thresholds, corpus identity, release or format law.
