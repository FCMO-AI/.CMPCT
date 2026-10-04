# PrefixGraph isolation + level-15 productization gate v2 — result

Status: **COMPLETE / FORGE S6 BUILDER SUPPORTED / ZERO RELEASE CREDIT**

Frozen authority: `docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_V2_PREREG.md`.

## Exact evidence

- source commit: `ee7fb2bb5ca7eb685c1f8c11be37cc04d354720a`;
- GitHub Actions run: `33727694904`;
- substantive job: `100560378734` (`hostile-review-v2`);
- artifact id: `9882714798`;
- artifact name: `v030-prefixgraph-isolation-productization-v2-ee7fb2bb5ca7eb685c1f8c11be37cc04d354720a`;
- artifact ZIP digest: `sha256:7b0fa3721d03a81b5651ff54ae129385100ed70a9705ad0e32a4761fa9ca07b8`;
- runner: hosted Ubuntu 24.04, Python 3.11.16;
- experiment validity: `true`;
- frozen terminal decision: **`PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED`**.

This receipt is the superseding mtime-stable S6 Builder-vs-threaded-control experiment. The original v1 receipt remains immutable and invalid for productization because its frozen genuine-r24 fingerprint was stale. No v1 threshold, result or identity was rewritten.

## Frozen genuine-r24 custody

The v2 fixture normalized only atime and mtime as preregistered. Every measured repetition produced the exact preflight identity:

- genuine-r24 bytes: **29,883,488 B**;
- genuine-r24 SHA-256: `a3192a1462e37282e5128e50c3b20a039ca26821d5ceb2508958d6e3918bbc22`.

The identity matched between control and candidate and the experiment reported no worker failure.

## Decisive Builder result

Two alternating rounds per arm produced these medians:

| arm | r25 bytes | whole-process-tree peak RSS | parent `ru_maxrss` diagnostic | wall |
|---|---:|---:|---:|---:|
| threaded level-19 control | **1,700,531 B** | **368,110 KiB** | 367,922 KiB | **48.6507572035 s** |
| process-isolated level-15 Builder | **1,700,594 B** | **259,418 KiB** | 325,536 KiB | **52.0816314795 s** |

Derived frozen quantities:

- decisive whole-process-tree RSS reduction: **29.5270435468%**;
- candidate wall ratio: **1.07052047025x**;
- selected-artifact size penalty: **+63 B**;
- selected-artifact size penalty ratio: **0.00370472517%**;
- deterministic bytes within each arm: **true**;
- byte budget: **pass**;
- hostile helper fail-closed contract: **pass**.

The candidate therefore clears all immutable S6 gates:

- RSS reduction >=20%: **pass**;
- wall ratio <=1.10x: **pass**;
- size debt <=8,192 B and <=0.50%: **pass**;
- exact r24 identity: **pass**;
- deterministic arm bytes: **pass**;
- PrefixGraph selection/lifecycle requirements: **pass under the frozen oracle**;
- exactly one bounded level-15 child, dead before G0-G4 continuation: **pass under the frozen oracle**;
- hostile malformed/wrong-owner/helper-failure behavior: **pass**.

## Forge interpretation

This closes the strongest surviving objection to the process-lifetime rehabilitation. The memory win survives the strengthened whole-process-tree sampler that retains descendant high-water contribution after child exit. The mechanism therefore does not merely hide the large PrefixGraph workspace in a short-lived process.

The prior v1 descriptive run had shown a ~28.86% whole-tree reduction but a 1.118x wall ratio. Under the causally corrected mtime-stable v2 fixture, the same mechanism reproduced a slightly larger **29.53%** RSS reduction while wall debt fell inside the frozen **1.10x** ceiling at **1.0705x**. This is sufficient S6 Builder evidence; further launcher tuning is not justified before broader D5 productization evidence shows a real remaining debt.

## Scope and carrying cost

This result proves the mechanism at the frozen Shifted Builder boundary only. It does **not** prove general release performance and grants zero release credit by design.

The mechanism still owes the preregistered productization vector:

- complete frozen product-size/runtime/RSS/selective-read matrix;
- recovery, integrity, hostile-input and resource checks;
- Python concurrency/profile-isolation review;
- Windows and macOS subprocess/path/atomic-cleanup evidence;
- Android/constrained-host feasibility under existing release law;
- native/reader/platform authority where implicated;
- exact current-fingerprint competitor authority;
- final strict release lock.

Its permanent carrying cost must include the bounded child-process executor, temporary artifact/receipt custody, one extra interpreter process on eligible PrefixGraph builds, cross-platform subprocess semantics and the requirement that non-applicable/failure cases retain safe fallback behavior. No global native/parser/format grammar was added by this mechanism.

## Negative constraints / reopening law

Do not reopen the already-retired nearby families merely because this mechanism succeeded:

- lower Zstd levels alone did not materially reduce PrefixGraph RSS;
- fresh-CCtx-per-member did not recover the workspace and was much slower;
- precomputed CDict worsened RSS.

Those scoped negatives remain in force. Reopening requires new causal evidence or a materially different runtime/library regime.

## Terminal decision

**`PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED`**

Forge state transition: the Shifted process-isolation mechanism moves from `REHABILITATION` to **D5 `CONVERGENCE`**. Preserve the exact supported mechanism and advance its exported product/platform debts. Do not tune away the measured ~29.53% RSS gain and do not weaken any release gate.

## Next decisive action

Run the exact current-fingerprint complete runtime/RSS/selective-read and recovery/platform authorities with the integrated Builder path. A failure outside the frozen S6 boundary becomes explicit rehabilitation/productization debt; a green must remain fingerprint-bound and cannot inherit release credit from this diagnostic receipt.
