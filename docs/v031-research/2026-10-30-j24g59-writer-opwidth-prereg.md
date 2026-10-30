# J24G59 — Writer-reachable multi-operation width versus J24G58 indexed replay

**Status:** prospectively registered independent applicability falsifier, not product/release claim. Source is the exact J24G58 research head `cd75aca5df40ff5dd2dbdab67b7770604bc8404f`, which inherits candidate code from `9582a4f0639427440c5f8542871793487123a338` and is stacked on J24G57 #795 `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`. Do not edit the J24G58 owner branch or frozen parent oracle.

## Primary question and prediction (before test)

Does the public revision-24 Writer actually emit `len(delta['ops']) >= 16`, required by the J24G58 fast path? Current source inspection of `transactions.append_update`, `append_delete`, `append_rename` shows each writes exactly ONE operation per committed delta, or emits a complete checkpoint at depth 64. If no reachable API writes multi-operation deltas, the 33×/4k-op helper win in J24G58 is **mechanism-level** headroom but **not yet a reachable speedup** for ordinary Writer-created signed archives.

The discriminating observable is each physical committed footer's generation kind and decoded `ops` count across fresh Builder archive, replacement, insertion, deletion, rename and the 64-delta checkpoint boundary. Bind the result to source and archive SHA-256. Separately count whether `_try_indexed_row_mutations` is called and whether it returns True on an ordinary Reader open of those authentic archives. A source-level claim alone is insufficient. The checker itself must not silently count a complete checkpoint as a multi-operation delta.

## Alternative explanations and counter-controls

1. Other product entrypoints may emit batches; audit the writer call graph and report known surface boundaries. A test of only one API is not a complete product census.
2. The same helper is used for arbitrary externally produced r24 deltas; a manually authenticated 16-op delta may legitimately take the indexed route. Preserve it as a **positive capability control**, never relabel it an ordinary Writer output.
3. A depth-64 checkpoint may change open-time cost despite containing zero delta operations. Count the kind=0 checkpoint separately; do not count the previous 63 single-op deltas as a simultaneous 63-op batch.
4. Reader and preflight may use distinct admission paths. Explicitly check what the real Reader invokes and inspect actual footers by an independent decoder, not only a patched in-memory `ops` list.

## Predeclared decision

- **`ORDINARY_WRITER_FAST_PATH_NOT_REACHED`** when all supported tested public mutation entrypoints emit one op/delta or checkpoint and no Reader replay calls with >=16 operations on those archives.
- **`REAL_WRITER_FAST_PATH_REACHED`** only with a genuine current public API artifact with a multi-op committed delta and verified indexed route.
- **`INCONCLUSIVE`** if artifact audit/source custody/platform support fails.
- If first outcome, do not discard J24G58 correctness or helper measurements; narrow its product economics to third-party/batch-produced archives and prioritize measuring ordinary single-op replay/full Reader cold open instead of further optimizing the 16-op-only path. Do not tune threshold to win this court; new production batched Write API would be a separate design with its own crash/durability/resource semantics.

## Evidence/limits

Use installed source-exact CMPCT on GitHub-hosted Ubuntu; deterministic synthetic generic files, native r24 Builder and Writer, raw footer decoding with independent Zstd+MessagePack and recorded checksums, source hash and archived receipt. This is a reachability/ownership experiment, not full CPU/RSS/ZIP benchmark. No product/format/version/frozen gate edits. Any Writer error must remain a failure and not be swapped for a hand-written archive.

## Concurrency and discovery

Existing #797 owns indexed replay implementation; #795 owns parent journal grammar; #789 owns Reader/preflight semantics; #574 owns Discovery STATE. This branch modifies only a new test, research note and dedicated workflow, not their code or shared state. If owner #797 independently measures this reachability question before CI, reconcile evidence and avoid duplicate implementation. Stronger hosted evidence wins.
