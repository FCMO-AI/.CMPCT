# CMPCT v0.30 canonical product architecture

Status: **T03 productization decision / provisional revision-25 integration contract**  
Branch owner: `agent/v030-coop-graph-productization`  
Release authority remains the v0.30 integration/referee flow in `docs/V030_AGENT_COORDINATION.md`.

## Decision

v0.30 has one product boundary even though its encoder can select more than one content representation.
The product may publish only:

1. **revision 25 / Geometry-Mosaic profile** — `CMP25G4\0`;
2. **revision 25 / PrefixGraph depth-1 profile** — `CMP25PG\0`; or
3. **genuine revision 24 fallback** — `CMPCT24\0`.

`CMPNX*` artifacts remain research evidence. They are not r24, are not accepted as canonical input by the
v0.30 product facade, and are never relabeled as a released revision merely because an internal portfolio
selected them.

The revision-25 profiles share one filesystem-semantics bridge. A deterministic authenticated manifest is
stored at the reserved logical path:

```text
.__cmpct_r25_internal__/filesystem-v1.msgpack
```

The manifest is an **ordinary member of the selected content graph**. Its bytes therefore pay normal archive
cost, participate in the profile's authenticated metadata/content identity, and follow the same recovery path.
It records the user-visible filesystem properties that the earlier content-only research graphs deliberately
did not own: directories, regular-file identity, symlink targets, hardlink relationships, mode, nanosecond
mtime, uid/gid and xattrs.

This is the critical productization boundary: r25 is not a content benchmark with archive branding attached.
It is an archive representation whose graph content and filesystem semantics are both authenticated and priced.

## Why PrefixGraph is an alternative profile instead of a new Mosaic node today

T03 permits either internalizing PrefixGraph into the owning graph/compiler or a rigorously justified
alternative canonical profile with equivalent accounting, locality, reader and portability guarantees.
The latter is selected for v0.30.

The evidence establishes a useful, bounded PrefixGraph relationship:

- one direct raw-content anchor;
- one target compressed against that direct anchor;
- dependency depth at most **1**;
- bounded anchor audition;
- selected decoded-context amplification at most **8x**;
- strict authenticated metadata and tail recovery;
- complete-artifact pricing rather than an estimated savings sum.

What the evidence does **not** establish is that adding the same relationship as another Mosaic node kind makes
the *combined complete artifact* smaller after descriptor cost, root placement, physical Geometry, locality,
reader complexity and native implementation cost. Doing that now would turn a measured independent mechanism
into an unmeasured grammar interaction.

Therefore:

- Geometry remains physically inside the Mosaic/pre-fallback structure where it was measured;
- PrefixGraph remains a separate revision-25 content profile;
- the system tournament builds/prices complete artifacts and picks the smaller valid profile;
- there is **no arithmetic borrowing** between Geometry and PrefixGraph savings;
- an r25 profile exists only when the complete candidate strictly beats the accepted-v0.29 research floor;
- if no r25 profile earns publication, the product compatibility fallback is built as genuine r24.

A future revision may internalize the relation if a combined ablation proves that representation beats these
complete profiles under the same locality/resource/native contract.

## Semantic ownership map

| Concern | r25 Geometry-Mosaic | r25 PrefixGraph | r24 fallback |
|---|---|---|---|
| Content writer | `entropygraph_v030_shared_portfolio.py` + owning G0–G4 reactor | `entropygraph_v030_prefixgraph.py` under release admission | `cmpct.builder.Builder` |
| Complete profile selector | `entropygraph_v030_release_candidate.py` | same complete-artifact selector | `entropygraph_v030_canonical.py` fallback boundary |
| Content reader | `entropygraph_v030_release_reader.py` + strict policy | same streamed reader + strict policy | `cmpct.reader.CMPCT` |
| Filesystem semantics | `entropygraph_v030_product_fs.py` manifest | same manifest owner | native r24 index/schema |
| Canonical API/CLI | `entropygraph_v030_canonical.py` | same | same |
| Recovery | authenticated G0–G4 primary/tail | authenticated PrefixGraph primary/tail | r24 committed-index/generation recovery |
| Native responsibility | T01 must implement the frozen r25 profile + manifest contract before release claim | same | existing r24 native core continues to own supported r24 semantics |

