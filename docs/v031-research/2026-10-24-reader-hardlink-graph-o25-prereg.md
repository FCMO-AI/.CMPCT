# O25 preregistration — ordinary Reader hardlink owner graph

**Date:** 2026-10-24 UTC. **Status:** prospectively preregistered, result unknown. **Base:** PR #365 exact `54c998200b1908b696ade049fe94df71a736c284`; released v0.30.0 / on-disk revision 24 unchanged. Branch O25 owns only the ordinary Reader hardlink name-resolution safety/performance seam, not signed-generation decoding/resource ceilings, native ABI, extraction destination safety or strong source-lifetime research.

## Baseline and question

Strict `preflight_archive` validates hardlink cycles and terminal regular owners using a memoized graph traversal. Ordinary `CMPCT(path)` constructs `self.by` but does not visibly run that hardlink graph court. `read()`, `read_range()` and `read_raw_range_verified()` recursively follow `row[6][0]`. This is a source hypothesis, **not yet a demonstrated product failure**.

Does an authentic revision-24 container with a SHA-committed index containing a cyclic or long-but-acyclic hardlink graph make the ordinary Reader recurse unboundedly or reject a strictly valid deep graph due to Python stack depth, despite the strict preflight contract?

## Prediction and falsification

1. A self-referential hardlink and a two-node cycle pass baseline `CMPCT(...)` construction but cause `RecursionError` on ordinary `read()`, `read_range()` and/or `read_raw_range_verified()`. Strict `preflight_archive` must reject cycles. If ordinary Reader already rejects before operation, the defect hypothesis is **falsified**.
2. A SHA-committed acyclic chain of >1,200 aliases terminating at one regular RAW owner passes strict preflight, but baseline ordinary Reader may exhaust the Python recursion limit. A corrected Reader must return byte-exact full/range/strong-range content without linear recursion per query, and must continue to reject cyclic and missing/wrong-kind owners.
3. A fixed direct regular + direct hardlink control must retain exact read/range outputs and ordinary checkpoint-open behavior. Full archive size/content must remain identical between control and candidate; only Reader source may change.
4. A corrected implementation should use memoized terminal-owner validation once at Reader construction, with O(number of aliases + dependency edges) work and no archive-controlled recursive call chains. It must not invoke an unbounded extra preflight on every open, change format/release law or weaken any existing validator gate.

## Alternatives and kill/narrow conditions

- **Always call full preflight on Reader open:** stronger generic guard but adds unrelated blob/index work and may regress hot cold opens; defer unless focused owner validation proves insufficient.
- **Catch RecursionError:** masks the trigger, does not bound graph traversal or preserve deep valid chains; reject.
- **Restrict aliases to one direct regular owner:** simpler but potentially rejects historical archives accepted by strict preflight; prefer semantic parity with currently enforced validator unless format authority proves otherwise.
- **Iterative per-read resolution:** bounds stack but rescans deep chains per read; memoize the graph once instead.
- If baseline refuses malformed graph already, terminate without Reader change. If deep valid chains are rejected by strict preflight, do not claim a product compatibility win. If new constructor overhead on checkpoints is material relative to existing Reader economics, retain the negative and reconsider lazy/conditional owner checks.

## Honest evidence scope

The fixture should use `cmpct.codec` revision-24 HEADER/BLOB/FOOTER constants, `msgpack` and native `zc` to create SHA-committed real archive bytes, not only mocked `self.by`. SHA-256 here is **unkeyed integrity**, not proof of archive origin. A focused negative court on the unmodified base must precede implementation credit. Re-run unchanged cases after fixing, followed by real Reader checks and full CI as far as available. Observe cold-open overhead and relevant RSS on hardlink-heavy and no-hardlink controls before any promotion claim.

**Concurrency:** #365 owns signed-generation resource limits and O25 is an independent adjacent hardlink resolution lane. #342 owns strict preflight hardlink graph memoization; reuse its semantics, do not overwrite its implementation. #377 owns source-lifetime snapshot research and is unrelated. This branch is intentionally stacked on exact #365 and is NOT a release or merge authority.
