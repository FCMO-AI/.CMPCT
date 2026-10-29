# J24G45 — Narrow zero-copy input ownership for authenticated zero-output Zstd

Date: 2026-10-29 UTC. **Experimental continuation of existing Python-codec PR #767. Not merged; no release credit.** Hosted results must be inspected at the resulting exact HEAD.

## Primary question / baseline
J24G43 (#763 / issue #764) falsified Python and Rust physical verification of a malformed Zstd frame with decoded size zero. J24G44 (#767) fixed the three Python adapter routes and passed its exact-installed physical court on Ubuntu/macOS/Windows at head e88797831e72a23ae0fd1aff6ad7b3c21cfd5ede. However, the newly activated decode path still copied the entire encoded input via ctypes.create_string_buffer(data), despite using a one-byte output buffer. The earlier 16-MiB source-copy micro measured a 16-MiB additional allocation, not full Reader RSS.

Question: can this newly exported copy be removed ONLY for nonempty encoded Zstd input claiming zero logical output, without altering historical encoded-empty sentinels, normal nonzero decoding, signed r24, the native ABI or errors?

## Design and code
A borrowed-source helper uses ctypes.c_char_p(data) on immutable bytes. Its ctypes object strongly retains the original bytes while the synchronous C ABI call executes; the native Rust input is an immutable pointer/slice, and the length is explicitly passed, so embedded NULs do not truncate. The source is not retained after returning. The existing copying helper stays unchanged for every nonzero output, compressor and dictionary-source call. Exactly three zero-output decode entrypoints now use the borrowed helper. No Builder, Reader, Rust ABI, format, golden vector, comparator or release-gate mutation.

## Independently executed local micro
A standalone CPython/ctypes oracle, research/j24g45/borrowed_input_oracle.py, ran on Linux x86_64, CPython 3.13.5, kernel 6.18.55, using 16,777,216 immutable bytes (SHA256 341aacac661ccb210720bedaa9ead5d668fe5ea41a73532fc147c71e34040df1) containing embedded NULs. Eight interleaved observations of each input-construction method are retained in research/j24g45/local-linux-cpython313-micro.json.

| Isolated source-pointer construction | Copy | Borrow |
|---|---:|---:|
| Median peak traced allocation | 16,781,290 B | 328 B |
| Median wall | 2,594,873 ns | 29,318 ns |
| Median process CPU | 2,547,402.5 ns | 17,170 ns |

Median peak traced allocation reduction: **16,780,962 bytes**. Local timing is a micro with significant first-run and allocator variation, **not installed CMPCT speedup or total process peak RSS**. On CPython, the ctypes pointer matches PyBytes_AsString and its owned object is the original bytes. Dedicated installed tests check this mechanism under each required host.

A separate Linux system-libzstd.so.1 oracle accepted a nine-byte compressed-empty frame (hex 28b52ffd2000010000), rejected a single-byte magic corruption, and rejected an appended NUL when passed via borrowed pointers with explicit lengths. System libzstd also accepted a valid **16,777,224-byte Zstd skippable frame** decoding to zero logical bytes and rejected its truncations. The large-frame observation shows physical bytes can substantially exceed zero logical bytes; it is **not evidence** that a particular CMPCT archive with that frame is admitted or safe in every runtime.

## Installed and adversarial evidence boundary
The existing signed authentic r24 valid/corrupt frame court, contradictory decoded-one-byte specimen, detached independent physical auditor, and unchanged direct-codec/dictionary golden vectors remain mandatory. Additional tests check embedded-NUL explicit lengths, borrowed-object lifetime after caller release, no accidental old-copy fallback and an isolated 16-MiB allocation comparison. A valid encoded-empty prefix plus trailing zero must fail.

The dedicated workflow runs these tests on installed Python+Rust packages on Ubuntu 24.04, macOS 14 and Windows 2022, preserving independent cost receipts and full raw physical artifacts. At initial writing, **new-head hosted outcomes were pending**, not product-creditable.

## Negatives, concurrency, kill conditions
Current historical general-test reds on the prior head are four existing release/fingerprint assertions, not caused by this source change; no evaluator was altered. Native Rust zero-size complete verification remains a different owner (#759/#765). Full Reader RSS, decode CPU, creation/extraction and selective-work costs, temporary I/O, hostile concatenated/multiframe rules, native-portable memory lifetime under other Python implementations, crash recovery and release parity are unmeasured.

Kill/revert if an installed host fails the signed physical court, an archived good frame changes acceptance, a malformed frame is accepted, the pointer loses lifetime/bytes, or the claimed source-copy elimination fails. The existing Python-codec owner PR #767 was advanced, rather than duplicating code; competing branches and docs/discovery/STATE.json were untouched. The practical counterfactual lesson is to inspect the complete encoded-input ownership before claiming that a one-byte output cap means small total memory. No discovery-policy change earned.

**Next:** adjudicate exact-head installed three-host CI and the detached wire/alloc receipts, compare inherited general/native/fuzzing gates and document every failure. No merge/release without ordinary authority and promotion evidence.