The table is intentionally one-owner-per-mechanism. Platform integrations must consume the shared native reader
when T01 imports r25 support; they must not reproduce MessagePack/graph parsing independently.

## Canonical build flow

`entropygraph_v030_canonical.build(root, out)` performs the following sequence:

1. Attempt to capture the bounded r25 filesystem manifest.
2. If r25 cannot preserve the source semantics, build/verify/publish a genuine r24 archive and stop.
3. Otherwise stage graph-owned regular files plus the authenticated manifest.
4. Build the exact G0–G4/accepted-v0.29 portfolio once through the shared substrate.
5. Build PrefixGraph only when its bounded encoder-admission contract permits it.
6. Compare the complete G0–G4 and PrefixGraph artifacts. Smaller wins; no sum of independent savings exists.
7. Classify the selected bytes by **actual magic**.
8. A real r25 profile is required to be strictly smaller than the accepted-v0.29 complete research floor. If
   an upstream selector ever returns non-improving r25 bytes, canonical publication fails closed.
9. If the internal winner is `CMPNX*`, retain it only as research evidence, then build/verify/publish genuine r24.
10. Otherwise publish the selected r25 profile atomically **without first performing a redundant r24 encode**.
11. Strongly verify the final product artifact through its canonical dispatch path.

This gives r25 two independent promotion floors:

- it must be a valid canonical r25 grammar rather than inherited research bytes; and
- it must strictly beat the accepted-v0.29 complete-artifact floor that the v0.30 release gate actually names.

The r24 builder is deliberately conditional. Building r24 before every successful r25 candidate would add a full
encode to the hot creation path solely to compute a compatibility artifact that will not be published. That would
contradict the release gate's requirement not to retain a known unacceptable create-time regression. Exact r24
semantics still apply whenever r24 is actually the selected compatibility fallback.

Footnote: accepted v0.29 remains valuable as the causal graph floor inside the research tournament. It is not a
format-compatibility fallback because accepted-v0.29 research can emit `CMPNX*`. The product fallback is r24
because r24 carries the complete released filesystem contract and installed reader ecosystem.

## Exact ablation hooks

The canonical facade exposes:

```bash
python -m experiments.entropygraph_v030_canonical ablate v029 SOURCE OUT.cmpct
python -m experiments.entropygraph_v030_canonical ablate geometry SOURCE OUT.cmpct
python -m experiments.entropygraph_v030_canonical ablate prefixgraph SOURCE OUT.cmpct
python -m experiments.entropygraph_v030_canonical ablate combined SOURCE OUT.cmpct
```

All four graph ablations consume the **same staged filesystem-manifest tree**, so manifest bytes are paid by the
candidate rather than added after measurement.

- `v029` — exact accepted-v0.29 causal floor over that staged tree;
- `geometry` — G0–G4 over the shared pre-fallback Mosaic structure;
- `prefixgraph` — bounded depth-1 PrefixGraph alone;
- `combined` — complete-artifact system tournament between Geometry and PrefixGraph.

`combined` is not `geometry_saving + prefixgraph_saving`. It is the byte size of one complete selected archive.

## Reader and hostile-input contract

The r25 reader path inherits the strict streamed reader/policy gates and adds the filesystem manifest gate.
Selected archives must retain:

- dependency depth <= 1 for PrefixGraph-like references;
- selected per-member decoded-context amplification <= 8x;
- bounded metadata, path, node, record and logical-size declarations;
- bounded physical decode units and decoder-memory declarations;
- authenticated primary/tail metadata recovery;
- payload/hash refusal on corruption;
- canonical path order and duplicate-path refusal;
- transactional extraction publication;
- no encoder similarity/Geometry heuristics in the reader.

The manifest additionally requires:

