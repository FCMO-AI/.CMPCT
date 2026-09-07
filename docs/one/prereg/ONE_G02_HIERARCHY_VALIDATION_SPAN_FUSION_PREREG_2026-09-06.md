# ONE-G0.2 hierarchy validation-span fusion preregistration — 2026-09-06

Status: **preregistered causal follow-up; diagnostic only, not promotion authority**.

## Mission lock

The first-level hierarchy-fusion candidate at exact source `316b1e0d22ca8895277a3efa5bd7eafb3e68313d` removed 99.95–99.98% of transient hierarchy-ref staging and made every frozen row faster, but failed its locked median elapsed gate by a narrow margin: `0.803663x` versus required `<=0.80x`. That candidate is terminally failed under its own preregistration and is not being rescued by changing the threshold.

Inspection localizes one remaining avoidable pass: before emitting each first-level concat, the candidate rereads every Segment length to compute that chunk's declared span. The shared writer's mandatory validation pass already visits every Segment and accumulates exact covered length. For hierarchical plans, only `ceil(segment_count / ONE_MAX_NODES)` chunk spans are needed.

Hypothesis: while performing the already-required validation scan, capture each 4,096-Segment group's exact covered span into the small parent-level metadata, then emit the first hierarchy layer directly from Segment[] using those prevalidated spans. This removes the extra span-summing reread while preserving the previous candidate's staging elimination.

This is not exact-capacity sizing, does not change output allocation, does not add a workload classifier, and does not alter reader-visible ONE semantics.

## Referee / disproof

The diagnostic is falsified if any of these occur:

1. validation acceptance/rejection differs from the seed validation for any frozen valid or hostile case;
2. canonical hierarchy bytes differ from the seed hierarchy bytes;
3. Surprise node numbering, concat node numbering, declared spans or final target span differ;
4. candidate temporary hierarchy metadata is not lower than seed on every hierarchical row;
5. after charging the additional boundary-span bookkeeping inside the validation pass, median candidate/seed `(validation + hierarchy emission)` elapsed is greater than `0.75x`, or any frozen row is above `0.95x`;
6. the gain depends on precomputing span data outside the timed candidate path.

A PASS earns a full shared-native-writer A/B only. It cannot promote the mechanism by itself.

Do not rescue a FAIL with corpus labels, segment-count thresholds beyond the already-canonical `segment_count > ONE_MAX_NODES` hierarchy branch, Surprise-rate dispatch, or retuned gates.

## Frozen valid shapes

Use the same structural shapes as the failed predecessor to preserve causal comparability:

- 4,097 all-Ref segments;
- 4,097 mixed Ref/Surprise;
- 16,384 all-Ref;
- 65,536 mostly-Ref with bounded Surprise count.

Each timed arm begins before a complete validation scan and ends after complete hierarchy concat emission. Output buffer allocation remains equal/excluded from both arms; hierarchy staging allocation and validation-span metadata allocation are included.

## Hostile validation shapes

At minimum:

- zero-length segment;
- unknown kind;
- source Ref out of bounds;
- Surprise target range out of bounds;
- incomplete target coverage;
- over-coverage;
- node-budget overflow where constructible without undefined behavior.

The candidate must return the same rejection class as the seed model before any hierarchy bytes are trusted.

## Required output

Per valid row report:

- exact hierarchy bytes and byte parity;
- seed/candidate transient hierarchy metadata;
- validation+emission elapsed for both arms;
- candidate/seed elapsed ratio;
- group-span count.

Report hostile rejection parity separately. Preserve a terminal negative if the locked gate fails.
