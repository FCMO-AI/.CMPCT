# J24R04c — Correct untimed sparse boundary probes without changing the ABBA measurement

**2026-10-27 UTC — prospective freeze before patch / new hosted result.** This is an evidence-enablement change on the existing *draft* J24R04 product candidate PR #596, not a new product mechanism or release proposal.

## Reconciled repository/ownership truth

Published v0.30.0/r24 remains on main; unmerged J24R04 #596 at `53d87bc3741164d9b0463409a5057f129a4284e7` holds the sole short-vector dual-path Reader mutation, based on J24R01 #584 `70336307312b5b277f0885c0057d2cddab0aefc1`, compared with composed J24C02 #569 `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`. The three-host source-exact functional court of Actions #40505113816 is green. Its *distinct* Ubuntu triple-Reader ABBA job failed before any measurement. The first attempt hid subprocess stderr; J24R04b installed a diagnostic-only wrapper. The second execution #40505113816, job 122192715492 reveals the genuine original Reader correctly rejected `read_range(start=8,length=-4)` for a four-byte, one-extent synthetic archive.

This is an inherited **untimed instrument fault**, not product failure: the source `research/j24r01_sparse_range_abba.py` iterates `pos=8` when `len(truth)=4` and constructs `min(11,len(truth)-pos)=-4`. It erroneously counts 21 post-checks in all profiles. J24R02 PR #586 already repaired this *same narrow issue* and produced successful hosted source-exact 48-observation evidence; its corrected script blob is `dea2ec48af7d7c5fad0dcec92e84c12124300967` (original #584 script `617bd1edd2acf04a1f94b7807d732256709a6dda`). Do not duplicate scientific policy or rewrite historical J24R01.

## Hypothesis and exact minimal permitted change

Reuse the **byte-for-byte validated J24R02 script** under a new J24R04c filename while leaving the frozen parent script unchanged. It clamps the lone E=1 post-probe `8` to member length and counts only genuinely issued strict-in-bounds checks. It does **not** change fixtures, ABBA order, number of independent processes, original-vs-candidate sources, 256 untimed warm-up ranges, 256 timed ranges, clock boundaries, cache/open costs, repetitions, or source identity.

Update the J24R04 workflow to invoke only this inherited corrected instrument (two control arms), and make the independent receipt referee require exactly **531 checks for E=1** and **533 for E=4/4096/65536**. Preserve all structural/Git/SHA, numeric, median, binary truth, archived physical byte, source provenance and tamper-refusal checks. Add frozen donor Git blob identity in workflow; don't rerun the invalid original instrument and don't silently relabel its failure.

## Prospective decision and kill conditions

Run source-exact two-control ABBA: original #569 vs dual #596 and unconditional bisect #584 vs dual #596, three ABBA rounds, four E profiles per arm, **96 fresh-child observations**. Referee must independently recompute medians and evaluate the *originally frozen* thresholds: small E=1/4 candidate within 5% of authentic linear, E=4096/65536 >=10x faster than linear, and high E within 5% of unconditional #584. Mismatched source, wrong bytes, archived byte drift, extra/missing processes, post-check drift, changed timed workload, invalid receipt, or failure to reject tampering invalidates the experiment. A measured slowdown remains a true negative, never adjusted into passing.

Success of infrastructure repair only earns **evidence readiness**. Even scientific PASS earns no general product/release claim without complete end-to-end parity/hostile/open/memory/portability tests. Retain the first two negative workflow runs and published older J24R02 evidence, including E=1/4 regressions of unconditional bisect. Never modify discovery state or its #574 owner. The current concurrent owner of Reader #569 and parent #584 remain untouched.

## Alternative explanations and counterfactual

This invalid check was prospectively catchable by deriving bounds for the minimum one-extent fixture before dispatch; reading a hidden stderr was the cheapest discriminator. Reusing the *already successful* corrected producer is stronger/cheaper than introducing a third independent ad hoc producer. This isolated evidence repair may also reveal a genuine negative for J24R04 dual path; if so, preserve the raw data and narrow/retire rather than gardening the E<=4 cutoff.

## Concurrency and release

No claims or locks on other branches, no changes to frozen original scripts, validators, benchmark comparator thresholds, payload bytes, Reader code, format, 0.30 release, or unrelated repos. Shared `docs/discovery/STATE.json` is stale and owned by draft #574. Stop this lane on outcome and hand back source-exact measurements to #584. **No merge, release, promotion or policy modification.**
