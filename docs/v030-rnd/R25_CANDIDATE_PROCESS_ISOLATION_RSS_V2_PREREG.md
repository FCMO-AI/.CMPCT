# r25 PrefixGraph process-isolation RSS A/B v2 — superseding custody freeze

Status: **FROZEN BEFORE V2 RESULT-BEARING EXECUTION / Forge R2 diagnostic / no release credit**.

## Supersedes

V2 supersedes `R25_CANDIDATE_PROCESS_ISOLATION_RSS_PREREG.md` for evidence custody only.

After V1 substantive execution had already begun, hostile review of `tools/check_ci_topology.py` found a workflow defect: `.github/workflows/v030-r25-candidate-process-isolation-rss.yml` omitted the mandatory CI-lane declaration and exact-running-receipt concurrency contract. Its measurement surface had therefore already become immutable, and it may not be edited in place to manufacture a green receipt. Any V1 measurements remain historical diagnostic output only and are not accepted evidence.

## Scientific contract — unchanged

V2 changes **none** of the V1 scientific question, code, workload, arms, identity requirements, memory charging, repetitions, order or decision bands.

It reuses the immutable V1 instruments byte-for-byte:

- `benchmarks/v030_r25_candidate_process_isolation_rss_worker.py`;
- `benchmarks/v030_r25_candidate_process_isolation_rss_oracle.py`.

The decisive metric remains sampled whole-process-tree live RSS (`parent + every transitive live descendant`) at <=10 ms intervals. Parent-only `ru_maxrss` remains diagnostic. Exact final product bytes/SHA/tree/selection and exact semantic-owner identities remain mandatory. The isolated PrefixGraph child must exit before G0-G4 continues. Two repetitions per arm and the alternating V1 order remain unchanged.

Frozen decision bands remain exactly:

- >=20% median whole-tree peak reduction: `PROCESS_LIFETIME_BOUNDARY_SUPPORTED`;
- <10%: `PROCESS_ISOLATION_RETIRED_AS_PRIMARY`;
- 10–20%: `PROCESS_ISOLATION_AMBIGUOUS`;
- supported result with isolated wall ratio >1.15: `PROCESS_LIFETIME_BOUNDARY_SUPPORTED_WITH_MAJOR_CREATE_DEBT`.

No production source, archive grammar, representation, selector, admission rule, locality/decode-unit limit, verification/integrity rule, recovery guarantee, corpus, comparator, runtime threshold or release fingerprint rule is changed by this freeze. Release credit remains false.

## V2 custody repair

The only changed surface is a new workflow, `.github/workflows/v030-r25-candidate-process-isolation-rss-v2.yml`, which must:

1. declare `ci-lane: deep`;
2. declare the repository's `preserve-running-exact-receipt` policy;
3. bind `EVIDENCE_HEAD` to `github.sha`;
4. scope push to `agent/v030-authoritative-integration` and the V2 custody files;
5. use a top-level exact-SHA concurrency group with `cancel-in-progress: false`;
6. checkout and assert the exact evidence SHA;
7. execute the immutable V1 worker/oracle without modification;
8. run `tools/check_ci_topology.py` explicitly on the V2 workflow before artifact upload;
9. upload the exact JSON receipt only after the frozen identity/decision ratchet and topology check pass.

## V2 authority rule

Only a substantive V2 run that completes the measurement, frozen ratchet, topology self-check and artifact upload can be accepted for causal interpretation. V1 workflow success/failure, classifier state, partial logs or measurements cannot substitute.

This V2 freeze becomes immutable once V2 result-bearing execution begins. Any further material defect requires another superseding freeze preserving V1 and V2 history.
