# J24N03 — native CDC late-mask width portability: original-source x86/x64 court

Date: 2026-10-27 UTC. PRE-REGISTERED BEFORE TEST/WORKFLOW. Parent #608 HEAD `b0be37721a7defbb570b2b3920a7924abb37379b`; original native blob `216189c6a15f1579d596bc4df5128ae63f794168`. Narrow sibling question to #606/#611; **tests only**. No native C source mutation permitted in this episode. No duplicate CDC fix on #608's source-owned branch.

## Prediction / cheapest decision-changing evidence

The exact original expression `(uint64_t)(avg_size / 2 - 1)` is evaluated as `size_t` before conversion. For `avg_size=1`, 32-bit returns `0x00000000ffffffff`, 64-bit returns `0xffffffffffffffff`. The deterministic seven bytes `00 de 1a 53 f0 11 63`, `min=1 avg=1 max=7 cap=4`, have rolling hash `0x2c28267800000000` after consuming the fourth scanned byte. Predict **two cuts [5,7] on real Windows x86**, **one cut [7] on real Windows x64** when compiling **the same exact GitHub `native/cmpct_cdc.c` blob** with MSVC. The inherited gear table matches SplitMix64 256/256. Portable positive control: `avg=2,min=1,max=7` has no architecture-induced unsigned underflow and should yield identical full logical partition across x86 and x64 (the exact cuts need not be prospectively guessed).

## Method / guardrails

Add one tiny C court that links the actual unmodified source, asserts source-observed x86/x64 cut counts and validates monotonic positive ends and last=7. Add a Windows 2022 two-arch hosted workflow that checks `HEAD:native/cmpct_cdc.c` equals the frozen blob and runs the same synthetic court under MSVC x86 and x64. Save stdout receipts per architecture. Keep the historical, perhaps undesirable, semantics as an **observational test**, not a promoted cross-architecture contract. Independent initial x64 C reconstruction + forced uint32 mask and GCC i386 codegen are supporting lower-rung evidence only; no actual i386 binary has yet run. Tests must not mutate a source file, freeze gate, comparator, format, version or owner PR.

## Kill / narrow / decision

If exact-source x86 does not emit [5,7], or exact-source x64 does not emit [7], reject/narrow the numerical model; report toolchain/platform and do not retune witness. A compiler failure is infrastructure, not semantics; fix instrumentation only with a new prereg addendum if necessary. A positive pair establishes a narrow portability counterexample, **not** any ordinary installed product failure: optional native helper was not exercised in inherited O196 product trace. Post-result: send source-attested evidence to #611 and #608 owners, recommend portable 64-bit subtraction as a separate guarded candidate only if source-owner and actual product path warrant it. No merge/release credit for an observational test.
