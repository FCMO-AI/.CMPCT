# v0.30 Analytics reusable-Zstd-context mission lock

Status: **research-only Mission Lock / Referee prerequisite**. No format, selector, release, comparator, locality, integrity, recovery or ONE/Genesis authority changes.

## Why this test exists

The proof-directed admission line has now established a much tighter bound than “find a better threshold.” On the frozen Analytics L15/L19 physical pack partition, L15 stores 6,569,053 B and the accepted v0.29 floor is 6,135,172 B, so at least 433,881 B must be recovered. The positive L15->L19 pack opportunity is only 434,221 B total. Even under an optimistic zero-metadata-penalty oracle, the 45 largest paying packs are required to reach the v0.29 floor; they recover 434,113 B and leave only 232 B of optimistic slack. The only three paying packs that can be skipped together recover merely 108 B. The next omitted paying pack would cost 5,274 B.

Therefore a classifier cannot turn the current representation into a “few expensive packs” problem while preserving the accepted floor. Admission remains useful to reject proven non-payers, but it cannot remove enough of the current high-effort work. The next causal question is whether the high-effort operation itself is unnecessarily expensive.

The current CMPNX5 research helper `zc()` invokes one-shot `ZSTD_compress` through ctypes for every pack and allocates a fresh source buffer and destination buffer per call. That is correct and deterministic, but it also recreates codec/workspace state and copies/allocates at pack granularity. ONE’s efficiency lessons permit testing reusable state/native bulk work so long as the v0.30 representation and semantics remain unchanged.

## Falsifiable hypothesis

For the exact 45 packs admitted by the frozen `>=256 KiB && L15 ratio <=0.70` rule, a single reusable libzstd `ZSTD_CCtx` plus a reusable destination buffer can produce **byte-identical level-19 frames** to the existing one-shot `ZSTD_compress` path while materially reducing compression work.

The mechanism earns continuation only if all admitted payloads are byte-identical and the reusable path reduces the median compression-only wall time by **at least 20%** across repeated fresh-process measurements. CPU time and peak-RSS movement are measured as companion evidence; any byte mismatch is an immediate semantic failure.

The 20% hurdle is intentionally demanding. The preserved scheduling floor shows that perfect eight-way scheduling of the current 8.454 s selected work would still spend 1.05675 s on repack against only about 0.835 s available after measured fixed work. A small micro-optimization does not solve the mission.

## Referee contract

1. Rebuild the same frozen Analytics normalized source and L15 canonical-filesystem research artifact.
2. Recover raw physical packs from the authenticated archive itself, not source paths.
3. Apply the already-frozen path-blind admission rule. No new threshold or feature search.
4. Require exactly the same admitted raw-pack identities across repetitions.
5. Compare the current `V25.zc(raw, 19)` one-shot path against a reusable `ZSTD_CCtx` using the same loaded libzstd and level 19.
6. Compare compressed bytes, not merely sizes. Any mismatch fails the mechanism.
7. Run each engine in fresh child processes and report wall, CPU, import/input RSS baseline, compression peak RSS and exact pack count/input bytes.
8. Time context creation and destination-buffer allocation as part of the reusable engine; pack-fixture loading is outside both compression timers.
9. Do not grant archive-size, locality, reader or release credit from this microbenchmark. Those properties are unchanged by hypothesis and require an actual writer Builder if the referee passes.
10. Green CI means the receipt is valid, not that the hypothesis won.

## Disproof / next decision

- **PASS:** all compressed bytes identical and reusable median wall <=0.80x one-shot. Build the reusable-context path into the exact selective writer and remeasure complete verified creation, RSS and same-runner ZIP.
- **FAIL:** byte mismatch, >=0.80x wall, unstable raw-pack population or resource regression that erases the gain. Retire context/buffer reuse as the main Analytics speed fix and escalate to a genuinely cheaper high-effort algorithm/native bulk implementation rather than another admission-threshold sweep.

`research/cmpct1` and the frozen ONE Genesis result remain untouched. This mission transfers only the general lesson “reuse state / remove redundant work.”
