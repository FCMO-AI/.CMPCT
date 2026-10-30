# J24P01 native loader selection: preregistered 2026-10-30

Baseline: released main at 80c358f8824ec1b20d349c92ed94c898090969b0, native_codec.py blob c928e69e1513fa1f7898e4016cbccd8bda3dfbec. Issue #840 preserves a synthetic selection ambiguity, not a confirmed affected installation.

Hypothesis: the loader can reject duplicate matching binaries and nonregular or symlinked candidates before dynamic loading, while preserving the successful unique-regular-file case. Compare to unchanged source and native packaging expectations.

Prospective controls: empty => missing-native error; one file => same load path; two candidates => fail closed; internal or external symlink => fail closed; matching directory or dangling symlink => fail closed; unrelated file => ignored; supported-host imports and optional-native fallback remain valid. Record exact stdout/failures and do not relax tests or release gates.

Kill/narrow: if actual editable packaging legitimately uses links or multiple physical candidates, do not claim compatibility; measure and redesign admission. Static path validation is not a guarantee against concurrent pathname replacement.

This is a draft research/product-hardening candidate. No format, version, ABI, benchmark, promotion or release change. #841 owns the post-benchmark mapped-inode diagnostic; #574 owns discovery state. Only this branch owns the pre-load selector and its focused tests.
