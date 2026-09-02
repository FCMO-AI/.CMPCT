# r24 worker-policy propagation causal A/B v2 — result

Status: **ACCEPTED DIAGNOSTIC CAUSAL EVIDENCE / FORGE-CUSTODY / NO RELEASE CREDIT**

This record preserves the exact result of the frozen superseding experiment in `R25_R24_WORKER_POLICY_PROPAGATION_V2_PREREG.md`. It does not change production behavior or release authority.

## Provenance

- authoritative branch: `agent/v030-authoritative-integration`
- exact experiment source: `2c95f2a935169f7a7a2480b316c9d2b4291a9ea6`
- workflow: `CMPCT v0.30 r24 worker-policy propagation causal v2`
- run: `33634652807`
- substantive job: `100263316089` (`worker-policy-v2`)
- artifact: `v030-r24-worker-policy-propagation-v2-2c95f2a935169f7a7a2480b316c9d2b4291a9ea6`
- artifact id: `9848385001`
- upload digest: `sha256:842c2795808e245f9a6026d3d549541b8aef1c156ff6b28ba6620cd83b94ef61`
- schema: `cmpct-v030-r24-worker-policy-propagation-v2`
- Python: 3.11.16
- runner: Ubuntu 24.04 hosted runner
- all arms strongly verified: true
- one logical tree across all arms: true
- each arm repeatable across all three rounds: true
- release credit: false

## Exact result

Target: `resemblance_hostile_v1 / 01_shifted_versions`.

| arm | encoder workers | dictionary state | complete archive | median peak RSS | median wall time |
|---|---:|---|---:|---:|---:|
| inherited shipping r24 | 4 | `dictionary-dead` | **30,275,603 B** | **283,584 KiB** | **0.376824 s** |
| one-worker control | 1 | `dictionary-live` | **29,883,734 B** | **209,132 KiB** | **0.667435 s** |
| propagated release policy | 4 | `dictionary-live` | **29,883,734 B** | **239,024 KiB** | **0.443203 s** |

Frozen terminal decision: **`THREAD_LOCAL_POLICY_LEAK_CAUSAL`**.

The four-worker propagated arm and one-worker control were exact on complete archive bytes, archive SHA-256, canonical logical tree and stable build statistics. The inherited four-worker arm was byte-distinct while reconstructing the same strongly verified tree. The predicted dictionary-state transition occurred exactly: inherited `dictionary-dead`; single and propagated `dictionary-live`.

Relative to inherited shipping r24, the propagated diagnostic arm:

- stores **391,869 B fewer bytes** (about **1.294%** smaller);
- reduces median total fresh-process peak RSS from 283,584 to 239,024 KiB, a **44,560 KiB / 15.713%** reduction;
- increases median wall time from 0.376824 s to 0.443203 s, a **1.17615x / 17.615%** slowdown;
- retains four encoder workers and therefore avoids the one-worker control's much larger **1.771x** wall-time cost.

These performance numbers describe the diagnostic arm only. They are not a release-runtime receipt.

## Causal interpretation

The v1 worker-count A/B correctly failed exact-output identity. V2 explains why.

The release r24 path enables medium-binary (`.bin`) text/dictionary eligibility through `_ReleaseTextHints`, whose release-policy state is stored in `threading.local()`. The Builder performs dictionary training and other parent-thread work while that policy is active, then dispatches `_encode_candidate()` into a `ThreadPoolExecutor`. Those encoder workers do not inherit the parent thread-local flag. `_encode_candidate()` re-evaluates `TEXT_EXT` inside those workers, so the trained dictionary is not auditioned for `.bin` candidates there. The resulting dictionary becomes physically dead and is elided.

The one-worker path never crosses a thread boundary, so it sees the active release eligibility and uses the dictionary. V2's propagated arm changes only this visibility inside an isolated diagnostic process. Its exact equality with the one-worker result establishes the thread-local policy leak as the byte-drift cause under this tested regime.

This falsifies the Builder comment/invariant that worker scheduling alone cannot perturb final bytes **when encoder behavior depends on thread-local policy queried inside worker threads**. Ordered `Executor.map` is sufficient for deterministic materialization order, but it is not sufficient for semantic determinism if the workers observe different policy state.

## Product implication

This is not merely a test-infrastructure defect. On the measured Shifted r24 fallback path, the current parallel shipping behavior pays **391,869 unnecessary bytes** because policy visibility changes across worker boundaries. Repairing that defect can therefore improve determinism and compression simultaneously.

The production repair must not copy V2's diagnostic process-global `TEXT_EXT` substitution. CMPCT already rejected process-global canonical-profile mutation because concurrent research callers can observe it. The lowest-sufficient production intervention is to make the encoding decision depend on immutable operation-scoped state captured before thread dispatch, or otherwise propagate the already-selected release policy into each worker without exposing mutable process-global semantics.

The 17.6% diagnostic create-time slowdown remains explicit debt. It may reflect actual dictionary compression work that the inherited bug accidentally skipped. A production repair is not promotable merely because it restores the smaller bytes; it must survive the exact full runtime/product gates.

## Reopening / negative constraints

Do not reinterpret v1's 26.29% single-worker RSS reduction as evidence that single-threaded shipping is the right fix. V1 compared different archives and therefore cannot justify a scheduler change.

Do not preserve the inherited four-worker bytes as the canonical answer merely because they are faster. The faster path is semantically inconsistent with the release policy already active in its parent thread and violates the repository's worker-count determinism claim.

Reopen a different cause for this exact byte drift only if a new experiment shows that operation-scoped policy propagation no longer reproduces the one-worker artifact exactly, the Builder/release policy materially changes, or independent evidence identifies another state difference sufficient to explain the same complete-byte delta.

## Forge decision

**`PROMOTE_NEXT_PREREQUISITE`**: implement the smallest operation-scoped worker-policy propagation repair, then require a one-worker-versus-N-worker exact-byte regression and rerun the full genuine-r24/r25 product, size, runtime/RSS, locality, recovery, native/platform and release authorities. No benchmark threshold or invariant changes.
