# O92b — Clean-installed import-only RSS result

Date: 2026-10-25 UTC

## Direct source-locked evidence

Prospective preregistration `cbb93860f6861f71ae48c1623b525f9405de5559` preceded instrument and execution. O92b genuine Ubuntu Actions [#40210747808](https://github.com/FCMO-AI/.CMPCT/actions/runs/40210747808), instrument HEAD `f7891d6fc9eef5167b92081925b9280f0dadc96d`, **SUCCESS**; six independent original-installed O63/O86 children, 3 per arm, no failed/skipped subprocesses. All installed Builder/codec Git blobs checked. Original raw artifact [#12605806189](https://github.com/FCMO-AI/.CMPCT/actions/runs/40210747808/artifacts/12605806189), `sha256:721da4708c4d24dc9e6637026be8500c40af4b3eb2929964ef045f9d268a9ca3`.

## Measurements: fresh child process (median 3 × per arm), KiB

| Checkpoint | O63 ru_maxrss | O63 current VmRSS | O86 ru_maxrss | O86 current VmRSS |
| --- | ---: | ---: | ---: | ---: |
| Pure Python measurement harness, **before cmpct import** | 19,728 | 18,460 | 19,728 | 18,396 |
| After `import cmpct` | 22,988 | 23,032 | 22,920 | 22,972 |
| After `cmpct.builder` import | 22,988 | 23,036 | 22,920 | 22,976 |
| After `cmpct.codec` import | 22,988 | 23,036 | 22,920 | 22,976 |
| After `cmpct.reader` import | 23,116 | 23,144 | 23,048 | 23,084 |
| After `cmpct.native_codec` import | 23,116 | 23,148 | 23,048 | 23,092 |

The first `import cmpct` transitively imports the release hooks and Builder/codec, so individual subsequent import rows are **not** standalone per-module cost measurements. The final O63/O86 process-live RSS difference is small; do not call it a product-level performance win.

## Decision and negative evidence

**The hypothesis that ordinary CMPCT import creates the ~300,348 KiB O92 pre-Builder peak is FALSIFIED.** Both genuine installed histories import with roughly 23 MiB live/current and process high-water RSS on this control. The original O92 300 MiB phenomenon must arise from work **outside ordinary clean `cmpct` import** (possibly fixture/harness or the inherited process-resource witness), not from this package initialization in isolation.

Cross-evidence discrepancy was preserved rather than explaining it away. In a separate *non-hosted* independent Linux process-control, a parent allocating/freeing a 300 MiB bytearray reported `resource.ru_maxrss=402312 KiB`; its fresh `subprocess` child printed the **same** ru_maxrss `402312 KiB`, while the child's `/proc/self/status VmHWM` was only `95368 KiB`. This is a lower-rung **environmental primitive observation**, not an O92b hosted product result. It strongly suggests Linux `resource.getrusage` may preserve inherited parent high-water **across subprocess creation and exec** under this execution boundary. Test it under the exact hosted O88/O92 conditions before a causal correction is promoted.

## Counterfactual and next decisive evidence

O92/O88 should have independently reported `/proc/self/status VmHWM` alongside `resource.ru_maxrss` at the first fresh-child checkpoint, before any Builder. This would distinguish inherited accounting history from child-actual memory. The next highest-value oracle is a bounded hosted parent-preallocation + subprocess child with both witnesses, then an actual O88 same-source worker with independent child `VmHWM` if warranted. If inheritance reproduces, O88's RSS values remain **raw instrumentation facts** but cannot justify claims about peak memory used by each CMPCT engine; correction to the evidence interpretation is required.

No format, product source, evaluator, release gate, benchmark, threshold or Discovery Engine policy changed. CPU and complete archive-byte conclusions of O88 are independent and remain supported. No product or release credit from this import-only experiment.
