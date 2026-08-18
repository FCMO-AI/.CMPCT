# Slot-00 adversarial review — T01 native/portability

These are integration-blocking findings to resolve before T01 can enter REVIEW. They are not a request to weaken or replace the current native architecture.

## P0 — MessagePack allocation preflight

`native/cmpct-portable/src/format.rs::parse_msgpack` currently invokes `rmpv::decode::read_value` before structural declaration limits are enforced. Add encoded-byte preflight for array/map/string/bin/ext lengths, depth, nodes and truncation before general decode. Keep the post-decode validator as defense in depth.

## P0 — non-finite numeric policy declarations

`format::number` accepts arbitrary `f64`. G0-G4 separately checks `is_finite()` for its locality declaration, but PrefixGraph currently performs only:

```rust
if number(value, "PrefixGraph read amplification")? > MAX_MEMBER_READ_AMP { ... }
```

A NaN makes that comparison false and can bypass the policy check. Prefer fixing the shared numeric admission helper so policy numeric values are finite by construction, then retain mechanism-specific range checks. Add NaN/+Inf/-Inf hostile tests for every float-bearing policy field.

Footnote: fail-closed numeric policy must not depend on IEEE comparison behavior for non-finite values.

## Cross-lane identity dependency

Do not freeze `CMPNXG4` / `CMPNXP1` into final native ABI/goldens. T03's current product architecture uses `CMP25G4\0` / `CMP25PG\0`; reconcile final identities and any filesystem-manifest semantics after T03 reaches REVIEW.
