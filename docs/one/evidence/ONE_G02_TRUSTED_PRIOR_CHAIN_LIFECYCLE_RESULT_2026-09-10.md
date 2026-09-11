# ONE-G0.2 trusted-prior chain lifecycle — exact hosted result

Date: 2026-09-10  
Experimental version: **ONE-G0.2**  
Decision: **HOLD_TRUSTED_PRIOR_CHAIN_LIFECYCLE**

## Exact authority

- branch: `research/cmpct1`
- exact source: `6595a8952b312944ebb827404fde5ccb88c54783`
- workflow: `CMPCT1 ONE-G0.2 trusted prior chain lifecycle`
- run: `34433474331`
- job: `102733653000`
- artifact: `10135433551`
- artifact digest: `sha256:c4612318e69a529e98fd7db95185e5daae4b5e04454e444543b98bccc4ad473c`
- frozen decision size: `1 MiB`
- transitions: `2, 4, 8`
- repetitions: `9` complete lifecycle measurements per family/length, alternating arm order
- inherited exact-source semantic suite: **12 passed**

The falsifier emitted its retained JSON and exited non-zero because the frozen economic promotion gate did not fully pass. This is a scientific HOLD, not an infrastructure failure.

## Mission lock

The candidate lifecycle pays one SHA-256 over generation zero to establish trusted prior identity, then computes only the current-root digest for each transition and promotes that verified digest as the next immutable prior identity. The control hashes both previous and current bytes on every transition.

The hypothesis was that the strong warm-call saving previously observed for trusted-prior reuse would remain large enough after initial trust establishment was honestly charged across a multi-generation chain.

## Semantic / integrity result

All semantic gates pass across every family and chain length:

- exact canonical wire is identical between candidate and control;
- relation admission/rejection decisions are identical;
- every transition reconstructs exactly;
- each reused prior digest equals an independently recomputed SHA-256 oracle for that generation;
- no arbitrary caller hash or unproven mutable state is accepted by the experiment.

Thus the mechanism is valid. Only its promoted lifecycle economics were falsified.

## Measured economics

At the decisive **8-transition** chain:

| family | candidate / rehash-both CPU | candidate / rehash-both wall | frozen CPU gate |
|---|---:|---:|---:|
| shift_plus1 | **0.904422x** | **0.904392x** | <=0.90x |
| fragmented_every96 | **0.999554x** | **0.999564x** | <=1.00x |
| independent_random | **0.905787x** | **0.905787x** | <=0.85x |

Every 8-transition wall row remains below the frozen `1.02x` ceiling. `fragmented_every96` meets its CPU gate. Clean shift misses its deliberately strict promotion threshold narrowly; the random rejection family misses materially.

The chain-length trajectory is also informative:

- `shift_plus1`: **0.9449x** at 2 transitions -> **0.9172x** at 4 -> **0.9044x** at 8;
- `fragmented_every96`: **0.9992x** -> **0.9997x** -> **0.9996x**;
- `independent_random`: **0.9463x** -> **0.9051x** -> **0.9058x**.

The candidate therefore genuinely saves redundant hashing, and the clean relation case improves as the one-time initial trust cost is amortized. But the system-level benefit is not as large as the prior warm-call result implied.

## Causal interpretation

The previous single-transition evidence remains correct for a caller that already possesses an authenticated immutable prior digest: removing a full previous-root SHA can materially reduce a cheap rejected path and moderately reduce productive paths.

This experiment answers a different lifecycle question. Once initial trust establishment is charged, only `N-1` previous-root hashes are actually removed over `N` transitions, while relation admission, segmentation, Program construction, current-root hashing, validation and emission remain. For expensive fragmented relations, hashing is negligible beside segmentation/reconstruction-program work. For cheap rejection, the total writer path still contains enough fixed work that removing prior hashing alone does not reach the preregistered 15% lifecycle saving.

Therefore do not advertise or account the earlier ~0.64-0.66x warm rejection ratios as cold multi-generation ingest economics.

## Hostile review

Do not relax the gates after observing this result. In particular, a `0.904x` clean-shift ratio is scientifically useful but is not `<=0.90x`, and `0.906x` random rejection is not close to the frozen `<=0.85x` target.

Do not remove the trusted-prior optimization from warm persistent operation either: its semantics are exact and its saved hashing is real. The correct accounting distinction is:

- **cold/trust-establishment lifecycle:** this result = HOLD for a broad promotion claim;
- **already-authenticated warm incremental transition:** the prior trusted-root ADVANCE remains valid within its stated boundary.

No reader-visible representation, opcode, integrity rule, recovery rule or format semantic changes here.

## Next decisive action

Carry the distinction into the Genesis measurement contract: report cold establishment and warm incremental ingest separately whenever prior authenticated state is legitimately part of the workload. Do not spend the remaining pre-gate window tuning hashing; profiling shows that fragmented productive paths are dominated elsewhere and the absolute system question is breadth/complete gate accounting.
