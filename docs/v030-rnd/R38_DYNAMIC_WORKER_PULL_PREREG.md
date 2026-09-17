# R38 — persistent dynamic worker-pull candidate encoding preregistration

Status: **FROZEN BEFORE RESULT**. Research evidence only; no product/release credit.

## Parent evidence

R36 localized transferable excess `threading.Condition.wait` time to `src/cmpct/builder.py:build` at the per-candidate `ThreadPoolExecutor.map` materialization boundary. R37 then decisively falsified equal-count contiguous batching: it reduced scheduler overhead on `nested-only` but regressed `full-backups`, with exact encoded identity, showing that scheduler granularity and dynamic load balance are coupled.

## Hypothesis

Archive determinism requires canonical result order, not one Future per candidate. A pool with exactly W long-lived worker futures can preserve dynamic load balancing if each worker repeatedly claims the next canonical candidate index from a shared counter and writes the encoded row into a preallocated canonical-index result vector. This should retain the natural tail balancing of itemwise scheduling while reducing Future/Condition ownership from O(N) candidate tasks to O(W) worker tasks.

## Frozen arms

1. `itemwise`: inherited one-candidate-per-`Executor.map` item behavior.
2. `dynamic-pull`: exactly W long-lived worker futures; each worker claims one next index under a short lock, performs `_encode_candidate` outside the lock, and writes only its claimed slot in a preallocated result vector.

Both arms share one prepared `Builder` state. R38 changes no codec, candidate admission, Deflate ownership, candidate order, worker count, archive format, or product Builder code.

## Targets and repetitions

Use the same deterministic `full-backups` and `nested-only` source families built by the R34/R36 substrate. Use 8 workers and 9 measured repetitions per arm after one warm identity pass. Alternate arm order each repetition.

## Mandatory identity

Every encoded tuple `(content_hash, codec, compressed_payload, metadata)` must be exactly equal between arms and across repetitions. Any identity drift kills this implementation class in its present form regardless of timing.

## Decision law

- `DYNAMIC_PULL_TRANSFERS`: median dynamic-pull encode time is strictly lower than itemwise on **both** targets, exact tuple identity holds, and neither target has a median saving below 2 ms (to reject practically empty wins at this scale).
- `DYNAMIC_PULL_DOES_NOT_TRANSFER`: identity holds but either target is non-improving or saves <2 ms median.
- Any identity failure is an implementation/substrate failure, not a timing result.

A positive result authorizes only a minimal product Builder implementation followed by uninstrumented full-build/archive-byte and whole-system measurement. It does not itself earn runtime or release credit.

## Strong alternative explanation / risk

The shared claim lock may merely replace `Future`/`Condition` overhead with lock contention, and Python thread/GIL behavior may make the O(W) Future reduction too small to matter. Conversely, if `_encode_candidate` spends most expensive work in native codecs that release the GIL, the claim lock should be short relative to useful work. The experiment decides this without queue-size, worker-count, or chunk-size tuning.

## Family exit

If R38 fails transfer with exact identity, retire scheduler-granularity surgery as the immediate efficiency route. Do not sweep queue implementations, claim batch sizes, or worker counts. Escalate to the next higher-level measured owner in create/extract architecture.

## Product promotion boundary

Any later Builder change must preserve complete archive bytes against the inherited candidate and prove uninstrumented end-to-end improvement without exporting unacceptable CPU, RSS, I/O, extraction, locality, recovery, portability, or determinism cost.