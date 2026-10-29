# J24M01e — prospective Linux ru_maxrss fork/exec attribution (2026-10-29 UTC)

**PREREGISTERED BEFORE NEW INSTRUMENT CHANGE; original J24M01d outcomes are preserved unchanged.**

## Observation and baseline
J24M01d same immutable 1160-byte archive: original unchanged child RSS 26176 / 23344 KiB; separate instrumented child 23576 / 23468 KiB, exact Reader blob f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f. Actual full suite opt-in sidecar: original unchanged child reported 180048 KiB; *separate* child read 180048 KiB on its first ru_maxrss call BEFORE importing CMPCT, same expected Reader, 8192 physical sparse bytes, 795 tests passed and 5 failed. This is not evidence that verify allocated 180 MiB.

## Hypothesis
Linux resource.getrusage(RUSAGE_SELF).ru_maxrss high-water can propagate across Python fork+exec, reflecting an earlier high-water from the parent process even if the child currently uses little resident memory; /proc/self/status VmHWM / VmRSS should distinguish new-child allocation. The original test uses ru_maxrss only. In a no-CMPCT local independent process, after touching/freeing a 240-MiB buffer, parent ru_maxrss=341000 KiB, newly execed child ru_maxrss=341000 KiB but child VmHWM~95388 KiB. This is a local mechanism demonstration, not hosted suite evidence.

## Strong simpler control, alternatives, and disproof
Run a no-CMPCT fresh child with parent after touching memory; record parent peak, child ru_maxrss, child VmHWM and VmRSS before import. In actual full-suite order intercept original subprocess.run only to log parent ru_maxrss, then pass original command+kwargs UNMODIFIED; afterward launch a clearly separate follow-up child that records ru_maxrss/VmHWM/VmRSS before import, after import, after verify, and exact imported Reader Git blob. Do not revise original test, 131072-KiB ceiling, release gate or expected failure. If child VmHWM is also high or parent peak does not agree with child initial ru_maxrss, inherited accounting is not sufficient; classify negative honestly. Alternative: native/loader work before Python starts could cause high true child VmHWM.

## Decision boundary
If parent high-water and child's inherited ru_maxrss are ~180 MiB while post-exec child VmHWM stays near ~25 MiB, classify the inherited test's ru_maxrss as a process-boundary measurement artifact under suite context. Do NOT call the general suite green or fix its threshold: #738 should own any proper child-peak evaluator change, source provenance, unchanged threshold, no release until other 4 failures and #749 publication custody resolved. No discovery STATE change or global policy lesson from this one boundary.

## Evidence type
Linux-hosted causal control; no product change or cross-platform assertion; original full-suite results, source SHA and frozen archive must remain independently reproducible.