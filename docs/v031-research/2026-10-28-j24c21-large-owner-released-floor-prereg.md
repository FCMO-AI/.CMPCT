# J24C21 — large physical owners × published Reader floor (preregistration)

**Frozen before implementation/results: 2026-10-28 UTC.** This is an independent, source-locked *scientific* child of J24C17 #676 at `3b6a73f9205f40f11124cd9ff332407e52cebb93`. No product, release, on-disk revision, benchmark, comparator, threshold, or Discovery state change. The parent is not promotable without stronger evidence.

## One question

Does the observed fused ABI3 checkpoint Qmany acceleration actually survive full physical owner sizes, nonrepeated owners, byte transport and authenticated r24 decoding, while its sealed-reference fix preserves the speedup and does not impose a prohibitive early-Q1 cost relative to **actual published v0.30.0**, rather than only the original #662 experiment?

## Authority / baseline / controls

- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` (Reader v0.30.0/r24), the genuine installed floor.
- Unsafe but fast fused checkpoints #662 at `a66fd593a83cc4c71556d3d86d835c51abd20a96`, as **research-only causal comparator**. Its J24C16 exposed-list mutation wrong-byte failure remains disqualifying.
- Sealed #676 at `3b6a73f9205f40f11124cd9ff332407e52cebb93`, the integrity-improved candidate; its J24C17 +13–24% cost relative to #662 remains a valid negative.
- Other owners/claims: #255/#270/#573 sparse, #681/#684/#686 malformed MessagePack, #683/#685 cross-owner encoding, #574 Discovery. Touch none.

## Why this matters / hypothesis

J24C14–J24C15 measured 4.94–49.11x Q6/Q64 against the published Reader, primarily on tiny repeated physical blob owners. Those results cannot by themselves distinguish Python descriptor traversal dominance from real decode/data movement. A 4 KiB physical owner, a 16 MiB distinct-owner collection, and a 1 GiB logical repeated-owner member offer qualitatively different costs and bound usefulness of this mechanism.

**Prediction:** with 262,144 references to 4 KiB physical chunks, Q6 late/selective sessions will retain a material advantage over published because the baseline rescans hundreds of thousands of references per query. A distinct-owner regime with 4,096 independently authenticated owners will show whether decode/cache/transfer suppresses the gain; early Q1 may still lose because of up-front exact native admission and tuple conversion. The retained #662 control will isolate the cost of sealing. Predictions are prospective, not results.

**Strongest simpler control:** published Reader unchanged. **Alternative explanation:** prior gain depends on extremely small/reused blobs, very cheap `_blob` and Python hot-loop costs; realistic decode shifts the bottleneck to physical work and invalidates observed Qmany advantage.

## Fixed experimental method (before running)

A single deterministic, Builder-independent revision-24 fixture generator creates signed MessagePack primary+checkpoint records and independently framed RAW blob owners. A *single* physical fixture tree is consumed by all three separately wheel-built, installed Readers. No per-arm regeneration. Complete archive bytes, index identity, exact logical size, per-range expected-byte SHA-256 and each source commit SHA are recorded.

Profiles:
1. `tiny_repeat_65k`: 65,536 refs, alternating 1-byte RAW owners (positive reproduction control).
2. `large_repeat_262k`: 262,144 refs, alternating two independently signed 4 KiB RAW owners; 1 GiB logical, only 8 KiB physical owners. Crucially, the full logical digest is computed by streaming, not by allocating 1 GiB.
3. `large_distinct_8k`: 8,192 refs over 4,096 distinct deterministic 4 KiB RAW owners (32 MiB logical / 16 MiB physical), with authenticated distinct physical blob headers.

For each profile measure three genuine session shapes: `Q1_early`, `Q6_spread`, `Q32_spread`; fixed deterministic range offsets, identical for all arms, 4,096–16,384 requested bytes per read when the file permits. At least four fresh independent processes per arm/profile/shape, balanced order across arms. Separately report process startup, Reader open, selective reads, complete in-process session wall and CPU, and peak RSS where available. Preserve every raw observation and actual output bytes' digest. Do not claim zero memory from missing telemetry. Include stored archive bytes, logical bytes, physical owner count/bytes, and calls/returned bytes.

Preregistered **research disproof** (not a new release gate):
- Wrong exact answer, accepted corrupted physical block, changed archive identity between arms or source identity mismatch invalidates the court and blocks any gain.
- For `large_repeat_262k` Q6, sealed #676 must beat published by both >=5% **and** >=3.0 ms in median session CPU and wall to retain *material Qmany* research credit. Q32 is separate evidence, not a substitute.
- If Q1 early suffers both >=5% and >=3.0ms versus published on either large-owner profile, mark the early-Q1 veto explicitly. Do not average with Qmany.
- Any RSS increase >8 MiB versus published is recorded as debt; unavailable RSS is inconclusive, not zero.
- `large_distinct_8k` is an honest stress/transfer profile; even a smaller or negative win must be preserved verbatim. No result can authorize promotion absent release/full matrix/hostile portability tests.

## Cheap first rung and controls

First static-check fixture identity, signed index logical hash, physical RAW BHDR CRC/SHA, deterministic expected range slices, and Byte-exact answers through one local Reader. Reject an invalid fixture; only then purchase three-arm fresh-process cost. The original published Reader *is* the simple control; no redefinition of its work, no hand-corrected historical measurements, no changes to its source or security semantics.

## Threat model / limits

All arms consume immutable, legitimately signed r24 archives. This measures normal read economics, **not** equivalence of hostile on-disk admission protections: released v0.30.0 validates less than guarded candidates. J24C16 stale mutable cached prefixes remain a separate correctness veto on #662 even if it wins wall time. No byte economy or general codec advantage is inferred from RAW-only fixtures. The large repeated profile is not a nonrepetitive disk workload; the distinct-owner control is required. Untraced peak RSS may be coarse; file cache/process startup must be reported separately.

## Handoff / no false promotion

Preserve original artifact, source pins, checksums, raw repetitions, adverse outcomes, owner size, query regime and proposed next action in a result note/PR. No state change unless evidence changes a decision. Any CI failure due to tooling is infrastructure only, not a product loss; never edit the candidate or comparison threshold to rescue a result.
