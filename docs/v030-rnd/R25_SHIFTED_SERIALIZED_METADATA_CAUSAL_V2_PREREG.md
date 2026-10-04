# Shifted serialized-metadata causal v2 preregistration

Status: **FROZEN FORGE D2 / CUSTODY CAUSAL CHECK / ZERO RELEASE CREDIT**

## Question

The predecessor `R25_SHIFTED_PRODUCT_METADATA_DETERMINISM_RESULT.md` was valid but returned `SHIFTED_MTIME_METADATA_NOT_SUFFICIENT` because its support rule incorrectly demanded logical product-tree variation in the fresh arm. That result is immutable. It nevertheless observed three fresh genuine-r24 sizes (`29,883,724 / 29,883,732 / 29,883,726 B`) and one repeated fixed-mtime r24 size (`29,883,488 B`).

This superseding experiment asks a narrower causal question that does not depend on logical tree identity: **among filesystem facts actually consumed by canonical r24 scanning, is mtime the only cross-generation varying field, and does normalizing only mtime produce a stable serialized metadata projection and exact r24 archive identity?**

## Frozen target

- `resemblance_hostile_v1 / 01_shifted_versions`
- accepted historical content identity: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`
- three independently generated repetitions per arm
- fixed timestamp: `1767225600000000000` ns
- production source and all release/S6 thresholds unchanged
- release credit: false

## Canonical serialized-filesystem projection

For every descendant path in lexical order, capture the fields canonical `Builder.scan()` consumes before representation selection:

- relative path;
- file type;
- permission mode (`stat.S_IMODE`);
- `st_mtime_ns`;
- `st_size`;
- uid/gid;
- xattrs as sorted name/value pairs where supported;
- hardlink relation as a stable prior-relative-path identity rather than device/inode numbers;
- symlink target bytes where applicable.

Two hashes are required:

1. `full_projection_sha256`, including mtime;
2. `projection_without_mtime_sha256`, identical encoding but with mtime omitted.

The instrument must also record complete genuine-r24 archive bytes and SHA-256, plus strong verification to the canonical logical tree.

## Arms

`fresh`: generated exactly through the current release-performance materializer, no metadata intervention.

`fixed-mtime`: independently generated, then only atime/mtime on root and descendants set to the fixed timestamp. No path, bytes, permission, uid/gid, xattr, link, type or size modification is allowed.

## Frozen support rule

`SHIFTED_MTIME_SERIALIZED_METADATA_CAUSAL_SUPPORTED` iff the experiment is valid and all are true:

1. all six accepted historical content hashes are identical to the frozen target;
2. all six strongly verify to one logical tree;
3. fresh `r24_bytes` has more than one value and fresh `r24_sha256` has more than one value;
4. fresh `full_projection_sha256` has more than one value;
5. fresh `projection_without_mtime_sha256` has exactly one value;
6. fixed `full_projection_sha256` has exactly one value;
7. fixed `projection_without_mtime_sha256` has exactly one value and equals the fresh mtime-omitted projection;
8. fixed `r24_bytes` has exactly one value and fixed `r24_sha256` has exactly one value;
9. every fixed descendant mtime equals the frozen timestamp.

Otherwise, if execution and identity checks are valid: `SHIFTED_MTIME_SERIALIZED_METADATA_NOT_SUFFICIENT`.

Any inability to capture a field that canonical r24 consumes, any historical identity drift, failed verification, or forbidden metadata change yields `INVALID_EXPERIMENT`.

## Consequence

Support would establish a fixture-level cause for the old S6 r24 identity drift, not an S6 pass. It may authorize a **new superseding S6 freeze** that normalizes only mtime before both control and candidate builds, freezes the resulting exact r24/archive identity, and retains every original robust-RSS, wall, size, PrefixGraph-selection, helper-lifecycle, recovery and integrity threshold unchanged. Old S6 receipts remain immutable and invalid.

Non-support retires mtime as sufficient explanation under this exact serialized-metadata model and requires attribution of the next varying canonical input before S6 can be superseded.
