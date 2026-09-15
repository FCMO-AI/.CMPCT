# A01 internal prior-art reconciliation — shifted latent consensus floor

Status: **mandatory correction to A01 novelty/priority framing; no product evidence**.

A post-O0 repository-wide adversarial pass found an important inherited mechanism that the first A01 preregistration did not cite:

- `benchmarks/v030_shifted_latent_consensus_floor.py`;
- `.github/workflows/v030-shifted-latent-consensus-floor.yml`.

This is materially adjacent and in several ways **stronger than the new A01 O0 toy oracle**. It constructs a latent consensus payload from candidate records, charges the consensus bytes and residual/index bytes, compares against observed-root candidates, includes negative controls, uses three deterministic 64 MiB runtime-style workloads, and has explicit `PROCEED_CAUSAL` / `RETIRE_FAMILY` decisions. It also handles shifted/variable-length-ish record structure through the existing runtime fixture families rather than only 128 KiB same-length synthetic byte vectors.

## Correction

Do **not** describe A01 O0 as inventing or first introducing latent/synthetic physical roots inside CMPCT. The repository already contained a shifted latent-consensus floor instrument before this activation.

The accepted A01 O0 result remains valid as a separately frozen charged measurement, but its value is narrower:

1. it independently confirms latent-root headroom under a simpler transparent exact residual accounting model;
2. it adds explicit random/two-cluster/near-medoid hostile controls and immutable receipts;
3. it triggered a fresh causal-predictor line;
4. it does **not** establish internal mechanism novelty.

## Missing authority that must be recovered

At the time of this correction, the repository tree contains the inherited benchmark and workflow but no obvious checked-in result receipt for the shifted-consensus run under `docs/`. Therefore its **code-level prior art is direct**, while its latest result-bearing outcome is not yet recovered from durable repository evidence.

Do not infer `PROCEED_CAUSAL` or `RETIRE_FAMILY` merely from the benchmark's existence. Recover an actual workflow artifact/log or rerun the exact inherited instrument under valid evidence custody before using its outcome to promote or retire A01.

## Priority consequence

Before spending materially on new A01 synthesis algorithms, execute/recover the inherited shifted-latent-consensus floor and compare its mechanism/results against the A01 O0/O1 line. If it already answers the same causal question at a stronger MRS, A01 should converge on that evidence rather than duplicate it.

If its result is negative, A01 must explain why the new charged O0 positive is not simply a friendlier below-MRS replay. If its result is positive, the next task is to unify the evidence and attack generic admission/productization rather than keep generating synthetic confirmations.

This correction is a direct application of the anti-local-optimum rule: repository archaeology outranks attachment to a newly created experiment.