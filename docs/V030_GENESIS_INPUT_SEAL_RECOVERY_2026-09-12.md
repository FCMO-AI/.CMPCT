# v0.30 Genesis input-seal recovery debt — 2026-09-12

Status: **evidence-custody hardening / no score change**.

## Trigger

A current exact-head attempt to transfer the locality-derived micro-pack mechanism onto the 15 frozen CMPCT1/ONE Genesis workloads regenerated the named corpus suites and compared them against `benchmarks/one/genesis_gate_workload_identity_v1.json`.

Only 10/15 current regenerations matched the frozen physical identities exactly. Five rows drifted:

- `neutral_hostile_v1/01_developer_repository`: file count and logical bytes match; tree hash differs;
- `neutral_hostile_v1/02_office_workspace`: current logical bytes are +19 B and tree hash differs;
- `neutral_hostile_v1/03_media_library`: current logical bytes are +6,125 B and tree hash differs;
- `neutral_hostile_v1/05_logs_and_telemetry`: file count and logical bytes match; tree hash differs;
- `neutral_hostile_v1/06_incremental_backups`: file count and logical bytes match; tree hash differs.

This is **input-seal drift**, not a product result. The frozen Genesis scores and decision remain unchanged.

## Why hashes alone are insufficient custody

A frozen hash can prove that a newly generated workload is wrong, but cannot reconstruct the historical workload. The affected generators include outputs from tools or container formats whose exact bytes may depend on external binary/library versions, embedded timestamps/metadata, platform behavior or implementation details. Pinning only the Python source revision is therefore not a complete physical-input seal.

The original source-sealed Genesis v0.30 recovery correctly sealed contender source. This incident shows the symmetric requirement on benchmark input: **source hermeticity and input hermeticity are separate obligations**.

## Durable law for historical/frozen gates

For any result intended to remain a physical byte comparator beyond the run that produced it, preserve at least one of:

1. **byte seal** — archive the exact benchmark corpus bytes (or a deterministic content-addressed bundle) with digest and per-workload manifest; or
2. **hermetic generator seal** — preserve a reproducible environment sufficient to regenerate byte-identical inputs, including external binaries/libraries and deterministic clock/metadata controls where relevant.

Prefer the byte seal for benchmark corpora small enough to retain economically. A hermetic generator remains useful for independent reproduction, but the exact historical byte bundle is the simplest authority when a future experiment must compare against the same physical workload.

A manifest containing only file count, logical bytes and tree hash is necessary validation metadata but not sufficient recovery custody.

## Fail-closed behavior

When a historical input cannot be reproduced byte-exactly:

- do **not** update the historical hash to the new output;
- do **not** call the mismatch a product regression;
- do **not** silently substitute the current corpus into a frozen score table;
- do **not** infer the missing historical bytes from aggregate comparator numbers.

Allowed work:

- run diagnostics on the exact subset that still matches, clearly labeled as a subset with no full-gate score credit;
- run current-fingerprint generalization separately, clearly labeled as a new corpus identity with no retroactive comparison claim;
- recover the original byte bundle from retained run artifacts/cache if available and verify every workload against the frozen identity before use.

## Genesis-specific recovery status

The frozen v0.30 source-sealed recovery authority remains the historical run and receipt documented in `docs/one/evidence/ONE_GENESIS_GATE_RESULT_2026-09-11.md`. Its retained result artifact contains the measurement receipt, not the original 15 workload directory bytes. Therefore this research session cannot honestly reconstruct the five drifted workloads from that artifact alone.

The exact-matching 10-workload subset may be used only as mechanism-transfer evidence. It cannot be summed with current versions of the other five and called the Genesis15 result.

## Forward custody requirement

Any new benchmark family that becomes a frozen release/gate authority should publish alongside its measurement receipt:

- corpus bundle digest;
- per-workload tree digest, file count and logical bytes;
- generator/source commit;
- toolchain/environment provenance;
- a retrievable exact byte bundle or reproducible hermetic image/reference;
- retention policy long enough to support the repository's historical-comparator horizon.

This requirement strengthens comparator hermeticity; it does not alter any frozen score or release law.
