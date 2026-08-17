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

## Pending evidence

The authoritative first result will come from `.github/workflows/lattice-v030-breakthrough.yml` and its
uploaded `lattice-v030-generalization.json`. Until that run completes successfully, no complete-artifact
Lattice performance claim is accepted.

Footnote: a green seed gate does not close creation/extraction/memory/portability debt and does not make
v0.30 a release. Those obligations remain explicit until the normal promotion gates are run unchanged.
