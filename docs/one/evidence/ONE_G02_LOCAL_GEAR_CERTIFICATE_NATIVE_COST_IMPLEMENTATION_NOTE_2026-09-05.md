# ONE-G0.2 — native certificate cost implementation note

Date: 2026-09-05
Status: pre-result Hostile Reviewer correction; frozen numerical gates unchanged.

The first native-cost workflow attempt failed before the benchmark because the new lane omitted the project test-environment install step. No result-bearing timing was produced.

During that blocked interval, Hostile Reviewer inspected the benchmark kernel itself and rejected two avoidable implementation artifacts before accepting any measurement:

1. a runtime `mode` branch sat inside the byte hot loop, so the compiler could not optimize each A/B arm as a production-specialized path;
2. the first bottom-8 implementation rediscovered the current worst witness by scanning all eight entries for every input window, even though a max-heap makes the overwhelmingly common non-replacement decision one root comparison.

Neither artifact is part of the frozen certificate semantics. Allowing them to decide the experiment would measure an intentionally generic microbenchmark dispatcher rather than the best simple implementation of the preregistered mechanism.

The result-bearing implementation therefore uses separately compiled baseline/rolling/certificate hot loops and a fixed eight-entry max-heap. Incoming Gear lookup reuse remains explicit. The exact certificate must still match the independent Python reference on every frozen vector before timing is valid.

**No promotion threshold, workload, state budget, certificate window, witness count, signal identity, or semantic requirement is changed by this correction.** Any timing emitted by the superseded generic-dispatch kernel is implementation-debug evidence only and cannot promote or retire the certificate.