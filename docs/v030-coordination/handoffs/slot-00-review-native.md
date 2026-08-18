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

## P0 — r25 product filesystem manifest is part of native parity

T03's canonical r25 product no longer consists only of G0-G4/PrefixGraph content rows. It adds an authenticated reserved filesystem manifest that reconstructs empty directories, modes/times, symlinks, hardlinks, ownership/xattrs where representable, and hides the reserved internal member from user listing.

The current native G04/PrefixGraph layers expose their raw content-graph entries, so a final r25 archive would currently expose the internal manifest and lose the canonical user filesystem view.

Before native release evidence:

- parse/authenticate the canonical product filesystem manifest under the same pre-allocation bounds;
- expose the **user-visible** entry list, hiding the reserved internal graph member;
- map regular/hardlink/symlink/directory semantics consistently with Python;
- make native user-tree verification distinguish the internal graph tree from the public user tree;
- transactional native extraction must reproduce link/directory/content semantics safely, with metadata application policy matching documented portability behavior;
- malformed/colliding reserved namespace, forward/cyclic hardlinks, unsafe symlink targets and manifest/content identity mismatches fail closed.

If T03 changes the manifest grammar before REVIEW, reconcile to that exact final grammar rather than snapshotting an intermediate one.

## P0 — r24 portable `verify()` is weaker than complete r24 verification

`PortableArchive::verify()` currently materializes each <=256 MiB r24 regular member with `cmpct-core::Archive::read_range` and treats successful return as complete verification.

That is not equivalent for every r24 representation. In the mature core, a direct RAW range read intentionally authenticates framing/touched bytes but does **not** hash the unseen/full payload. Even when the requested range is the full member, the RAW branch does not currently compare the complete logical SHA before returning. Therefore the portable wrapper can report `verify()` success for a corrupted RAW direct payload.

Required resolution:

- add/reuse a mature core complete-member verification primitive that authenticates the whole logical identity for every supported r24 storage kind, including direct RAW;
- have the portable adapter delegate to that primitive rather than inferring verify from range-read success;
- corruption test: mutate a RAW direct payload byte while leaving framing untouched and require portable `verify()` to fail;
- do not cap correctness at 256 MiB merely because a convenience materializer does; a streamed complete verifier is preferable.

## P1 — r24 locality stats must not claim synthetic `1.0x`

The portable r24 adapter currently returns `decoded_context_bytes = logical_bytes` / `amplification = 1.0` for member stats without observing the actual storage representation. That is false for compressed direct members and shared packs/chunks where decoding context can exceed the requested logical bytes.

Either:

- expose real touched/decoded-work accounting from `cmpct-core`, or
- mark the metric unavailable and let accepted r24's existing release-locality evidence carry the inherited policy.

Do not emit a precise 1.0x measurement that was not measured. Final T02 selective-read evidence should use operation-derived stats for r25 and a truthful comparable r24 surface.

## P1 — new native workflow must obey current CI topology

`.github/workflows/native-v030-portable.yml` is a legitimate native compile/lint/conformance smoke lane, but it currently predates the reconciled mainline workflow policy.

Before handoff:

- declare `# ci-lane: fast` near the top if the measured job remains ordinary native PR feedback; if it routinely exceeds the fast-lane envelope, classify it honestly and route it accordingly;
- add a PR/ref-scoped concurrency group with `cancel-in-progress: true`;
- avoid duplicate feature-branch push + pull_request executions for the same authority. A narrowly documented branch-only push during isolated research is acceptable only if it cannot also double-run an open PR; otherwise prefer the path-scoped PR trigger plus `workflow_dispatch`;
- run `python tools/check_ci_topology.py .github/workflows/native-v030-portable.yml` and include the exact output in T01 handoff.

Do not weaken Rust tests, Python/Rust conformance or r24 delegation coverage merely to shorten the lane.

## Cross-lane identity dependency

Do not freeze `CMPNXG4` / `CMPNXP1` into final native ABI/goldens. T03's current product architecture uses `CMP25G4\0` / `CMP25PG\0`; reconcile final identities and filesystem-manifest semantics after T03 reaches REVIEW.
