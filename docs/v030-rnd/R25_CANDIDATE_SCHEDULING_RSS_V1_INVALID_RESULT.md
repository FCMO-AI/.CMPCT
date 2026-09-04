# r25 candidate scheduling RSS v1 — invalid result record

Status: **preserved invalid diagnostic / zero causal credit / zero release credit**.

## Authority

- source commit: `81b64517271baf4efa534ae1cadfa96d0b02c6d8`;
- workflow: `.github/workflows/v030-r25-candidate-scheduling-rss.yml`;
- workflow run: `33594786248`;
- substantive job: `100136114271` (`candidate-scheduling-rss`);
- artifact id: `9833258503`;
- artifact: `v030-r25-candidate-scheduling-rss-81b64517271baf4efa534ae1cadfa96d0b02c6d8`;
- uploaded artifact digest: `sha256:f02cbd7cd499a73ebbcbcad38c98370be2215c70727d97fb3eced417a5447788`;
- schema: `cmpct-v030-r25-candidate-scheduling-rss-v1`;
- `experiment_valid`: `false`;
- release credit: `false`.

The substantive A/B did run in fresh processes and uploaded its JSON, but its frozen oracle rejected the result. Per Custody law, the worker, oracle, preregistration and result are not edited after execution.

## Defect

The frozen question requires every worker to prove the same source/product tree identity while changing only candidate scheduling. The v1 worker correctly ran the shipping `release_product.build` path and then strongly verified the resulting product with `release_product.strong_verify`. That shipping verifier reports the canonical filesystem/user-tree identity.

The v1 parent oracle instead computed its expected tree with `canonical.RC.treehash(source)`, which is the private release-candidate research-content identity. Existing canonical semantic-owner instrumentation makes the domain distinction explicit:

- shipping product verification identity: `canonical.treehash(source)` / `canonical-filesystem-user-tree-v1`;
- private research-candidate verification identity: `canonical.RC.treehash(source)` / `research-content-tree-v1`.

The v1 oracle therefore compared two intentionally different identity domains and marked otherwise strongly verified shipping workers invalid. This is an instrument defect, not evidence that either A/B arm reconstructed the wrong user tree.

The same run also exposed a separate CI-custody defect: the v1 workflow declared split classifier / exact-receipt policy but did not satisfy the repository topology checker. That workflow remains historical result-bearing evidence and is not rewritten after execution.

## Observed but inadmissible numbers

The invalid artifact reported:

- concurrent median total peak RSS: `395760 KiB`;
- serialized median total peak RSS: `400248 KiB`;
- nominal serialized reduction: `-0.01134020618556701` (serialization was about 1.13% worse);
- concurrent median wall time: `50.9826503825 s`;
- serialized median wall time: `52.687608067 s`;
- nominal threshold decision: `retires-concurrency-primary-explanation`.

**These numbers receive no causal decision credit because the frozen validity gate failed.** They may be used only as a debugging witness for the superseding instrument. The concurrency hypothesis is not retired by v1.

## Superseding requirement

A new freeze must preserve the original arms, workload, alternating order, exact artifact-identity requirement, fresh-process total-RSS metric, and 20% / 10% decision thresholds while repairing the identity-domain proof. The superseding worker/oracle must explicitly bind both:

1. `research_tree_sha256 = canonical.RC.treehash(source)` for PrefixGraph eligibility/private candidate context; and
2. `expected_verification_tree_sha256 = canonical.treehash(source)` for the shipping product strong-verification domain.

Every concurrent/serialized shipping worker must strongly verify against the second identity, report both identities, select the same representation, and produce identical complete product bytes/SHA/tree pairwise. The superseding workflow must also satisfy split exact-receipt custody before its result is accepted.

## Scoped negative constraint

Do not reinterpret the v1 `-1.13%` observation as evidence against concurrency. Reopen causal interpretation only from a superseding valid run with the corrected identity-domain proof. Conversely, do not rerun the exact v1 instrument expecting a different scientific answer: its validity comparison is structurally wrong for the shipping product domain.
