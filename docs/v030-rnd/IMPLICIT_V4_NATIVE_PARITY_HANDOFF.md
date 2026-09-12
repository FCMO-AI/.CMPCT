# r25 implicit-v4 native parity handoff

Status: **staging-only Forge D5 prerequisite / no release credit**.

This record exists on `agent/v030-implicit-v4-native-staging` so native work can advance while the authoritative integration branch is frozen for the exact Python seam landing receipt. It must be reconciled against the eventual authoritative landing head before promotion.

## Proven upstream boundary

The exact canonical Python A/B at source `7efe8625eb76366e75eb340419cb935b62b4f150` admitted implicit-v4 structurally and measured:

- explicit filesystem-v1 control: 139,634 B;
- implicit-v4 control: 14,697 B;
- complete r25 baseline: 909,369 B;
- complete r25 candidate: 844,116 B;
- complete-artifact saving: **65,253 B**;
- exact filesystem-v1 semantic reconstruction: yes;
- strong tree verification: yes;
- control read amplification: **1.0x**;
- release credit: no.

The authoritative landing workflow must re-run this exact D5 boundary before persisting the seam.

## Native ownership mismatch to close

`native/cmpct-portable/src/manifest.rs::FsManifest::parse` currently accepts only the filesystem-v1 map and obtains every regular size/SHA from that map. That is deliberately insufficient for implicit-v4: compact control omits regular paths, sizes and SHA-256 values because the authenticated G04/PrefixGraph content graph already owns them.

`native/cmpct-portable/src/canonical.rs::Canonical25Archive::open` already has the information needed to close this honestly:

1. open the authenticated content archive;
2. locate/read/authenticate the filesystem-control member;
3. enumerate all graph entries and obtain each exact `(size, SHA-256)` through `entry_identity`;
4. pass those graph-owned identities into one dual-control manifest parser;
5. for filesystem-v1, retain the existing map parser and exact manifest-vs-graph cross-check;
6. for implicit-v4, parse the bounded array, reconstruct regular entries from the sorted authenticated graph identities, merge explicit directory/symlink/hardlink rows, then expose the same `FsManifest` semantic object used by list/read/verify/extract/ZIP export.

Do **not** duplicate the downstream public/materialization paths for implicit-v4. Concept compression is the point: both controls must converge into the existing `FsManifest` semantic object before ordinary archive behavior.

## Exact implicit-v4 grammar native must consume

Wire root:

`[4, default_metadata, regular_metadata_overrides, explicit_rows]`

`default_metadata = [mode, mtime_ns, uid, gid, xattrs]`.

Each regular override is `[mask, ...changed values]`, with mask bits:

- `1`: mode delta;
- `2`: signed mtime-ns delta;
- `4`: uid delta;
- `8`: gid delta;
- `16`: complete xattr replacement.

Numeric deltas are signed integers. Applying a delta must be checked for overflow and the reconstructed value must pass the same final domain as filesystem-v1: mode `0..0o7777`, mtime signed i64, uid/gid u32, bounded xattrs.

Each explicit row is `[prefix_len, suffix, kind_code, metadata_override, payload]` where kind codes are `1=directory`, `2=symlink`, `3=hardlink`. Paths are prefix-deltas against the previous explicit path and must be safe, strictly sorted and unique. Directory payload is nil. Symlink payload is a portable-safe target string. Hardlink payload is an integer index into the canonical sorted regular-identity vector.

The total regular+explicit count is bounded to 65,536 and raw control remains under the existing 8 MiB metadata/decode-unit ceiling.

## Required fail-closed checks

Native parity is incomplete unless all of these are independently rejected:

- unsupported version/root shape;
- over-limit raw control, arrays, strings, xattrs or entry count;
- invalid metadata mask or trailing override fields;
- signed-delta overflow or reconstructed domain violation;
- invalid prefix length, unsafe path, duplicate/unsorted explicit path;
- regular path colliding with an explicit path;
- internal control path appearing as a regular user member;
- invalid directory/symlink/hardlink payload;
- hardlink index outside the regular vector;
- graph regular-count mismatch;
- graph content set differing from reconstructed semantic regular set plus the control member;
- non-regular internal content entry;
- control member size/SHA mismatch;
- regular size/SHA mismatch during subsequent streaming/materialization.

No malformed implicit-v4 value may fall back to filesystem-v1 interpretation merely because the compact parse fails.

## Frozen native vector

`tests/conformance/v030-r25-implicit-v4-native.json` is the first builder-independent wire vector for this seam. It is paired with `tests/test_v030_implicit_v4_native_vector.py`, which binds the frozen bytes to the Python executable specification and exact filesystem-v1 expansion.

The vector deliberately covers:

- signed pre-epoch mtime;
- numeric metadata deltas;
- xattr replacement;
- directory;
- symlink;
- hardlink by regular-owner index;
- two graph-owned regular identities.

It is a seed, not sufficient conformance by itself. Native tests must add malformed variants rather than treating one happy vector as parity.

## Promotion sequence

1. land Python canonical admission on the authoritative frontier only after its exact D5 A/B re-passes;
2. rebase/reconcile this staging branch onto that exact landing head;
3. make `FsManifest` dual-control without duplicating public semantics;
4. consume the frozen vector and add malformed-control tests in Rust;
5. regenerate canonical r25 golden archives that actually select implicit-v4 where structurally beneficial;
6. rerun native list/read/verify/extract/recovery/C-ABI/locality authority;
7. carry the same vectors through Android/JNI and physical ARM64 authority;
8. only then let all-15/external/release authority grant product credit.

## Forge decision

Diagnosis: **D5 productization/platform**. Saturation: **S6 proven-win productization**. Lowest sufficient intervention: native semantic parity, not new representation research. Decision: **PROMOTE_NEXT_PREREQUISITE** once the authoritative Python seam is durably landed.
