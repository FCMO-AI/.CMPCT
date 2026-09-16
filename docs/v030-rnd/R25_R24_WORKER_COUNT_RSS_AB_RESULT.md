# r24 worker-count RSS A/B result

Status: **accepted exact-head Forge diagnostic / `R24_SINGLE_WORKER_AMBIGUOUS` / no production or release credit**.

This record preserves the result of the frozen worker-count experiment in `docs/v030-rnd/R25_R24_WORKER_COUNT_RSS_AB_PREREG.md`. It does not alter the experiment, its decision bands, the Shifted corpus, canonical r24 bytes, release thresholds, or production worker policy.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`;
- exact source: `60c3b5986dd13f1fddf9b1475e475a5275dd32ab`;
- workflow: `CMPCT v0.30 shipping-r24 worker-count RSS A/B`;
- workflow run: `33637277836`;
- substantive job: `100274712199` (`r24-worker-count-ab`);
- artifact id: `9849750891`;
- artifact: `v030-r24-worker-count-rss-ab-60c3b5986dd13f1fddf9b1475e475a5275dd32ab`;
- artifact ZIP digest: `sha256:e246ff768cb61dc65e5c058d0eeeeab44f0b367421466ad8067701680b68c96e`;
- schema: `cmpct-v030-r24-worker-count-rss-ab-v1`;
- target: `resemblance_hostile_v1/01_shifted_versions`;
- release credit: **false**.

The exact-source classifier completed and the substantive fresh-process A/B ran to completion. The workflow independently ratcheted the frozen identity and decision bands before uploading the evidence.

## Frozen contract

The preregistered terminal bands were:

- RSS reduction >=20% **and** wall-time ratio <=1.25 -> `R24_SINGLE_WORKER_REHAB_SUPPORTED`;
- RSS reduction <5% -> `R24_WORKER_PARALLELISM_RETIRED`;
- otherwise -> `R24_SINGLE_WORKER_AMBIGUOUS`.

The experiment permits no production change and grants no release credit.

## Exact result

| Arm | Median total peak RSS | Median incremental peak RSS | Median wall time |
|---|---:|---:|---:|
| inherited shipping worker count (`4`) | **239,780 KiB** | **116,984 KiB** | **0.478535 s** |
| forced single worker (`1`) | **209,132 KiB** | **86,336 KiB** | **0.762858 s** |

Derived frozen metrics:

- total-peak RSS reduction: **0.1278171657 / 12.7817%**;
- wall-time ratio: **1.5941546965x**;
- worker counts observed: inherited `[4]`, single `[1]`;
- exact output/stat identity across arms: **true**.

The result is therefore exactly **`R24_SINGLE_WORKER_AMBIGUOUS`**. It is below the 20% support threshold and substantially exceeds the allowed 1.25x wall-time ratio for a supported single-worker rehabilitation. It is also above the <5% retirement threshold, so the frozen contract does not authorize calling worker parallelism irrelevant.

## Causal interpretation

The operation-scoped dictionary-policy repair made the worker-count comparison scientifically valid by restoring exact output identity between four-worker and one-worker r24 construction. Under that repaired semantic regime, worker count materially influences peak memory, but the blunt one-worker intervention exports too much create-time debt to qualify as a product repair.

This narrows the Shifted r24 memory problem:

1. worker parallelism owns a measurable **~30,648 KiB** of total peak RSS under this exact runner/regime;
2. removing that concurrency wholesale costs about **59.4%** wall time;
3. therefore a global `workers=1` switch is not justified;
4. the remaining opportunity is narrower lifetime/ownership or scheduling work that captures part of the 12.8% memory headroom without paying the measured 1.59x wall-time cost.

This result must not be promoted into a claim that four workers are universally optimal or that worker parallelism is the dominant owner of the complete r25 product RSS. It tests one genuine-r24 Shifted build after the policy-propagation repair.

## Relationship to the repaired dictionary-policy win

The preceding causal evidence remains independently valid: transporting the release dictionary policy into worker execution restored dictionary-live r24 bytes and produced the same repaired output at one and four workers. The worker-count A/B does not revoke that semantic repair. It prices one exported resource trade-off after the repair.

No archive bytes, dictionary eligibility, tree identity, format grammar, integrity/recovery rule, locality limit, benchmark comparator, or release threshold changed in this experiment.

## Forge decision

**Do not productize single-worker r24 as the Shifted RSS fix.** The frozen result is ambiguous, not support.

The next intervention must be lower-radicality than globally removing worker concurrency: isolate which concurrent encode/training lifetime contributes the recoverable ~30 MiB while preserving four-worker throughput where useful, or obtain a new causal measurement showing a bounded scheduling/ownership change can recover material memory without violating the full release runtime gate. If no such narrower owner is found, retain the current worker count and attack another measured RSS owner rather than tuning the frozen bands.

## Reopening / supersession

A new worker-count experiment is justified only by a material implementation or ownership change that alters the causal regime (for example, bounded in-flight candidate ownership, process/allocator lifetime changes, or a different operation-scoped scheduling mechanism). Merely rerunning until wall time improves is not a reopening predicate.

The normative next product evidence remains the exact full-product runtime/RSS authority on the repaired source fingerprint; this diagnostic alone cannot unlock v0.30.
