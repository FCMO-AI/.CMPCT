# Authority-v2 runtime owner diagnosis — 2026-09-15

**Scope:** diagnosis of preserved exact-head runtime evidence from authority-v2 run `34919975890`. This note does not change a benchmark threshold, product byte, release gate, or release claim.

## Direct evidence inspected

The failed runtime artifact `10377997083` contains both `runtime-v2.json` and `runtime-tree-rss.json`. The latter measures whole process-tree RSS and is the correct custody surface for child-process-heavy creation.

## What is actually red

Whole-process-tree evidence shows peak RSS is **not** the current blocker. Maximum v0.30/v0.29 pack-RSS ratios are shifted `0.9538x`, logs `0.6295x`, ML `0.7297x`; the aggregate peak ratio is `1.0x`, within the frozen `1.25x` ceiling. The parent-only receipt's shifted `2.1099x` signal is therefore a measurement-custody artifact, not a product RSS regression.

Runtime debt is concentrated in two rows:

- `09_ml_artifacts`, selected `geometry-g04`: median create `1.4162x` (`~37.9 s` v0.30 vs `~27.3 s` v0.29) and median extract `2.0339x` (`~0.181 s` vs `~0.090 s`). It violates both `1.25x` per-workload ceilings. The row still saves about `161.6 KiB`, so deleting G04 merely to turn the runtime matrix green would discard material byte value rather than rehabilitate the mechanism.
- `05_logs_and_telemetry`: median create is `~0.0085x`, but extract is `1.3342x` (`~0.051 s` vs `~0.038 s`). This violates the per-workload extract ceiling and drives the three-row median extract ratio to `1.3342x`, above the frozen `1.10x` ceiling. The exact byte margin is only about `264 B` in this receipt, so carrying-cost/admission deserves explicit scrutiny if the extraction debt cannot be removed cheaply.
- `01_shifted_versions` is not a runtime blocker in the process-tree receipt: create `1.0585x`, extract `0.9101x`, RSS `0.9538x`.

All three measured rows remained byte-nonregressing.

## Existing extraction decomposition narrows the owner

The preserved G04 extraction-cost receipt from run `34823485696`, artifact `10338664126`, is research/oracle evidence on the same canonical ML workload. Its three fresh-process medians were: strong verify `0.14683 s`, verified staging `0.14828 s`, full extract `0.16061 s`. Thus strong verification / authenticated G04 decode accounts for about `91.4%` of full extraction wall time in that receipt; physical staging adds only about `1.46 ms`, and the remaining restoration/publication layer about `12.33 ms`.

That independently explains why verified-restore syscall fusion was correctly retired: the measured restore layer is too small to close an approximately `90 ms` v0.30-vs-v0.29 ML extraction gap. The next extraction intervention belongs inside authenticated G04 verification/reconstruction unless newer evidence contradicts this decomposition.

## Profiler route correction to test, not assume

The older `benchmarks/v030_g04_ml_extract_cprofile.py` wraps shipping `PRODUCT.build()` / `PRODUCT.extract()` calls in the private `PRODUCT.C._revision25_profile_context()`, while the authoritative fresh-process worker calls the shipping product front door directly. Its preserved 15-minute checkpoint never advanced beyond `shipping_build_started`, whereas authority-v2 builds ML in tens of seconds. That discrepancy proves the old profiler does not currently provide extraction ownership evidence; it does **not by itself prove** which setup detail caused the stall.

A separate shipping-route profiler now exists specifically to test the unwrapped product front door while preserving exact G04 selection and strong tree identity. Until it lands a valid profile, treat function-level extraction ownership below the strong-verify layer as unknown. cProfile wall time itself receives no release credit.

## ML creation owner from authority build stats

The same authority receipt also narrows creation without a new timing boundary. The ML shared v0.29/attempt5 candidate build is about `26.46 s`, essentially the same scale as the v0.29 product's `~26.5 s`; complete v0.30 creation is about `37.2–37.6 s`. The extra `~10.7 s` is therefore downstream of the shared base candidate and associated with the G04 overlay/tournament/publication path, not the inherited v0.29 base build.

The selected G04 overlay transforms 9 physical records (8 lane + 1 delimiter) and buys about `161.8 KiB`. Any creation optimization must preserve that exact byte result/locality or prove a stronger complete-product trade; skipping G04 wholesale is not rehabilitation.

## Derived minimum rehabilitation bounds

The frozen aggregate and per-workload gates interact; clearing each red row to merely `1.25x` is not sufficient. Using the exact whole-tree receipt medians:

- ML create must fall from `37.89634 s` to at most `33.44985 s` to satisfy its `1.25x` row ceiling: at least `4.44649 s` / `11.73%` of current ML creation must be removed or overlapped.
- ML extract must fall from `0.181171 s` to at most `0.111342 s`: at least `69.83 ms` / `38.54%` of current ML extraction must be recovered.
- Logs extract needs only `3.22 ms` / `6.31%` recovery to cross its own `1.25x` row ceiling, **but that would still leave the three-row median extract above the frozen `1.10x` aggregate ceiling** because Shifted is the only already-green ratio below `1.10x`.
- If ML remains above `1.10x`, Logs must therefore reach at most `1.10x`, or `0.042112 s` against its `0.038283 s` v0.29 control. That requires about `8.97 ms` / `17.56%` recovery from the current `0.051079 s` Logs median. Conversely, a sub-`1.10x` ML extraction could carry a Logs result between `1.10x` and `1.25x`, but current evidence makes that the harder route.

This matters for mechanism selection: a Logs idea with a credible 4–7% complete-extraction win can clear the local row yet still fail the release receipt. The current planning target should be the stronger aggregate-aware bound unless another row is independently driven below `1.10x`. Thresholds are not being changed; this is a derivation from the existing frozen thresholds.

## Next falsifiable actions

1. Harvest the shipping-route ML extraction profile and use function-level ownership to attack the authenticated verify/reconstruction layer; do not reopen restore-syscall fusion.
2. Attribute the `~10.7 s` post-shared-build ML creation cost inside G04 audition/overlay/publication before changing admission or parallelism.
3. Keep logs extraction independent: its `~1.334x` debt and tiny byte margin make carrying-cost/admission a separate decision, not evidence that an ML fix will transfer. Prefer mechanisms with plausible `>=17.6%` complete-extraction headroom unless ML is independently brought below `1.10x`.

`runtime-memory-selective` remains open and v0.30 remains merge/release locked.