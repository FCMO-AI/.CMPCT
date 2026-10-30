# J24P01c — macOS wheel architecture-label truth (preregistered)

UTC date 2026-10-30. Exact head before test `7d6d740c4d059843426048f67aef4e5401517580` on PR #843. Published main v0.30.0 / archive r24 unchanged.

## Observed trigger, not conclusion

The original [J24P01b result](2026-10-30-j24p01b-wheel-install-result.md) on source HEAD `cb393b97880737969ac5acc5d1fffc7f4b8d15b5`, hosted [Actions #41099549701](https://github.com/FCMO-AI/.CMPCT/actions/runs/41099549701), reports a macOS-14-arm64 wheel named `cmpct-0.30.0-cp311-cp311-macosx_11_0_universal2.whl`. It proved the wheel imports on ARM64 and has one native package file. It did NOT prove that the native Mach-O actually carries both ARM64 and x86_64 slices. A wheel tagged `universal2` advertises both architectures: this is a separate *portability and packaging-metadata* claim, not Zstd content integrity.

## Frozen question and disproof before code

Inspect the **same exact wheel-native member** named in the source-attested wheel receipt, with host tool `/usr/bin/lipo -archs`; independently read the original wheel's macOS platform tag. If tag contains `universal2`, H1 predicts both `arm64` and `x86_64` slices in the installed native library. A single architecture contradicts H1 and must be preserved as an actual wheel-label/payload compatibility red, without relabeling the wheel, weakening the test, or extrapolating the ordinary ARM64 runtime PASS to Intel Macs. If wheel is genuinely single-architecture tagged, require only the matching platform slice, preserving compatibility.

The stronger control, if a discrepancy arises, is to inspect the same binary's Mach-O header using `file` or `lipo -detailed_info`, and examine the setuptools-rust build/host target; do not infer runtime failure on a machine we did not test. Report actual observed slices, full wheel filename and exact source head in a durable artifact. All previous J24P01b wheel receipts, injected duplicate controls and main safety/evaluator thresholds remain intact.

## Ownership and cost

This is a **small extension of PR #843's existing macOS wheel CI**, not an independent product fix or release. Only research/CI files may change. If the disparity is real, file a bounded portability issue and coordinate with packaging owner; do not change build flags without a separate architecture/size/performance/cross-host court. Single-host macOS-14 ARM64 can establish binary layout but cannot prove actual Intel runtime performance or complete platform portability. No Discovery policy/state mutation and product credit zero.
