# O156 — logical pathname separator parity

Date: 2026-10-26 UTC. Prospective research registration, prior to instrument implementation. Branch base `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.

Question: does the current Python Reader export the same logical namespace to ZIP as it extracts directly? `canonical_logical_path` treats backslash as a separator, while the ZIP serializer appears to use the unnormalized stored name.

Prediction: an authenticated revision-24 archive with a single path `nested\\leaf.bin` extracts through CMPCT into two path components; its ZIP export, read by Python `zipfile` on Linux/macOS, identifies one pathname with a literal backslash. Original unmodified single-file golden and explicit `nested/leaf.bin` variants should agree. All three original physical payloads and content hashes are held constant across treatments.

Method: start from existing independently authored `tests/conformance/v24-direct-codecs.json`. Change only the MessagePack logical name and regenerate both compressed indexes and SHA-256 fields; retain all physical data bytes. Verify source, decode, ZIP CRC, files and relative names. Use the same Reader and identical logical content. Compare RAW, Zstd, and Deflate variants on Linux and macOS.

Falsifier: archive cannot open, modified physical data, corrupted ZIP, or both extractions yield the same relative names in the backslash arm. The result establishes only ZIP namespace interoperability; it cannot prove broader security, performance or release readiness. No Builder, Reader, release evidence or format changes. Existing ZIP owner retains implementation responsibility.
