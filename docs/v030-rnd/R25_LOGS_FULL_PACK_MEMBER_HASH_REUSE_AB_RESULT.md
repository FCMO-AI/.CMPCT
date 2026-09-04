# Logs full-pack member identity proof-reuse A/B — result

Status: **ACCEPTED SCOPED FORGE AMBIGUOUS / `LOGS_FULL_PACK_MEMBER_HASH_REUSE_AMBIGUOUS` / ZERO RELEASE CREDIT**

This record closes the frozen experiment in `R25_LOGS_FULL_PACK_MEMBER_HASH_REUSE_AB_PREREG.md`. The experiment changed no production source, archive bytes, pack framing, selection rule, recovery behavior, locality/decode-unit bound, cold selective-read semantics, integrity threshold, or release threshold.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `fcb05acfa7cf9d18ef02336c6056fc244e985071`
- workflow: `CMPCT v0.30 Logs restore attribution`
- workflow run: `33699056154`
- substantive job: `100474158137` (`full-pack-member-hash-reuse`)
- artifact id: `9872838956`
- artifact: `v030-logs-full-pack-member-hash-reuse-fcb05acfa7cf9d18ef02336c6056fc244e985071`
- artifact digest: `sha256:161baa9cf8259b65725236bdd4ba504e4d6836fcdc0a574cca34fd14c523b2b0`
- runner: Ubuntu 24.04.4 / Python 3.11.16
- target: `neutral_hostile_v1/05_logs_and_telemetry`
- selected representation: `logs-inverse`
- measured rounds: **21 paired alternating rounds**
- experiment valid: **true**
- release credit: **false**

The result-bearing A/B, frozen decision ratchet, CI-topology self-check, public-surface guard and evidence upload all completed successfully.

## Exact result

| arm | median complete extraction |
|---|---:|
| inherited control | **0.042391835 s** |
| whole-pack proof reuse | **0.040922930 s** |

Frozen derived metrics:

- candidate/control wall ratio: **0.9653493414x**;
- complete-extraction reduction: **0.0346506586 / 3.4651%**;
- whole-pack logical-SHA proof reuses observed per candidate extraction: **6**;
- ordinary logical SHA checks retained per candidate extraction: **6**;
- authenticated pack calls retained per candidate extraction: **7**.

The hostile expected-SHA separation check passed, candidate lifecycle restoration passed, and strong verification passed.

## Integrity interpretation

The candidate did not remove pack authentication. The unchanged `_read_pack` path continued to verify complete pack CRC32 and complete pack SHA-256. Proof reuse was permitted only when one logical member was exactly the complete already-authenticated pack and the member's declared expected SHA-256 exactly equaled the pack header's declared SHA-256.

Derived members and partial-pack members retained their inherited logical SHA-256 computation. Cold selective reads were unchanged. A synthetic mismatch between the member expected SHA and the authenticated pack-header SHA remained ineligible for proof reuse and exercised the inherited logical identity rejection path.

The measured speedup therefore represents genuine duplicate-proof headroom rather than borrowed integrity work.

## Frozen terminal decision

**`LOGS_FULL_PACK_MEMBER_HASH_REUSE_AMBIGUOUS`**

The preregistered support boundary required at least **4.0%** complete-extraction reduction and a candidate/control wall ratio `<=0.96x`. The measured **3.4651%** reduction / **0.96535x** ratio misses that bar.

It is also well above the `<1.0%` retirement boundary, so the mechanism may not be called irrelevant.

## Forge decision

Do **not** productize this proof-reuse rule by itself for v0.30, and do not rerun it until it happens to cross 4%. Preserve it as measured headroom that may be subsumed by a broader authenticated full-restore traversal improvement.

The next Logs intervention should return to another independently measured owner—most plausibly inverse-decode or authenticated-pack traversal/materialization—and may reuse this result only if the broader mechanism naturally eliminates the same redundant proof without adding special-case carrying cost. Any superseding intervention needs a new frozen causal contract.

## Reopening predicate

Reopen this exact standalone proof-reuse family only if one of the following materially changes:

1. the promoted Logs packing geometry creates substantially more exact whole-pack logical members;
2. a shared authenticated traversal can subsume the proof reuse with lower carrying cost while independently attacking another measured owner; or
3. a different runtime/hashing implementation changes the measured cost enough to justify a new preregistered question.

Runner noise, more repetitions of the same code, or relaxing the 4% support threshold is not a reopening predicate.
