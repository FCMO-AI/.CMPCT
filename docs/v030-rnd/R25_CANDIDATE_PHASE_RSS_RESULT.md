# r25 candidate-phase RSS ownership result — v1 evidence conflict

Status: **PRESERVED MEASUREMENT / EVIDENCE CONFLICT / causal interpretation withdrawn / no release credit**.

This record preserves the first substantive result from the v1 candidate-family RSS ownership oracle after the product-phase experiment ruled out canonical profile/manifest capture alone as the dominant owner of the current r25 peak-memory regression.

The measurement itself is retained. Its original candidate-family ownership interpretation is **not accepted**, because hostile review found that the isolated `prefixgraph` arm did not execute the same PrefixGraph implementation surface used by the canonical shipping product.

No selector behavior, candidate admission, archive grammar, integrity, recovery, locality/decode-unit limit, benchmark threshold, or release state is changed by this record.

## Authority

- exact source: `c2bbfdce215113790124c01fb96f69bf09b8962e`;
- workflow: `.github/workflows/v030-r25-candidate-phase-rss.yml`;
- workflow run: `33589815780`;
- substantive job: `100121374612` (`candidate-phase-rss`);
- artifact id: `9831560776`;
- artifact: `v030-r25-candidate-phase-rss-c2bbfdce215113790124c01fb96f69bf09b8962e`;
- artifact digest: `sha256:809845f1a769664cdb4d60294db4ce270a27d338cb691c1f613811c0246a111a`;
- schema: `cmpct-v030-r25-candidate-phase-rss-v1`;
- artifact-reported experiment valid: `true` under the v1 instrument;
- worker failures: `0`;
- release credit: `false`.

The substantive measurement really executed. This is not a classifier-only result. The conflict is semantic: the v1 instrument measured the wrong PrefixGraph implementation for the claimed shipping-candidate ownership comparison.

## Exact conflict

The v1 fresh-process worker imports:

`experiments.entropygraph_v030_prefixgraph_parallel as pg`

and uses `pg.build(...)` for its isolated PrefixGraph arm.

The canonical release product does not use that module as its PrefixGraph semantic owner. `experiments/entropygraph_v030_profile_isolation.py` defines:

- `PG_SOURCE = "experiments.entropygraph_v030_prefixgraph"`;
- a private canonical PrefixGraph clone `PG = _clone(PG_SOURCE, "experiments._v030_canonical_prefixgraph")`;
- the private release-candidate clone is explicitly bound with `RC.PG = PG`.

The canonical candidate builder then calls `RC.PG.build(...)`.

Therefore the v1 isolated PrefixGraph arm used the release-facing *parallel research wrapper*, while shipping used the private canonical clone of the historical PrefixGraph semantic owner. The wrappers are not execution-equivalent: the parallel wrapper exposes bounded concurrent anchor auditions and worker-policy fields that do not appear in shipping's own PrefixGraph build statistics.

That violates the intended causal question: an isolated arm cannot establish ownership of shipping RSS if it is not the exact implementation surface shipping invokes.

## Measurements preserved, but not promoted to ownership claims

### Shifted versions

`resemblance_hostile_v1 / 01_shifted_versions`

| Arm as actually measured by v1 | Median total peak RSS | Median diagnostic incremental RSS | Median wall time | Complete bytes |
|---|---:|---:|---:|---:|
| shipping product | **399,008 KiB** | 276,004 KiB | 58.334 s | 1,700,601 B |
| isolated G0-G4 arm | **149,068 KiB** | 26,064 KiB | 107.969 s | 1,723,056 B |
| **parallel research PrefixGraph wrapper** | **430,496 KiB** | 307,492 KiB | 5.578 s | 1,700,242 B |

The large parallel-wrapper RSS number is real for that wrapper. It is **not** sufficient evidence that the private canonical PrefixGraph candidate owns shipping's ~399 MiB peak.

### ML artifacts

`neutral_hostile_v1 / 09_ml_artifacts`

| Arm as actually measured by v1 | Median total peak RSS | Median diagnostic incremental RSS | Median wall time | Complete bytes |
|---|---:|---:|---:|---:|
| shipping product | **181,370 KiB** | 58,366 KiB | 36.894 s | 13,674,822 B |
| isolated G0-G4 arm | **154,944 KiB** | 31,940 KiB | 73.678 s | 13,674,596 B |
| parallel research PrefixGraph wrapper | structurally ineligible | — | — | — |

The ML G0-G4/shipping gap remains useful diagnostic evidence, because that arm does not depend on the PrefixGraph implementation mismatch. It still does not by itself identify the missing product-memory owner.

## Scoped negative constraint from the conflict

Do **not** use v1 to justify a PrefixGraph shipping-memory intervention. Before changing PrefixGraph worker policy, representation, scheduling, or admission, a superseding instrument must isolate the exact private canonical `RC.PG` implementation that shipping calls and independently verify byte/tree identity.

Do not edit the result-bearing v1 worker/oracle/workflow to repair the claim after seeing the result. They remain historical evidence of the instrument defect. The correction requires a new v2 freeze/instrument.

## Strongest surviving self-critique

The v1 instrument correctly tried to import all candidate surfaces before taking the RSS baseline, but it confused a release-facing optimization wrapper with the canonical product's semantic owner. That is exactly the kind of implementation-identity error Custody is supposed to catch: same mechanism name and similar bytes are not enough for causal attribution.

The previous interpretation also leaned too quickly on the numerical coincidence that the parallel-wrapper peak exceeded shipping. The correct question is not whether a nearby implementation can reproduce the magnitude; it is whether the **exact implementation shipping invokes** does so under an equivalent fresh-process boundary.

## Decision

**EVIDENCE CONFLICT -> supersede the candidate-family ownership instrument.**

The v2 experiment must:

1. invoke the exact private canonical PrefixGraph surface (`canonical.RC.PG` / the identical object used by the canonical candidate builder);
2. invoke the same exact G0-G4 semantic owner shipping uses;
3. assert object/module identity against the canonical release-candidate graph before measurement;
4. retain the same fresh-process, strong-verification, total-peak-RSS and two-order accounting boundaries;
5. require exact candidate archive/tree identity and fail closed if the private canonical arm cannot be isolated safely;
6. grant no release credit and make no selector/admission/scheduling change.

Only v2 may support the next candidate-family ownership decision.