- a fixed schema/profile/version declaration;
- a bounded entry count and <=8 MiB manifest decode unit;
- safe canonical relative paths;
- exact integer metadata types;
- bounded xattr shape;
- SHA-256 + length identity for every graph-owned regular file;
- hardlinks only to previously declared paths, making cycles impossible by grammar;
- a reserved internal namespace that cannot collide with user input.

The graph's logical member set must equal:

```text
{manifest-declared regular files} U {reserved filesystem manifest}
```

Any extra/missing content member is a verification failure.

## Explicit r24 fallback cases

r25 currently falls back to genuine r24 when any of the following is true:

- the source contains a sparse regular file;
- the source contains a special/device/socket/FIFO file not modeled by the manifest;
- a source path collides with `.__cmpct_r25_internal__`;
- path/file/count/logical-size manifest policy is exceeded;
- the internal complete-artifact tournament selects an inherited `CMPNX*` research archive.

The first cases protect semantics. The final case protects product identity: research bytes stay research bytes.
Fallback is therefore an explainable result, not silent feature disappearance or a magic-byte rewrite.

## Product API/CLI behavior

The canonical module owns these operations across r25 and r24:

- `build(root, archive)`;
- `strong_verify(archive)`;
- `list_members(archive)`;
- `read_member(archive, path)`;
- `extract(archive, destination, ...)`;
- `build_ablation(root, archive, mode)`.

CLI equivalents are `pack`, `verify`, `list`, `read`, `extract`, and `ablate`.

For r25, the reserved manifest is never exposed as a user file through `list_members` or extraction. `read_member`
resolves hardlinks and symlink target bytes from the authenticated manifest while regular content is decoded by
the selected content-profile reader. For r24, the API dispatches to the existing reference reader.

Research-only `CMPNX*` input fails with an explicit non-canonical profile result instead of entering the r24
reader under a false revision label.

## Compatibility and portability effect

This T03 design introduces reader-visible revision-25 semantics. It therefore **does not by itself claim shipped
native/platform support**. T01 owns the native and portability implementation required to consume these bytes
through the shared core.

Until that native work is imported and its conformance gates are green:

- r25 is a provisional integration-branch contract;
- r24 remains the released interoperability floor;
- the product builder emits exact r24 when r25 is unsupported/ineligible/non-winning;
- platform/browser documentation must not claim r25 support merely because the Python product facade can read it.

The manifest design is intentionally portable to T01: it is bounded deterministic MessagePack with no encoder
heuristics, and both content profiles have fixed dispatch magics. Native code needs one profile dispatcher, the
existing bounded graph decoders for the selected content profile, and one filesystem-manifest parser—not a copy
of the Python encoder/compiler.

## Research modules intentionally retained

Useful experimental code is not deleted merely because it is no longer the promoted entrypoint.

Retained for causal evidence/ablation:

- `entropygraph_v030_authoritative.py` — historical convergence facade; **not** imported by the canonical product;
- `entropygraph_v030_release_candidate.py` — complete-artifact research selector reused beneath the product boundary;
- `entropygraph_v030_prefixgraph.py` — semantic owner of the bounded PrefixGraph content grammar;
- `entropygraph_v030_geometry_overlay*.py` — reactor lineage and G0–G4 semantic owners;
- rejected/earlier Geometry and graph experiments referenced by the research notes.

`CMPNXP1`, `CMPNX11` and related research identities remain historically useful evidence. Canonical publication
uses only the fixed `CMP25*` identities or real `CMPCT24\0` fallback.

## Completion boundary for T03

T03 is product-architecture complete when:

1. the implementation and `docs/FORMAT.md` agree with this decision;
2. focused tests prove r25 round-trip/recovery/locality plus r24 fallback and research-magic refusal;
3. public-surface checks remain green;
4. T00 reconciliation is reflected in the final source head; and
5. T01/T02 consume this frozen contract for native/conformance and evidence work before T04 promotion.

This document does not grant release status. It removes the architectural ambiguity T03 owns so the remaining
release gates can test one explicit product contract instead of several overlapping experiment facades.
