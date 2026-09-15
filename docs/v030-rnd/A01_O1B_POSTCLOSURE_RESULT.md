# A01 O1b post-closure result

Status: **result-bearing run completed after the research PR was closed; raw `PREDICTOR_FALSE_NEGATIVE`; superseded by stronger inherited R4 `RETIRE_FAMILY`; no promotion**.

PR #107 was closed once the stronger inherited shifted-latent-consensus R4 retirement evidence was recovered. GitHub had already started the O1b job, and no cancellation action was available through the execution surface, so the in-flight job completed. Its evidence is preserved rather than hidden.

## Receipt

- research branch source head: `e51ec2f65cb2f4c5a69020d9dea294aac2eec4be`;
- PR merge-test checkout: `ed6c9f078066ea1a82b0ffa42acfaf6de4bc81ae`;
- workflow run: `34974530190`;
- job: `104398796234`;
- artifact: `10399230238`, `a01-o1b-ed6c9f078066ea1a82b0ffa42acfaf6de4bc81ae`;
- artifact ZIP SHA-256: `ca5735811d97caba428c75d37462f8866e9cb5b850d52b55a58a531c70151d61`;
- raw JSON SHA-256: `a95e648f549a821e4e286080b6da323162117589937139408c32db5ee24b36e6`;
- corpus fingerprint: `f947be639315d68b9cd4c1991b43367e08cd2da037e07903e65fe0d0822824ac`;
- raw decision: **`PREDICTOR_FALSE_NEGATIVE`**;
- exact roundtrip: all six families.

## Direct result

The unchanged 8% sampled consensus predictor correctly called the three intended unimodal families LATENT and random/near-center as OBSERVED. The false negative came from `three_cluster`:

- best single observed root: 410,701 B;
- best **two** observed roots: 409,519 B;
- synthetic root: **404,596 B**;
- synthetic advantage versus the frozen observed portfolio: **4,923 B / 1.20%**;
- predictor consensus advantage: **0.83%** -> `PREDICT_OBSERVED_OR_MULTIMODAL`.

Other material synthetic wins were predicted LATENT:

- private block bursts: 159,686 B vs 178,053 B observed portfolio, -18,367 B / -10.32%; predictor 31.54%;
- private sparse scatter: 166,044 B vs 187,343 B, -21,299 B / -11.37%; predictor 17.39%;
- shared history + private: 150,342 B vs 161,560 B, -11,218 B / -6.94%; predictor 23.40%.

Independent random remained strongly hostile: 1,159,626 B synthetic vs 1,049,027 B observed, +110,599 B / +10.54%.

## Strongest interpretation

The corrected O1b adjudicator fixed O1a's single-root/two-root contradiction, but it exposed a deeper comparator problem: a frozen **two-root** portfolio is not necessarily the strongest observed ownership control for a **three-cluster** family. The synthetic root barely crossed materiality against two roots, while the low consensus predictor correctly recognized the family as multimodal. A three-observed-root control is the obvious causal alternative and was not included.

Therefore O1b is a genuine negative against the frozen test, but it does not justify tuning the predictor. More importantly, it reinforces the anti-Goodhart lesson: “strongest observed control” must be structurally matched rather than capped at an arbitrary root count.

No O1c is authorized. The stronger inherited R4 result already retires this mechanism family at representative product scale: explicit latent consensus lost its optimistic payload floor to solid Zstd-19 by 48,362 B and was ~15.8x slower to create. Generating a three-root synthetic follow-up would be below-MRS threshold gardening, not frontier work.