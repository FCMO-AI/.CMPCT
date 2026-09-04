# r24 operation-scoped dictionary-policy repair — frozen Forge preregistration

Status: **FROZEN BUILDER REPAIR / RELEASE CREDIT REQUIRES NORMAL AUTHORITIES**

Predecessor evidence: `R25_R24_WORKER_POLICY_PROPAGATION_V2_RESULT.md`, terminal decision `THREAD_LOCAL_POLICY_LEAK_CAUSAL`.

## Problem

The v0.30 shipping-r24 parent thread deliberately admits `.bin` data into the text/dictionary policy, but `Builder._encode_candidate()` re-evaluates the dynamic `TEXT_EXT` predicate inside encoder worker threads. The release predicate is thread-local, so parallel workers observe a different policy than the parent. On Shifted this makes the trained dictionary dead and produces an archive 391,869 B larger than the exact one-worker/propagated answer.

Correctness/determinism is the primary defect. The inherited path is faster only because it skips intended dictionary work.

## Frozen intervention

Use the lowest-sufficient operation-scoped repair:

1. immediately after dictionary training, while still in the policy-owning build thread, capture the exact content hashes for which dictionary audition is eligible;
2. store that immutable eligibility set on the Builder instance for this build only;
3. encoder workers consume the captured fact rather than re-evaluating a thread-local policy;
4. no process-global profile mutation, no worker-count reduction, no archive grammar change and no reader change.

Implementation may use an encoder-only compatibility wrapper around the existing candidate audition, but it may not change codec levels, dictionary training, candidate order, locality, integrity, recovery or selection thresholds.

## Exact acceptance sequence

### A. Determinism / causal retention

On `resemblance_hostile_v1 / 01_shifted_versions`:

- normal four-worker shipping r24 after the repair must strongly verify;
- one-worker shipping r24 after the repair must strongly verify;
- complete archive bytes + SHA-256 + stable build stats must be exact between worker counts;
- both must report the dictionary live;
- the repaired four-worker complete archive must equal the accepted v2 propagated artifact semantics (29,883,734 B on v2's exact source/corpus regime; a later source may differ only if the deterministic corpus itself legitimately changed and that change is separately proven).

### B. Negative control

An ordinary historical Builder invocation without the dynamic release policy must retain its existing deterministic output. The repair is policy transport, not a new `.bin` classification rule.

### C. Product/runtime debt

The repair receives no release waiver. The exact current full product/runtime/RSS gate must determine whether the extra intended dictionary work is acceptable. The v2 diagnostic observed a 17.615% Shifted r24 wall-time cost versus inherited buggy four-worker behavior; that debt remains explicit until the ordinary gate says otherwise.

### D. Hard invariants

No change to:

- r24/r25 grammar or complete-member accounting;
- accepted v0.29 product floor;
- genuine-r24 fallback law;
- <=8x locality / <=8 MiB decode-unit law;
- integrity/authentication/recovery;
- hostile-input/resource behavior;
- native/platform requirements;
- competitor settings or timing/size thresholds.

## Frozen decisions

- `REPAIR_CAUSALLY_VALID`: A + B pass exactly. Proceed to the normal full product/runtime/release authorities; any performance red remains rehabilitation debt.
- `REPAIR_CHANGES_HISTORICAL_POLICY`: negative control changes. Reject this implementation and narrow the policy ownership boundary.
- `REPAIR_FAILS_WORKER_IDENTITY`: worker-count bytes/stats still differ. Reject and inspect the next thread-visible state owner.
- `INVALID_REPAIR_EVIDENCE`: corpus/source/verification/fingerprint requirements are not established.

No wording or threshold in this freeze may be changed after result-bearing execution.
