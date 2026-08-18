# CMPCT v0.30 canonical product architecture

Status: **provisional revision-25 integration contract; not a release claim**  
Authoritative implementation line: `agent/v030-authoritative-integration`  
Execution policy: `docs/V030_EXECUTION_MODEL.md`

## Decision

v0.30 has one product boundary even though its encoder may select more than one bounded content representation. The product may publish only:

1. **revision 25 / Geometry-Mosaic profile** — `CMP25G4\0`;
2. **revision 25 / PrefixGraph depth-1 profile** — `CMP25PG\0`; or
3. **genuine revision 24 fallback** — `CMPCT24\0`.

`CMPNX*` artifacts remain research evidence. They are never relabeled as a canonical release profile.

The revision-25 profiles share one authenticated filesystem-semantics bridge stored as the reserved logical member:

```text
.__cmpct_r25_internal__/filesystem-v1.msgpack
```

The manifest pays ordinary archive cost and participates in authenticated content/recovery. It records directories, regular-file identity, symlink targets, hardlink relationships, mode, signed nanosecond mtime, uid/gid and xattrs.

Footnote: r25 is an archive representation, not a content-only benchmark with release branding added afterward. Filesystem framing must be included in exact product bytes.

## Product-floor rule

The release-facing implementation is `experiments/entropygraph_v030_canonical_final.py` through `experiments/entropygraph_v030_release_product.py`.

For every r25-eligible source tree it builds a **genuine canonical r24 artifact** and the r25 tournament as independent complete candidates. They may execute concurrently, but approximate estimates never decide publication.

- r25 must be a real canonical `CMP25*` profile;
- r25 must strictly beat the accepted-v0.29 historical research floor where that causal gate applies;
- r25 must also be strictly smaller than the genuine canonical r24 artifact for the same original user filesystem tree;
- exact r24/r25 size ties keep r24;
- if source semantics are not representable by r25, the product builds/verifies/publishes r24 directly.

This product floor is separate from the immutable historical 15-workload causal substrate. Historical causality and canonical product parity are both required; neither may redefine the other.

## Why PrefixGraph is an alternative r25 profile

PrefixGraph remains a separate revision-25 profile for v0.30 rather than an unmeasured new Mosaic node kind. Its measured contract is:

- one direct raw-content anchor;
- dependency depth at most **1**;
- bounded anchor auditions;
- selected decoded-context amplification at most **8x**;
- authenticated primary/tail metadata recovery;
- complete-artifact pricing.

A future revision may internalize the relation into the Mosaic graph if a one-artifact ablation proves that the extra descriptor/reader/native burden wins under the same complete-product and locality constraints.

## Semantic ownership map

| Concern | Canonical responsibility |
|---|---|
| Product selector / r24 floor | `entropygraph_v030_canonical_final.py` |
| Public release facade | `entropygraph_v030_release_product.py` |
| Geometry semantics | `entropygraph_v030_geometry_overlay_g04.py` and owning Geometry helpers |
| PrefixGraph semantics | `entropygraph_v030_prefixgraph.py` |
| Streamed admission/recovery | `entropygraph_v030_release_reader.py` + strict policy |
| Filesystem semantics | `entropygraph_v030_product_fs.py` |
| r24 fallback | `cmpct.builder.Builder` + `cmpct.reader.CMPCT` |
| Native/shared reader | `native/cmpct-portable` with one dispatcher across r24/r25 |
| Android | parser-free JNI shim consuming the shared portable core |

One responsibility may have research/history adapters, but there must be only one promoted semantic owner.

## Canonical build flow

1. Capture the bounded r25 filesystem manifest.
2. If r25 cannot preserve the source semantics, build/verify/publish genuine r24.
3. Otherwise stage graph-owned regular files plus the authenticated manifest.
4. Build genuine r24 and the r25 complete-artifact tournament concurrently.
5. The r25 tournament may choose Geometry-Mosaic or PrefixGraph only after its own bounded admission/locality checks.
6. Classify r25 candidate bytes by actual magic; research-only `CMPNX*` bytes are not eligible product candidates.
7. Compare exact complete r25 bytes with exact genuine r24 bytes. r25 must be strictly smaller; ties keep r24.
8. Publish the selected artifact with same-filesystem atomic replacement.
9. Strongly verify the exact published product through canonical dispatch.

## Tree identities

