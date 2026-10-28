# r25 candidate scheduling RSS A/B v2 — superseding frozen Forge preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / Forge diagnostic / no release credit**.

## Supersedes

This freeze supersedes `docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_PREREG.md` for causal interpretation only. V1 remains immutable and is preserved in `docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V1_INVALID_RESULT.md`.

The v1 substantive run proved the instrument had an identity-domain defect: the shipping worker strongly verified a canonical filesystem/user-tree hash, while the parent oracle compared that receipt against `canonical.RC.treehash(source)`, the private research-content identity. Existing canonical semantic-owner instrumentation already distinguishes those domains. The v1 result is therefore invalid and grants no positive or negative causal credit.

V2 changes **only the identity proof and CI custody** required to make the original A/B valid. It does not change the causal question, workload, arms, repetition order, measurement metric, thresholds, product code, or selection semantics.

## Causal predecessor

`docs/v030-rnd/R25_SEMANTIC_OWNER_RSS_V2_RESULT.md` established that neither exact canonical candidate family reproduces the shifted-version shipping peak in isolation:

- shipping product: **400,000 KiB** median total fresh-process peak RSS;
- exact G0-G4: **180,654 KiB**;
- exact PrefixGraph: **200,670 KiB**.

The unresolved boundary remains product composition/lifetime. Shipping overlaps G0-G4 and PrefixGraph construction when PrefixGraph is eligible. V2 asks whether that overlap is the primary owner of the extra shipping peak.

## Frozen question

> On deterministic `resemblance_hostile_v1 / 01_shifted_versions`, does forcing the exact canonical G0-G4 and PrefixGraph contenders to execute serially materially reduce total fresh-process shipping peak RSS while preserving the exact selected complete product artifact and canonical filesystem/user-tree identity?

## Arms

### A — inherited concurrent shipping

Run unmodified `experiments.entropygraph_v030_release_product.build` with the inherited two-worker release-candidate tournament.

### B — serialized scheduling override

Before calling the same product build, replace only `canonical.RC.ThreadPoolExecutor` with an inline executor implementing the same context-manager and `submit(...).result()` contract. Candidate builders execute synchronously in the inherited submission order.

The override may not modify semantic-owner identities, PrefixGraph eligibility, candidate bytes/arguments, candidate admission, exact size comparison, selection, strong verification, final r24/r25 product selection, grammar, integrity, recovery, locality/decode-unit bounds, corpus identity, or benchmark thresholds.

## Identity domains — v2 repair

Every worker MUST report both identities from the exact supplied source tree:

1. `research_tree_sha256 = canonical.RC.treehash(source)` with identity domain `research-content-tree-v1`. This is the identity used by the private release-candidate graph and PrefixGraph eligibility.
2. `expected_verification_tree_sha256 = canonical.treehash(source)` with identity domain `canonical-filesystem-user-tree-v1`. This is the identity required by the shipping release-product strong verifier.

Every worker MUST strongly verify its final shipping product and require:

`verified_tree_sha256 == expected_verification_tree_sha256`.

The parent oracle MUST require the same research identity and the same canonical product identity across all workers, but MUST NOT compare the canonical product-tree receipt directly to the research-content identity.

This is a correction of a category error, not a relaxation: both identities are now explicit and independently checked instead of one domain being silently substituted for the other.

## Workload and repetitions

Build the deterministic corpus once in the parent and supply the same immutable source directory to every worker.

Run two independent fresh-process repetitions per arm in alternating order:

1. concurrent -> serialized;
2. serialized -> concurrent.

## Validity conditions

The experiment is invalid unless all conditions hold:

1. every worker proves exact object identity for `canonical.RC.PG`, `canonical.RC.G04`, and `canonical.RC.READER` against `PROFILE_ISOLATION`;
2. every worker reports the same `research_tree_sha256` computed from the supplied source;
3. every worker reports the same `expected_verification_tree_sha256 = canonical.treehash(source)`;
4. every final shipping product strongly verifies and `verified_tree_sha256` equals that canonical expected product-tree identity;
5. both arms select `prefixgraph`;
6. paired concurrent/serialized products have identical complete byte count, physical SHA-256, verified product tree and selection;
7. serialized workers report exactly two inline executor submissions;
8. total fresh-process peak RSS is the decisive causal metric; baseline-subtracted `ru_maxrss` is diagnostic only;
9. no production source is modified to obtain the result;
10. the result-bearing workflow satisfies split classifier / exact-SHA non-cancelling receipt custody.

Any failure makes the result invalid and preserves concrete worker failures. An invalid result may not retire or support the hypothesis.

## Decision thresholds — unchanged from v1

- **Support concurrency/lifetime ownership:** serialization preserves exact product identity and lowers median total fresh-process peak RSS by **>=20%**.
- **Retire concurrency as the primary explanation:** valid serialization lowers median total peak RSS by **<10%**.
- **Ambiguous:** valid reduction is **10–20%**; no production scheduling change.

Wall time is recorded and remains explicit debt. Even a causal RSS win grants no release credit and must later survive the unchanged authoritative runtime/RSS/selective-read gate before any product promotion.

## Custody

This preregistration, its v2 worker/oracle and its result-bearing workflow become immutable once a substantive v2 run begins. Any further defect requires a new superseding freeze. V1 observations may not be used to alter these thresholds or interpretation.
