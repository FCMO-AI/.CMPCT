# v0.30 current15 deterministic substrate result — 2026-09-13

Status: **research substrate rehabilitated; no release credit; no Genesis rescore**

## Mission

Make the current 15-workload research surface reusable across independent hosted runs without weakening the same-input rule.  Earlier density and selective-read runs were internally fair because each A/B comparison shared one generated tree, but cross-run composition was invalid because the portfolio fingerprint drifted.

The acceptance condition was byte-level: two immediate builds on one exact runner must produce 15/15 identical workload tree hashes and one identical portfolio fingerprint.  Fixing benchmark identity must not change CMPCT encoder policy, thresholds, locality, integrity, recovery, or comparator settings.

## Causal diagnosis

The first back-to-back referee isolated three neutral workloads with wall-clock/container drift:

- Office
- Logs and Telemetry
- Incremental Backups

The stable wrapper fixed ZIP/OOXML core-property timestamps, GZIP `mtime`, and the backup ZIP.  That reduced the instability from three workloads to **Office only**.

Two narrower hypotheses were then falsified:

1. setting ReportLab `rl_config.invariant = 1` globally did **not** stabilize Office;
2. forcing `Canvas(..., invariant=1)` explicitly also did **not** stabilize Office.

The byte-attribution referee isolated exactly one changing file, `client_report.pdf`, with the first difference at byte **471,188**.  The surrounding PDF bytes showed a ReportLab image XObject name changing between builds:

- `FormXob.234cfdd5...`
- `FormXob.43fc4d24...`

The two builds live under different benchmark work roots.  ReportLab names an image XObject from the filename string when `drawImage` receives a path, so identical image pixels at different absolute paths receive different internal PDF names.  Passing an `ImageReader` instead makes the XObject identity derive from image content.  The deterministic wrapper therefore converts path-like `drawImage` inputs to `ImageReader` while leaving the rendered image unchanged.

## Accepted stability evidence

Exact substrate-fix commit:

`f5b14b5c4c60644874cd9e99cb7a515e66d8ba62`

Hosted stability run:

`34745122950`

Receipt artifact:

`v030-fp-stable-n0-none-offnone-anone-bnone-40df619da5-40df619da5-f5b14b5c4c60644874cd9e99cb7a515e66d8ba62`

Result:

- builds A/B: 15 workloads each;
- unstable workloads: **0**;
- fingerprint A: prefix `40df619da5`;
- fingerprint B: prefix `40df619da5`;
- scientific verdict: **CURRENT15_FINGERPRINT_STABLE**.

## First evidence rehabilitated on the stable fingerprint

Content-economic current15 density run `34745122941` used the same stable substrate and emitted fingerprint prefix `40df619da552`:

- completed: **15/15**;
- stored-byte delta vs same-grammar independent: **-796,830 B**;
- stored-byte delta vs extension-bucket control: **-378,545 B**;
- workload economics: **8 strict wins / 7 exact ties / 0 losses**;
- locality/invariant losses: **0**;
- maximum decode unit: **938,064 B**;
- maximum member amplification: **8.0x**.

Content-economic current15 selective-read run `34745122943` also emitted fingerprint prefix `40df619da5` and therefore shares the now-reproducible input identity.  It preserved all invariants but exposed three confirmed timing debts; those debts remain active research blockers rather than being hidden by the substrate repair.

## Interpretation

The substrate repair does **not** improve CMPCT compression.  Its value is epistemic: density, selective-read, memory and future composition receipts can now be compared across independent runs without silently changing Office bytes.

Historical current15 runs with other fingerprint prefixes remain useful within-run A/B evidence but must not be arithmetically composed with the stable `40df619da5...` frontier.

Genesis remains frozen exactly as adjudicated on 2026-09-11.  This result neither reruns nor changes ONE, v0.29, or the frozen v0.30 Genesis score.