Public verification distinguishes three identities instead of overloading one field:

- `tree_sha256` / `user_tree_sha256`: canonical user-visible semantic tree across r24/r25 comparisons;
- `content_graph_tree_sha256`: internal r25 content-graph identity, including the reserved manifest member;
- `filesystem_manifest_sha256`: authenticated filesystem-semantics manifest identity.

For r25, strong verification must reconstruct and hash user-visible regular members and verify that the manifest and content graph agree exactly. A manifest-declared user digest is not trusted without reconstructing the represented content.

## Timestamp and link safety

- r25 mtime uses bounded signed i64 nanoseconds so pre-1970 files are not self-rejected by the reader;
- safe symlink extraction rejects lexical escape under both POSIX and Windows rules independent of the verification host;
- absolute POSIX paths, Windows drive/root/UNC forms, and `..` components under either slash spelling are rejected unless the caller explicitly chooses unsafe symlink restoration.

Footnote: bytes judged safe on Linux must not become traversal-capable when the same archive is later extracted on Windows.

## Canonical profile dispatch

Canonical r25 identity must be explicit and operation-local. Import order must never permanently rewrite research grammars. The remaining productization requirement is stronger: canonical operations must not rely on temporarily mutating process-global research-module magic/dispatch state because a concurrent direct research call could observe that state. The final implementation must pass immutable-profile/concurrency regression coverage before T03 becomes `DONE`.

## Reader and hostile-input contract

Selected r25 archives retain:

- dependency depth <=1;
- selected per-member decoded-context amplification <=8x;
- max decode unit <=8 MiB;
- bounded metadata, path, node, record and logical-size declarations;
- authenticated primary/tail recovery;
- payload/hash refusal on corruption;
- canonical path order and duplicate-path refusal;
- transactional extraction publication/rollback;
- reader semantics independent of encoder nomination heuristics.

The manifest additionally requires a fixed schema/profile/version, bounded entry count/size, safe canonical relative paths, exact integer metadata types, bounded xattr shape, exact SHA-256+length identity for every graph-owned regular file, acyclic hardlink ownership, and a reserved namespace unavailable to user input.

The content graph member set must equal:

```text
{manifest-declared regular files} U {reserved filesystem manifest}
```

Any extra or missing content member is a verification failure.

## Explicit r24 fallback cases

r25 falls back to genuine r24 when source semantics are unsupported or bounded policy is exceeded, including sparse/special files, reserved-namespace collisions, unsupported metadata/path/count/logical-size conditions, or when no canonical r25 candidate strictly beats the genuine r24 product artifact.

Fallback is an explicit product result, not silent feature disappearance.

## Public API/CLI

The release product facade owns:

- `build(root, archive)`;
- `strong_verify(archive)`;
- `list_members(archive)`;
- `read_member(archive, path)` / member stats;
- `extract(archive, destination, ...)`;
- release ablation/benchmark hooks.

For r25, the reserved manifest is not exposed as a user file. For r24, operations dispatch to the mature reference reader. Research-only `CMPNX*` input fails explicitly as non-canonical.

## Native / portability boundary

Revision-25 is not releasable until the shared portable native reader implements the same fixed profiles, recovery, resource admission, member-locality observability, ZIP/export behavior and filesystem-manifest semantics. Platform integrations consume that shared reader rather than copying graph or MessagePack parsers.

The Python product facade proving r25 semantics is therefore necessary but not sufficient release evidence.

## Research modules retained intentionally

Research/history modules remain useful for causality, ablation and negative results. Their presence does not make them promoted APIs. In particular, historical `CMPNX*` magics remain research identities, while canonical publication uses only fixed `CMP25*` identities or genuine `CMPCT24\0` fallback.

## Completion boundary

The canonical architecture is complete only when:

1. implementation and `docs/FORMAT.md` agree;
2. r24-vs-r25 product-floor, tree-identity, signed-time, cross-platform symlink, recovery/locality and hostile-input tests are green;
3. canonical profile dispatch has no process-global mutation/concurrency hazard;
4. native/shared-reader and platform conformance consume this same fixed contract;
5. historical causality and canonical product evidence are independently green on the exact reconciled candidate; and
6. final architecture evidence is bound to the frozen release fingerprint.

This document is architecture, not release authority. Only the strict release lock on the exact frozen candidate can authorize v0.30 publication.
