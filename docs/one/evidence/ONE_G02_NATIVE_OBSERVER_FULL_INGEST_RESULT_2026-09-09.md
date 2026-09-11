# ONE-G0.2 native observer full-ingest transfer — result

Date: 2026-09-09  
Experimental version: ONE-G0.2  
Decision: **ADVANCE_NATIVE_OBSERVER_FULL_INGEST**

## Exact hosted authority

- branch: `research/cmpct1`
- exact evidence source: `7008d1b45a3bcd6ba5662c5ac29a713c2ee650dc`
- workflow: `CMPCT1 ONE-G0.2 native observer full ingest`
- run: `34431081712`
- job: `102726550400`
- artifact: `10134514550`
- artifact digest: `sha256:701a67dbaa8cca510b00a666dcc23ebf22d63203ef28d3586e805f0ff0472319`
- retained JSON: `one_g02_native_observer_full_ingest.json`
- inherited semantic suite: **46 passed**

The first result-bearing attempt at source `cf5b48d8926fd503ec8758099debdc1a92208393` did not reach the scientific falsifier because its workflow referenced obsolete test paths (`tests/one/test_wire.py`, `tests/one/test_vm.py`). Source `7008d1b...` repairs only those inherited-test paths to the existing `test_one_g01_wire.py` / `test_one_g01_vm.py` files. Candidate, benchmark, thresholds, inputs and representation semantics were unchanged before the first admissible measurement.

## Mission lock

Frozen hypothesis: replacing only the current-root Python `observe()` call with the exact native `observe_native()` implementation should preserve the complete charged adjacent-version writer result while transferring the observer's speed advantage through the full measured ingest path.

Both arms still charge current observation, previous/current SHA-256, the same relation admission and native segmentation, generic ONE Program construction, full validation, and direct canonical emission. No cache, changed-cone authority, reader-visible mechanism, special storage mode or weaker verifier is introduced.

Frozen disproof gates included:

- exact Observation and semantic parity;
- identical canonical wire, Law/Surprise choice, relation-selection outcome and reconstruction result;
- median candidate/baseline total CPU <= **0.15x**;
- median candidate/baseline wall <= **0.15x**;
- every row CPU and wall <= **0.35x**;
- no stored-byte or modeled reader-work regression;
- no new persistent state.

## Hosted result

All frozen gates passed.

- median candidate / baseline total CPU: **0.0318218622x**;
- median candidate / baseline wall: **0.0318135514x**;
- median timing gate: **PASS**;
- every-row timing gate: **PASS**;
- semantic gates: **PASS**;
- repetitions per row: **15**, paired alternating A/B-B/A.

The measured full-ingest path is therefore about **31.4x faster at the median** after substituting native fresh observation, despite continuing to charge hashes, admission, Program construction, validation and canonical emission.

At the 1 MiB current-root scale:

| case | baseline total CPU | candidate total CPU | ratio | canonical wire | relation |
| --- | ---: | ---: | ---: | ---: | --- |
| exact repeat | 257.075 ms | 8.181 ms | **0.03182x** | 2,097,273 B | no |
| one-block edit | 257.786 ms | 7.591 ms | **0.02945x** | 2,097,273 B | no |
| eight-block edit | 258.786 ms | 7.664 ms | **0.02961x** | 2,097,273 B | no |
| shift +1 | 259.681 ms | 8.260 ms | **0.03181x** | 1,048,710 B | yes |
| independent random | 260.287 ms | 7.544 ms | **0.02898x** | 2,097,273 B | no |

For the 1 MiB rows, native observation itself is roughly 5.95–6.02 ms. The remaining charged work is mostly root hashing plus writer stages; observation still accounts for roughly 73–79% of candidate CPU, so this promotion does not imply the full writer is finished or that future observer improvements are irrelevant.

The candidate keeps the same one-pass observation traffic recorded by the benchmark: one current-root source read, zero verification reread, and the same retained observation-index payload as the baseline. Wire and modeled reader work are unchanged row-for-row because only the execution backend for producing the same Observation changed.

## Interpretation

This closes the transfer question left open by the standalone native-fresh-observer result. The ~27x standalone observer gain was not a misleading microbenchmark: after charging the surrounding writer pipeline, the full measured adjacent-version ingest path becomes about 31x faster than the Python-observer baseline on this frozen matrix.

The result also strengthens the earlier decision to demote the persistent positional cache as the default optimization target. A competent fresh native observer is both simpler and materially faster than carrying a large persistent cache for the tested workload classes; any future incremental observer must beat this native fresh baseline under honest changed-cone accounting rather than comparing itself to Python scanning.

## Hostile review / limits

This is **not** the September 11 Genesis gate and does not establish v0.29/v0.30 supersession. Its claim boundary is deliberately narrower: adjacent-version research-writer transfer of exact native fresh observation.

It does not establish authenticated archive placement cost, product-native RSS, complete recovery/portability behavior, full 15-workload breadth, or universal automatic Law discovery. Most non-shift rows in this matrix correctly remain Surprise-only, so the experiment proves fast observation and faithful writer transfer, not broad compression gains on every row.

The strongest remaining efficiency owner is now outside Python observation. At 1 MiB, roughly 1.33 ms is still spent in the two SHA-256 root hashes, while writer work ranges from about 0.30 to 0.90 ms depending on whether relation work is admitted. Further optimization should target common fused ingest/identity/accounting only if it preserves exact integrity semantics; do not remove required hashes merely to improve a benchmark.

## Comparator / campaign status

Frozen Genesis comparators remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No ordinary v0.30 mechanism development was resumed and no Genesis gate result is claimed here.

## Next decisive action

Prioritize Genesis gate readiness and breadth rather than further isolated observer tuning. The pre-September-11 readiness lane must certify the exact 15-workload substrate and frozen comparator identities without encoding/scoring the candidates. Any remaining readiness failure should be diagnosed and repaired as infrastructure or deterministic-corpus debt without changing expected evidence after observation.

Once readiness is closed, the next research value lies in broad ONE Law discovery/admission that can exploit more of the canonical workload matrix while preserving the native observer economics, authenticated selective access, integrity/recovery/resource invariants and fail-closed reader simplicity already demonstrated elsewhere in G0.2.
