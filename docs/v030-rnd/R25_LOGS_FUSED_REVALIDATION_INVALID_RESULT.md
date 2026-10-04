# Logs one-session extraction revalidation — invalid comparator receipt

Status: **INVALID FOR SCIENTIFIC INTERPRETATION / CUSTODY DEFECT PRESERVED / NO RELEASE CREDIT**

This record preserves the exact current-head run that appeared to show a flat/slightly negative one-session Logs extraction result, and explains why that measurement cannot be interpreted as evidence for or against the fused extractor.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `813595d17336960beb2d1a4e2b3bcc535336a5ac`
- workflow: `CMPCT v0.30 logs runtime productization`
- workflow run: `33678905254`
- substantive job: `100410400533`
- target: `neutral_hostile_v1/05_logs_and_telemetry`
- release credit: `false`

Focused product/safety semantics completed first with **16/16 tests passing**, including the newly ratcheted cross-platform symlink policy. The timed oracle then reported:

- baseline median: **0.043068192 s**;
- candidate median: **0.043116852 s**;
- apparent improvement: **-0.11298%**;
- frozen promotion threshold: **+10%**;
- exact reconstructed trees: true.

Those timing numbers are preserved as observed telemetry only. They are **not** a valid A/B result.

## Why the A/B is invalid

The oracle imported:

- `experiments.entropygraph_v030_release_product_logs_candidate` as `BASELINE`;
- `experiments.entropygraph_v030_release_product_logs_runtime` as `FUSED`.

However, commit `9f761a13a14f77c391ecf71e6d4c51e93337f684` had already promoted the one-session extractor into the Logs candidate itself. The current `BASELINE.extract` therefore delegates Logs archives to `LOGS_FUSED.extract`, while `FUSED.extract` also delegates the same archive to the same fused implementation.

The revalidation consequently timed **fused vs fused**, not mature pre-promotion extraction vs fused extraction. A near-zero delta is exactly what such comparator collapse predicts. Treating it as a negative would violate custody law by silently changing the comparator after the mechanism was promoted.

## Historical comparator identity

The parent of promotion commit `9f761a13` (`3ae4dd6729b673639b8a7acbe342d723488f1751`) preserves the actual mature comparator. Its Logs extraction path:

1. validates the positive caller byte budget;
2. decodes the authenticated filesystem manifest;
3. charges user regular bytes against the caller budget;
4. rejects unsafe symlinks;
5. calls the mature `LOGS.extract` path.

The repaired current oracle reconstructs exactly that extraction ownership boundary while using the current canonical cross-platform symlink predicate. This is a custody repair only; the workload, 11-round rotating order, +10% promotion threshold, exact-tree requirement and release-credit law are unchanged.

## Terminal interpretation

**Do not retire or promote the fused extractor from run `33678905254`.** The scientific result is invalid because comparator independence was lost.

The next authority is the repaired exact-head revalidation in `benchmarks/v030_logs_semantic_owner_runtime_oracle.py`. Only that independent comparator may confirm, reject or supersede the historical +22.91% promotion evidence under the current product regime.

## Reopening / prevention

Future performance A/Bs for already-promoted mechanisms must bind comparator ownership independently rather than importing a public product symbol that can later be rebound to the candidate. A classifier/workflow green cannot repair comparator aliasing after the fact.
