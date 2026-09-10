# CMPCT1 / ONE Genesis contender raw-adapter assembly v0.1

Date frozen: 2026-09-10
Branch: `research/cmpct1`
Experimental campaign: ONE-G0.2
Status: preregistered before implementation or Genesis contender execution

## Mission Lock / Referee

Assemble the already-falsified fresh-process product workers into one raw workload-measurement layer without changing contender semantics, generating the Genesis corpus, comparing contenders, or scoring a winner.

The executor owns the physical input tree and source identity. This layer owns only repetition, phase orchestration, raw sample retention, median calculation, and explicit propagation of unsupported/unavailable cells.

## Falsifiable hypothesis

For an arbitrary executor-owned transfer tree, a common orchestrator can run five fresh-process creation repetitions and five fresh-process cold-open whole-read repetitions for CMPCT1, frozen v0.29, and frozen v0.30; it can additionally run five fresh-process selective-member repetitions only where an exact product surface exists. It preserves every individual sample, computes medians without dropping outliers, never manufactures unavailable metrics, and does not execute any comparison or scoring logic.

Disprove the hypothesis if any contender requires a different measurement boundary, if archive bytes are not measured from the actual persistent artifact, if repeated builds are semantically/wire inconsistent where determinism is promised, if exact reconstruction fails, if unsupported v0.29 selective access is synthesized, or if orchestration needs access to Genesis workload generators before the gate.

## Frozen inputs to the orchestrator

- CMPCT1 worker: `benchmarks/one/one_genesis_cmpct1_product_worker.py` at the sealed candidate checkout.
- Historical worker: `benchmarks/one/one_genesis_historical_product_worker.py`; frozen product code remains at:
  - v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
  - v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`
- Repetitions: exactly 5 per supported phase.
- Statistic: median; retain all 5 raw samples.
- Selective request: supplied by the deterministic selective-access authority, never chosen by the contender.

## Authorization boundary

Pre-gate tests may use only worker `--transfer-fixture` mode on synthetic/transfer inputs and are permanently production-ineligible.

Production orchestration must refuse unless the caller explicitly supplies `CMPCT_GENESIS_REAL_GATE_AUTHORIZED=1` and source binding. Authorization may be propagated downward only after the top-level Genesis executor has passed both its calendar lock and explicit real-execution switch. Ambient authorization is not sufficient to turn a transfer fixture into production evidence.

## Measurement assembly

For each supported phase, retain the five worker outputs verbatim under `samples` and expose medians for CPU, wall, and peak RSS. `stored_bytes` comes from the actual built archive and must be identical across repeated deterministic builds; differing persistent bytes or deterministic wire hashes are a semantic/evidence failure, not a value to average.

Whole-read exactness is required on every repetition.

Selective access is:
- CMPCT1: supported through authenticated ONE range/member read;
- v0.30: supported only through frozen `read_member_with_stats`;
- v0.29: explicit `unavailable` unless a separately preregistered exact frozen selective surface is proven.

Unknown touched/decoded/auth/proof/temp/reconstruction metrics remain `unavailable`; do not infer them from requested size, returned size, archive size, or timing.

## Semantic and reader-burden evidence

The measurement orchestrator must not invent static product claims merely to satisfy the final schema. Runtime exactness/integrity facts proven by workers are retained in raw phase samples. Recovery, portability, reader discovery, hidden-codec status, or other static capability claims must come from an explicit authority/evidence layer or remain `unavailable` until such a layer is frozen.

## Required negative tests

1. fewer/more than five samples cannot be promoted as the preregistered median;
2. one failed exact reconstruction fails the workload result;
3. deterministic build-size or wire mismatch fails closed where promised;
4. a negative timing/resource metric fails closed;
5. v0.29 selective remains unavailable;
6. absent product access counters remain unavailable rather than zero;
7. transfer-fixture output cannot claim production eligibility;
8. no module/path containing Genesis `neutral_hostile` or `resemblance_hostile` generation may be imported by this layer;
9. no delta, verdict, aggregate rank, campaign decision, or winner field may be emitted.

## Claim boundary

Passing this preregistration can establish `ADVANCE_RAW_ADAPTER_ASSEMBLY`: the common measurement boundary is executable on transfer/synthetic inputs and preserves raw evidence correctly. It is not evidence that the 15-workload Genesis gate has run, that any contender is faster/smaller, or that ONE should remain primary.