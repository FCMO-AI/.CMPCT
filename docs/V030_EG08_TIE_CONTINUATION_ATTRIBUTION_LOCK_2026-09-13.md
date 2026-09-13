# v0.30 EG08 tie-continuation attribution lock — 2026-09-13

Status: **preregistered causal attribution; research evidence only**

## Question

EG08's fixed effort ladder (`3, 6, 12, 19`) continues after either a strict storage win **or a tie**, and stops at the first strictly worse rung. The strict eligible-nine transfer shows that EG08 generalizes strongly in stored bytes but is blocked only by exported creation economics (`low_yield_cpu_export_cost_ok`).

Before changing the Builder, determine whether continuing through ties earns any of EG08's selected bytes. This uses EG08's already-recorded per-pack attempt trace and does not alter or recompress product bytes.

## Falsifiable hypothesis

**H0:** On all nine preregistered EG07-valid transfer surfaces, every final EG08 selected payload can be reached without ever crossing a tie. Equivalently, replaying the observed ladder with `stop at first tie or worse` produces exactly the same selected payload size for every pack and every workload while avoiding at least one effort attempt somewhere.

Disproof is intentionally strict and threshold-free: **one pack** whose eventual EG08 strict win occurs only after crossing a tie falsifies H0.

## Frozen surfaces

Use exactly the eligible-nine set from `docs/V030_EG08_ELIGIBLE9_TRANSFER_LOCK_2026-09-13.md`:

Neutral/current15: Office, Analytics, Logs, ML artifacts, Large mixed binary.

Hostile: shifted versions, false neighbors, boundary churn, incompressible.

No surface may be added or removed after observing the attribution.

## Replay method

For each pack's authenticated EG08 telemetry:

1. start from `current_payload_bytes` as the incumbent;
2. replay the already-observed `tried` ladder in order;
3. on a strict smaller payload, update the incumbent and continue;
4. on a tie or a worse payload, stop immediately;
5. compare that counterfactual selected size with EG08's actual `selected_payload_bytes`;
6. count attempts avoided, packs whose bytes change, and bytes of EG08 benefit that depend on crossing ties.

The analysis must require the original EG08 build to strongly verify and remain within the same locality geometry. It must not call a new compressor setting, tune a byte threshold, use workload/path/file-type identity, or modify an archive.

## Interpretation

- If H0 survives, `stop-on-tie` becomes a justified next Builder candidate because it is predicted to preserve exact EG08 archive payload sizes while eliminating redundant effort attempts. It still requires exact archive-identity and creation-CPU/RSS testing before promotion.
- If H0 is falsified, tie continuation carries real density information. The negative is preserved and the next CPU attack must use a different mechanism (first-pass fusion, reusable work, or a stronger content-derived bound) rather than silently dropping those bytes.

This attribution cannot change Genesis, v0.29, ONE, locality, integrity/recovery or version scores.
