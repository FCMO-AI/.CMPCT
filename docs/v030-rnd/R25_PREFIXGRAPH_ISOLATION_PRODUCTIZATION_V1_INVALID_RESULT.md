# PrefixGraph Builder isolation productization v1 invalid result

Status: **INVALID EXPERIMENT / ENTRY-SURFACE MISMATCH / ZERO SCIENTIFIC OR RELEASE CREDIT**

This record preserves the first execution of the frozen S6 Builder-isolation transfer instrument. The run produced repeatable, strongly verified control/candidate archives and a large apparent memory effect, but it entered the canonical-final facade directly rather than the promoted release-product front door. That bypassed the release-only r24 policy transport and therefore violated the frozen exact-r24 identity gate. The run is invalid for the S6 terminal decision and must never be promoted as product evidence.

## Authority

- branch: `agent/v030-authoritative-integration`
- exact source: `7a58e28a6bd6890f993e54f787455bd3a9e4da3c`
- workflow: `CMPCT v0.30 PrefixGraph isolation Builder hostile review`
- run: `33694108062`
- substantive job: `100459978171`
- artifact id: `9871380432`
- artifact: `v030-prefixgraph-isolation-productization-7a58e28a6bd6890f993e54f787455bd3a9e4da3c`
- artifact digest: `sha256:92faaed3051dd21cce07772cac345118dbcf0912df566dce842220a6095ccd40`
- result schema: `cmpct-v030-prefixgraph-isolation-productization-v1`
- `experiment_valid=false`
- terminal decision: `INVALID_EXPERIMENT`
- release credit: **false**

The measurement step failed closed after writing the invalid receipt. CI topology and public-surface guards then passed, and the exact artifact was uploaded.

## Observed but non-authoritative signal

| Arm | Median whole-process-tree peak RSS | Median wall | Final archive |
|---|---:|---:|---:|
| threaded control | **389,076 KiB** | **36.22755 s** | **1,700,603 B** |
| integrated level-15 isolation | **224,918 KiB** | **37.41439 s** | **1,700,666 B** |

The apparent diagnostic deltas are approximately:

- whole-process-tree RSS: **42.19% lower**;
- wall ratio: **1.03276x**;
- final selected artifact: **+63 B**.

Both arms were deterministic within the two alternating repetitions and reconstructed the exact canonical user tree. The candidate also exercised exactly one audited process executor and the child was dead when synchronous submission returned.

These numbers are retained only as an invalid-run debugging signal. They do not satisfy or alter any frozen S6 threshold.

## Exact invalidity

The frozen S6 contract requires the genuine repaired shipping r24 floor to remain exactly **29,883,732 B**. Both arms instead produced `r24_product_bytes=30,275,591`.

Cause: the v1 worker imported and called `experiments.entropygraph_v030_canonical_final.build` directly. The shipping/runtime authority enters through `experiments.entropygraph_v030_release_product`, whose import and front-door path install the release-owned operation-scoped r24 policy and canonical bindings. Direct canonical-final entry therefore measured the historical dictionary-dead r24 semantic regime rather than the promoted product boundary.

This is an evidence-instrument error, not permission to change the r24 floor and not evidence against the process-isolation mechanism.

## Superseding execution

The worker was repaired in commit `83388672a4d267b101a8490e67cf11d3fe257268` to import and execute the promoted release-product front door first while preserving the exact same S6 control/candidate intervention and thresholds. The superseding run must independently satisfy the fixed `29,883,732 B` r24 identity before any RSS/wall/size result can receive S6 authority.

Do not combine or average this invalid run with the superseding run. The only allowed use of these measurements is debugging the invalid entry surface and checking whether the direction of effect is plausibly reproduced after exact identity is restored.
