# ONE Genesis historical measurement preflight — 2026-09-10

Status: **ADVANCE_HISTORICAL_MEASUREMENT_PLUMBING_ONLY**

Experimental line: **ONE-G0.2**

## Mission lock / hypothesis

Before the Genesis gate, prove that the frozen v0.29 and v0.30 product surfaces can be measured under one raw vocabulary on an executor-owned external synthetic tree, without importing historical corpus generators or touching the frozen 15-workload Genesis matrix.

Falsifier: fail if either frozen checkout differs from the Genesis SHA; if exact reconstruction fails; if a historical corpus generator is newly loaded; if a missing capability is represented as zero; if v0.30 selective locality is inferred when the frozen reader does not directly export it; or if any comparison/scoring/winner selection occurs.

## Durable implementation

- `benchmarks/one/one_genesis_historical_measurement_probe.py`
- `tests/one/test_genesis_historical_measurement_probe.py`
- `.github/workflows/cmpct1-one-genesis-historical-measurement-preflight.yml`

Exact hosted source: `2f5d23829dfb8250ed01fedf3aa3e8516bd38378`.

Frozen contenders:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Hosted evidence

- workflow run: `34472273887`
- job: `102854702140`
- conclusion: **success**
- artifact: `10150106703`
- artifact digest: `sha256:d6ac8e1023cc1a91a76139c024dbd4dc5045654175af4f8c1b58499b21f5effb`
- normalization falsifiers: **4 passed**

The synthetic executor-owned transfer tree was identical for both frozen products:

- files: `3`
- logical bytes: `15,452`
- tree SHA-256: `852ad4ccf259918186b12a096da4f9daf019077d08257c067594ea81353fe58d`

Observed complete stored bytes on this tiny transfer fixture were `979 B` for frozen v0.29 and `1,577 B` for frozen v0.30. These values are diagnostic plumbing evidence only; the fixture is not representative and no relative win is adjudicated.

The hosted run also measured exact whole-tree reconstruction and strong verification for both products. v0.29 selected `v028-fallback`; v0.30 selected `r24-fallback`. Again, those selections describe this synthetic transfer fixture only.

For v0.30, `read_member_with_stats()` reconstructed each requested member exactly and reader latency was measurable, but the frozen `canonical-r24` stats exported `decoded_context_bytes = null` and `decoded_context_amplification = null`, with locality accounting requiring operation-level instrumentation or inherited r24 evidence. Therefore the result is explicitly **`measured-reader-latency-only`**. The preflight does not infer locality from archive size or wall time.

For v0.29 no proven direct selective-member reader exists in the frozen product surface, so selective access remains explicitly **unavailable**, not zero and not an automatic loss.

No Genesis workload was used. No comparison, scoring, or winner selection was executed.

## Hostile review / strongest limitation

The CPU values emitted by this first probe use `time.process_time()` in the driver process. They are useful for verifying that a common measurement shape can be populated on the tiny synthetic fixture, but they are **not yet production-authoritative creation/read CPU** for the Genesis gate because child-process CPU would not be charged if a historical path spawns workers. Peak RSS is intentionally marked unavailable for the same reason.

The production adapter must move creation/read measurements to a fresh process boundary that charges the full reconstruction/build process tree, and it must define peak-memory semantics before the gate. Prefer an explicit unavailable cell over fake precision.

A second unresolved asymmetry is ONE itself: the frozen historical product boundaries are now concrete, but the campaign still needs to certify one equivalent complete ONE archive/product boundary so ONE is not measured through a cherry-picked mechanism benchmark while v0.29/v0.30 are measured as products.

## Decision

**ADVANCE_HISTORICAL_MEASUREMENT_PLUMBING_ONLY.** The experiment validates external-tree ownership, exact historical reconstruction, explicit missing-capability semantics, and a common raw vocabulary. It does **not** validate Genesis scores, relative performance, resource parity, or a winner.

## Next decisive action

1. Certify ONE's complete archive/product boundary for the gate.
2. Add fresh-process CPU/wall/RSS measurement semantics that charge child work rather than driver-only CPU.
3. Falsify those measurement boundaries on synthetic/transfer corpora only.
4. Keep the frozen 15-workload matrix untouched until the first eligible activation on 2026-09-11.
