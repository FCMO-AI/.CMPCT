# J24N02b — Windows MSVC test-instrument build correction (prospective)

**2026-10-27 UTC, written before correcting the test runner.** J24N02 exact-source specialized Actions #40541596061 completed SUCCESS for Ubuntu and macOS; Windows failed **before invoking the C test**. Its MSVC build command used `/Fo:<single-file>` while passing two C translation units to `cl`, which rejects this combination with D8036. This is an *instrument/host command failure*, not a measured native CDC regression or a Windows semantic pass.

## Narrow repair

- Remove the explicit single-object `/Fo` option.
- Run compiler in the already allocated temporary build directory so each input generates its own temporary `.obj`; keep `/Fe:<same-EXE>` and `/W4 /WX /std:c11` unchanged.
- Do not modify either actual C source blob, test cases, fixture bytes, historical parent SHA checks, ABI, thresholds, compiler warning strength or feature admission.
- Re-run all three hosts on the new **exact** HEAD. Re-check compiler logs and original artifact for Windows; a silent skip or a build failure is not a pass.

## Independent evidence and known negative

A separate locally reconstructed **byte-identical** #501 source (`git hash-object=a6253beece20ce8aad3cdb605a6d9fcaa50d9364`) and repaired candidate (`216189c6a15f1579d596bc4df5128ae63f794168`) were compiled with GCC and compared to an independently written Python unlimited-precision cut oracle: 1,200 ordinary source-parity cases and 1,500 extreme-parameter cases passed. Ten observed ordinary-buffer samples returned 0 on historical C but valid monotone cuts on the repaired C with huge `max_size`. **That local check is not hosted Windows proof, full product proof or a global performance claim.**

The generic O166 exact-blob court fails intentionally when product C changes: it specifically requires the immutable #501 source blob, and therefore cannot be reclassified as an algorithm regression or treated as source-independent product acceptance. All frozen evaluators remain intact. New J24N02 specialized court carries the missing behavior proof.
