# J24M01f-b — correction of an overstrong positive-control parent-highwater equality (2026-10-29 UTC)

**CORRECTION PREREGISTERED AFTER ORIGINAL NEGATIVE, BEFORE EDITING SCIENTIFIC CONTROL.** Do not replace or erase original result.

## Exact original red / why it matters

Original exact-head candidate `035868a6d1ecfaf8f0fc6a3c102a6121b1423ef0` in [J24M01f complete-suite run #40907740111](https://github.com/FCMO-AI/.CMPCT/actions/runs/40907740111) returned **796 passed / 5 failed** with actual original pytest exit code **1**. Crucially, the formerly failing *real 256-MiB sparse verifier test passed* at the unchanged strict `<128*1024 KiB` limit and verified genuine sparse input. Four original historical release/fingerprint tests remain failed, as required.

The fifth failure was the newly added independent kernel control's **incorrect extra identity assertion** `assert inherited_kib >= parent_kib`. It observed:
- `parent_peak_kib=178792`;
- `child.ru_maxrss_kib=175312`;
- `child.vmhwm_kib=11012`.

The old assertion failed because 175312 < 178792 by 3480 KiB, even though the directly relevant causal discriminator was extremely positive: the *child's own reported ru_maxrss* exceeds its post-exec VmHWM by **164300 KiB**. This negative is not rewritten. The physical/accounting reason for the 3480 KiB mismatch is uncertain: parent vs child kernel RUSAGE historical accounting is not an exact equality contract. The upstream no-CMPCT J24M01e source-locked independent control already showed the discrepancy class; this correction eliminates an unjustified exact-magnitude dependency, not the measured high-water divergence.

## Revised falsifiable control / harder than a mere delta check

The positive control must independently prove:
1. the parent actually touched >=160 MiB anonymous memory and reached `parent_peak_kib >=160*1024`, as before;
2. the execed child's reported inherited `ru_maxrss_kib >=160*1024`, a large carried high water that cannot be explained by a small interpreter, **new requirement**;
3. the child actual `VmHWM` is positive and **strictly <128*1024 KiB**, a bounded process-local memory control, **new requirement**;
4. child's `ru_maxrss - VmHWM >=32*1024 KiB`, as before;
5. fail closed on missing/malformed kernel fields or subprocess failures as before.

We remove only `assert inherited_kib >= parent_kib`, which was scientifically unnecessary; it incorrectly required the kernel to report a child's inherited accounting as an exact monotone extension of the measured parent **ru_maxrss**. No modification to the user-data resource threshold, real sparse workload, Reader, Builder, ZIP parity, format, release tests, or any original 4 historical failures. If the above stricter causal conditions fail, scientific court remains negative.

## Next evidence
Reexecute the full suite and independent focused job on the **new exact HEAD**, preserve their original pytest return codes and original artifacts. The only success claim authorized is attribution accuracy of the test under source-locked Ubuntu; no product merge/release or stage publication safety qualification. J24G33 inherited workflow source-pin mismatch remains an independent CI/evidence routing debt.
