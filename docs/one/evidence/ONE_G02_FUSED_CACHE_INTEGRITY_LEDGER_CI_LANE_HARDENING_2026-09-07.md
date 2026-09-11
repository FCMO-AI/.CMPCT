# ONE-G0.2 fused-cache integrity-ledger CI-lane hardening — 2026-09-07

## Mission Lock / Referee

The fused-observation cache cost ledger is research evidence only if its dedicated lane executes the repository test contract against the exact evidence head and propagates benchmark failures. A red lane caused by missing test provisioning is infrastructure evidence, not a scientific falsification; conversely, a green lane that tests a different checkout or masks a failed pipe is not admissible promotion evidence.

Falsifiable hypothesis: after aligning this lane with the repository-established ONE workflow contract, the hostile ledger tests and deterministic integrity audit will execute against the exact triggering head. If they still fail, the failure becomes scientific/test evidence to investigate rather than being attributed to lane plumbing.

Disproof: an exact-head, fully provisioned rerun fails the hostile tests or deterministic audit. In that case the cache/ledger hypothesis remains red until the assertion or audit discrepancy is causally resolved; do not weaken gates.

## Observed failure

Dedicated workflow run `34154780148` on source head `c75e1f630c78c684cd12f13a69cdc5d04e9f9dca` concluded failure.

The Actions job metadata localizes the failure to `Run hostile ledger tests`. Checkout and Python setup completed; the subsequent deterministic integrity audit and artifact-producing path did not execute to completion, and no audit artifact was available from that run.

The exact stderr for the failed test step was not retrievable through the available connector/runtime, so this receipt does **not** claim a specific missing-module exception as observed fact.

Static comparison with neighboring current ONE workflows nevertheless exposed concrete lane defects:

- no repository test-extra provisioning before invoking `python -m pytest`;
- no explicit exact-evidence-head checkout/binding;
- no `pull_request` path trigger matching the same research surface;
- no `set -o pipefail` around the benchmark-to-artifact pipeline;
- no explicit fast-lane classifier tag used by neighboring ONE research workflows.

Those omissions make the old red result ambiguous and therefore unsuitable as scientific evidence.

## Builder change

Commit `43ce46719496c136b46a27e6d57c31b5a23928d7` hardens `.github/workflows/cmpct1-one-g02-fused-cache-integrity-ledger.yml` to:

1. bind `EVIDENCE_HEAD` to the pull-request head or triggering SHA;
2. checkout exactly that SHA and assert `git rev-parse HEAD == EVIDENCE_HEAD`;
3. provision `-e '.[test]'` before running pytest;
4. preserve the hostile ledger and fused-cache test surface;
5. run the deterministic audit under `set -o pipefail`;
6. retain the audit JSON with the exact evidence head in the artifact name;
7. expose matching pull-request path coverage and the repository fast-lane tag.

No cache algorithm, ONE representation, threshold, semantic gate, benchmark input, or comparator was changed.

## Hostile Reviewer

This repair does not turn the previous failure into a pass. It only removes known ambiguity from the evidence lane. The exact-head rerun is authoritative.

If the hardened lane is green, the result establishes that the ledger tests/audit execute correctly under the repository test contract; it does not establish a writer-speed win.

If the hardened lane is red, retrieve the actual assertion/audit failure and repair or reject the scientific mechanism. Do not respond by weakening integrity accounting or performance thresholds.

There is also research-efficiency debt here: an under-provisioned dedicated lane consumed scheduler/CI capacity while producing an uninterpretable red signal. Future experiment-specific workflows should inherit the exact-head/provisioning/pipefail pattern at creation time rather than rediscovering it after a failed run.

## Representation and comparator impact

- Canonical ONE stored bytes: unchanged.
- Law + Surprise semantics: unchanged.
- Reader discovery/complexity: unchanged.
- Decode/access/reconstruction/failure-blast-radius behavior: unchanged.
- Frozen v0.29 and deferred-v0.30 authorities: unchanged.
- Genesis scoreboard: no point earned.

## Next decisive action

Consume the hardened exact-head run. If it passes, retain the deterministic ledger artifact and proceed to cost-owner decomposition across current-content validation SHA, cached-state seal verification, new seal construction, cached-feature traffic, exact reuse proof, and changed-block recomputation before attempting a full writer/ingest A/B. If it fails, treat the first exact failing assertion/audit delta as the next research target.
