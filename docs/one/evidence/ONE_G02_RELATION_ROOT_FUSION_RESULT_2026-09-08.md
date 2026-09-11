# ONE-G0.2 relation root fusion — exact result

Date: 2026-09-08
Branch: `research/cmpct1`
Research version: ONE-G0.2

## Verdict

`HOLD_RELATION_ROOT_FUSION`

This is a clean scientific HOLD, not an invalidation. The candidate preserved the exact existing ONE Program and root semantics, and the semantic/adversarial tests passed. It succeeded at the representation-neutral geometry objective—removing redundant intermediate materialization—but failed the frozen performance gates badly enough that this Python/CPython execution boundary must not be promoted.

## Exact evidence authority

- source SHA: `9657c08d31ccd7d1db7e1a65acd4ee99b53ef6bb`
- workflow run: `34302114363`
- job: `102311032163`
- retained artifact: `10085291395`
- downloaded artifact ZIP SHA-256: `e20d1a6819ad4dcfed553bed36889db611e7afbabb31209d13ee7f5ebe3c86ea`
- matrix: exact 24/24 cells (64 KiB, 256 KiB, 1 MiB × 512/1024/2048/4096-byte relation spans × add8/xor)
- semantic and hostile decision-law tests: PASS
- workflow job conclusion: failure only because the frozen falsifier returned HOLD

## Decisive 1 MiB / 4096-byte rows

### add8

- reference work / literal: `2.3333333333333335x`
- reference materialized / literal: `2.5x`
- fused work / literal: `1.5x`
- fused materialized / literal: `1.0x`
- fused peak temporary bytes: `1,052,672` (1 MiB root sink + one 4 KiB translated block)
- fused wall / literal: `4.400154648968268x`
- fused CPU / literal: `4.400825412376177x`
- fused wall / current native prepared reader: `1.2140183028127454x`
- fused CPU / current native prepared reader: `1.2139552402120626x`

### xor

- reference work / literal: `2.3333333333333335x`
- reference materialized / literal: `2.5x`
- fused work / literal: `1.5x`
- fused materialized / literal: `1.0x`
- fused peak temporary bytes: `1,052,672`
- fused wall / literal: `4.406475017216651x`
- fused CPU / literal: `4.407242674557158x`
- fused wall / current native prepared reader: `1.2098364308125888x`
- fused CPU / current native prepared reader: `1.2095415745445584x`

Neither decisive row meets the stronger <=1.05x literal system-ready diagnostic.

## Causal interpretation

The geometry hypothesis is partially and strongly supported. Direct root sinking reduces modeled reader work from 2.333x to exactly 1.50x literal and retained graph materialization from 2.5x to exactly 1.0x without changing the stored Program. Therefore the predecessor's work/materialization penalty is not intrinsic to the Law representation.

The implementation hypothesis is falsified. Per-relation Python dispatch plus `bytes(source).translate(...)` and block copies make this executor about 4.4x literal and about 21% slower than the already-promoted generic native prepared reader. A representation-neutral fusion principle exists, but this is the wrong runtime boundary.

The predecessor density evidence remains valid: coarse 4 KiB add8/xor relation spans can approach ~0.504x literal wire. This result does not upgrade that density evidence into a system-ready reader path.

## Stop condition

Do not rehabilitate this line by relaxing the 1.50x/0.50x frozen gates, moving more work outside timing, dispatching only the favorable relation family, or introducing a reader-visible relation codec/opcode. Do not continue relation-specific reader micro-optimization merely to force the synthetic frontier green.

If root/cone fusion is revisited, it must be part of a general bounded reconstruction compiler/executor serving multiple existing ONE Law shapes. The already-promoted generic prepared control plane plus native bulk data plane remains the stronger reader architecture.

Primary research should return to writer-side automatic Law discovery and exact synthesis efficiency. A high-value next falsifier is budget-aware maximal relation-span growth: after cheap observer nomination, grow exact add8/xor relations to maximal verified spans using exponential extension plus bounded refinement, emit ordinary existing ONE relation nodes with Surprise at cracks/tails, and measure node/control reduction, wire bytes, exact-check work, writer CPU/wall, peak state, and bytes eliminated per extra CPU second versus fixed-window synthesis. This absorbs the useful relation principle into ONE without creating another mechanism family.

## Comparator / Genesis truth

Frozen comparator authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No ordinary v0.30 development resumed. No Genesis supersession point moves from this scoped reader experiment. The September 11 same-input, same-semantics full 15-workload gate remains authoritative.
