# cmpct-logs-auth-oracle

Research-only helper for `R25_LOGS_FUSED_AUTH_NATIVE_SEAM_V1_PREREG.md`.

This crate is **not** part of the canonical reader/writer and carries **zero release credit**. It exists solely to test whether one native traversal of already-decoded Logs pack bytes can establish both mandatory identities more cheaply than two Python traversals.

Hard contract:

- every decoded byte is consumed by both CRC32 and SHA-256 state;
- full CRC32 and full 32-byte SHA-256 are returned;
- expected identities are never supplied to the helper;
- no archive grammar, decompression, locality, recovery or downstream logical-member verification is changed;
- zero-length input is supported without dereferencing a null data pointer;
- nonzero input requires a readable buffer and valid writable output pointers;
- the benchmark must prove exact parity with Python identities before timing and must reject deterministic pack corruption in both arms.

Any future productization would require independent hostile-input, fuzz, portability/native-platform and exact-fingerprint runtime review. The helper must not be linked into production merely because the research A/B is positive.
