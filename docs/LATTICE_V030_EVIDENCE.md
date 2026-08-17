# Lattice v0.30 evidence ledger

PR: #45

Status: **seed gate pending**.

This file is the durable regression-debt/evidence ledger for the Lattice campaign. It exists separately
from the design note so benchmark conclusions are not retroactively folded into the hypothesis that
preceded them.

## Frozen seed gate

- exact same-live-tree accepted v0.29 control for every workload;
- 15 public deterministic workloads, no dropped rows;
- candidate complete artifact <= accepted v0.29 on every row through exact fallback;
- >=128 KiB aggregate saving and >=64 KiB best-row saving to retain the first Lattice mechanism;
- strong tree verification for every emitted candidate;
- dependency depth 0 and node read amplification 1.0 for the first lane-transform seed.

## Adjacent negative evidence — Multi-View HyperPack

An independently developed v0.30 HyperPack branch executed on the fixed 724-file hostile structural
aggregate before Lattice's generalization run. It produced **0 B complete-artifact saving** versus accepted
attempt #5 and therefore fell back byte-identically to v0.29 (`47,147,764 B`). Its portfolio creation path
was also very expensive (~672 s), so non-adjacent multi-view placement is rejected as the primary v0.30
compression breakthrough.

The experiment did expose a more important invariant. A weighted read-amplification score allowed an
inherited plan with a ~53.73x worst-member outlier. A member-safe variable-size plan reached ~7.66x
worst-member amplification while costing only 56 B more at the compared packing layer. Therefore future
elastic packing may use **per-member <=8x amplification** as the admission law; weighted-average locality
alone is insufficient. The 56 B storage debt means this locality repair is not silently promoted as a
size win.

Footnote: this conclusion is preserved as negative/architectural evidence even though HyperPack's workflow
ended red after its result because an assertion read the inherited summary's worst-member value rather than
the selected member-safe plan. The compression result itself was already complete and showed exact v0.29
fallback; the failing assertion does not turn 0 B into a hidden win.

## Pending evidence

The authoritative first complete-artifact Lattice result will come from
`.github/workflows/lattice-v030-breakthrough.yml` and its uploaded `lattice-v030-generalization.json`.
Until that run completes successfully, no complete-artifact Lattice performance claim is accepted.

A second, cheaper causal oracle on PR #44 opens the real accepted attempt-5 graph and prices lane transforms
plus <=8x/8 MiB elastic fusion directly against the public ML workload. Its first run never reached the
mechanism because the workflow omitted public corpus-generator dependencies; that runner defect has been
repaired without changing the oracle or its preregistered >=64 KiB disproof threshold.

Footnote: a green seed gate does not close creation/extraction/memory/portability debt and does not make
v0.30 a release. Those obligations remain explicit until the normal promotion gates are run unchanged.
