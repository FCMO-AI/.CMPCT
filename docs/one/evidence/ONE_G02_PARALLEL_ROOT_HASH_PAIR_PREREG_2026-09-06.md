# ONE-G0.2 parallel root-hash pair — preregistration

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Mission Lock

Exact simple-relation phase attribution at source `3d801313803aa8c890a09cd6dd440a9d4e95da43` identifies root SHA-256 + digest preparation as the largest stable charged owner: median **57.39%** of the ref-fused full candidate on mature `shift_plus1`, with >=15% share on 5/5 rows. Native segmentation is second at 28.88%; admission/proof and final writer/output are only 3.69% and 6.27% medians respectively.

Root integrity is mandatory. This experiment may not move hashing outside the charged writer boundary, replace SHA-256, cache a hash not already available by semantics, or weaken root verification.

## Falsifiable hypothesis

`previous` and `current` root hashes are mathematically independent. Computing their exact SHA-256 digests concurrently through one bounded reusable native worker will materially reduce elapsed root-identity preparation without changing a single root byte.

The worker is an encoder-side compute executor, not reader-visible state. It uses one persistent helper thread with a deliberately bounded 64 KiB stack. Worker creation is measured separately as cold-start cost; the steady-state gate applies only after one explicit warmup because the Speed/Efficiency Law explicitly permits reusable creator-side execution resources, but the cold result and state cost must remain visible.

No workload-, size-, content-, segment-count- or benchmark-result dispatcher is allowed. The same hash-pair function is used for every row.

## Frozen baseline

Exact current shared-native preparation:

1. `sha256(source).hexdigest()`;
2. `sha256(target).hexdigest()`;
3. convert both 64-hex identities back to raw 32-byte digests for the native writer ABI.

This is the exact work presently charged by `_candidate_once_native`.

## Candidate

One native call accepts immutable source/target pointers, computes standard SHA-256 for source on the calling thread and target on a persistent helper thread, joins through a condition variable, and returns two raw 32-byte digests. The implementation links system OpenSSL/libcrypto; it does not implement a weaker hash or change canonical bytes.

## Matrix

Sizes: 4, 8, 16, 32, 64, 128, 256 KiB.

Content families for semantic diversity (speed is expected to be content-insensitive): independent deterministic random, repeated byte/pattern, `shift_plus1` source/target, and already-compressed-like deterministic bytes where available from the existing relation matrix.

At minimum the existing `shift_plus1` source/target and `independent_random` pair are required at every size.

## Timing / state discipline

- exact digest equality is checked before timing every row;
- record one cold candidate call including worker creation;
- then one untimed warmup;
- 63 paired steady-state rounds, alternating baseline/candidate order A/B-B/A;
- GC disabled during timed pairs;
- report median ns, candidate/baseline ratio and ns/input-byte over `len(source)+len(target)`;
- report helper stack target = 65,536 B plus fixed synchronization/context state;
- no input/output copies may be hidden outside the candidate call except the same already-materialized immutable input buffers both arms receive.

## Frozen gate

Semantic:

- exact previous digest = baseline SHA-256 on every row;
- exact current digest = baseline SHA-256 on every row;
- deterministic repeated calls;
- worker startup/shutdown/error path must not silently return partial hashes.

Steady-state performance:

- mature sizes >=16 KiB: median candidate/baseline across all rows <= **0.75x**;
- every mature row <= **0.90x**;
- no tested row > **1.10x**;
- 128/256 KiB median <= **0.65x**.

Cold/resource guard:

- record cold ratio; no cold promotion threshold is imposed at this research stage, but if cold setup exceeds 1 ms or worker stack cannot be bounded to <=64 KiB, the design is **not** eligible for immediate writer integration even if warm speed passes;
- exactly one helper thread; no unbounded queue or per-call heap growth.

## Disproof / retirement

If warm concurrency fails the gate, preserve the negative and attack native segmentation next. Do not add a size threshold that serializes small files and parallelizes large ones to rescue this result. If it passes speed but violates the bounded worker resource guard, keep it as a future shared-executor idea rather than integrating it now.

## Claim boundary

This falsifier promotes at most an encoder-side exact root-hash preparation strategy for subsequent full-writer A/B. It grants no writer, stored-byte, reader, product, comparator or Genesis-gate authority.