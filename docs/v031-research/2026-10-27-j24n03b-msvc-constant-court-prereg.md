# J24N03b — instrumentation correction only (2026-10-27 UTC)

## Observed failed execution

GitHub Actions #40550908925: both Windows x86 and x64 **failed to compile** the newly introduced test `tests/native_cdc_width_court.c`; MSVC `/W4 /WX` emitted C4127 for `if (sizeof(size_t) ...)`, promoted to C2220. **No source CDC call ran; this is instrument compilation failure, not falsification or acceptance of the width prediction**.

## Repair fixed before implementation

Introduce a `volatile size_t runtime_width = sizeof(size_t);` probe inside the court and compare `runtime_width` instead of the compile-time constant expression on the two offending conditionals. Do not disable MSVC `/WX`, weaken any assertion, alter the seven witness bytes/params, modify the original C, change expected x86/x64 outputs, run a different compiler/architecture or change CI custody. Re-run the exact unchanged two-host question. If the compiler still rejects, preserve failure and preregister a separate narrowly justified instrument correction; no conclusion until a real 32-bit executable runs.
