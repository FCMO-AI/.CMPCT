# CMPCT format revision 24 — working specification

This is a **working pre-1.0 contract**, derived from the executable reference implementation. The
implementation is authoritative when this document and code disagree; such disagreement is a bug in
the documentation and should be fixed in the same change.

## 1. Archive structure

A revision-24 file is laid out conceptually as:

```text
HEAD HEADER
PRIMARY COMPRESSED INDEX
SELF-DESCRIBING BLOB RECORDS...
OPTIONAL TRANSACTION DELTAS / GENERATIONS...
TAIL COMPRESSED INDEX
COMMIT FOOTER
```

The primary and tail indexes carry the same authoritative logical state at a checkpoint. The footer
is the commit marker for the latest complete generation. Readers may fall back to the other index or
blob scanning when damage prevents normal opening.

## 2. Magic and version

Current reference constants:

- header magic: `CMPCT24\0`
- footer magic: `CMPTF24\0`
- blob magic: `CMA4`
- format revision: `24`

Pre-1.0 magic/revision changes are allowed. 1.0 must define compatibility rules before freezing.

## 3. Logical entries versus physical blobs

Logical filesystem entries are separate from physical stored blobs. Multiple paths can therefore
reference one content object without storing duplicate bytes. Entry kinds currently include:

- regular file;
- directory;
- symbolic link;
- hardlink.

Regular files can use multiple storage descriptions, including one blob, chunk lists,
content-defined chunks, sparse extents, virtual nested archives, and packed microblocks.

## 4. Blob records

Every physical blob record stores enough framing information to be scanned independently, including:

- codec identifier;
- flags;
- uncompressed and compressed sizes;
- codec metadata length;
- CRC32 for fast corruption detection;
- SHA-256 for strong content identity/integrity.

Current codec IDs in the prototype are RAW, ZSTD, WAV/FLAC, ZSTD-with-dictionary, and raw DEFLATE.
The format must remain codec-agile; IDs are never inferred from file extensions.

## 5. Chunking and seeking

Large files may be represented as independently decodable chunks. Revision 24 additionally supports
content-defined chunking. The **reader never needs the chunking algorithm**: logical chunk lengths and
blob references are recorded explicitly. This allows the encoder's boundary algorithm to evolve
without invalidating old archives.

## 6. Sparse files

Sparse logical files may record data extents separated by holes. A reader returns zeros for holes;
an extractor should recreate sparse holes when the destination filesystem supports them instead of
materializing the entire logical zero range.

## 7. Nested archives

ZIP/WHL objects can be stored as virtual recipes when CMPCT can reconstruct the original nested
container byte-for-byte from canonical payloads plus container structure. If virtualization is not
profitable or exact reconstruction is not justified, the nested archive remains an ordinary blob or
packed object. Looking inside an archive is an optimization, not a semantic requirement.

## 8. Integrity

Normal reads use CRC32 as a cheap corruption check where applicable. `verify` performs SHA-256-based
strong validation across logical files/blobs. Index/footer hashes protect authoritative metadata.

## 9. Transactional generations

Updates append new data and metadata before a final commit footer. An incomplete tail is not a
committed generation; readers recover the newest valid prior generation. Checkpoints periodically
collapse long delta chains.

## 10. Extraction safety

The reference extractor rejects path traversal and unsafe output paths. Symlink extraction is
conservative by default and can require an explicit unsafe override. Resource limits such as maximum
materialized bytes exist to reduce decompression-bomb risk.

## 11. Compatibility endpoint

CMPCT can export a normal Deflate ZIP. When exact reusable Deflate streams are already present, the
export path copies them rather than inflate/recompressing them. ZIP compatibility is deliberately an
endpoint and does not constrain the canonical CMPCT representation.

## 12. 1.0 requirements

Before format 1.0, this document must become a byte-level normative specification with:

- canonical integer encodings and bounds;
- complete index schema;
- codec registry and capability negotiation;
- endianness and size limits;
- deterministic archive rules;
- Unicode/path normalization rules;
- xattr/ACL/platform metadata semantics;
- encrypted archive and authenticated-metadata design;
- streaming/remote range-read contract;
- split-volume rules;
- backward/forward compatibility policy;
- fuzz corpus and conformance vectors.

---

# Provisional format revision 25 — v0.30 integration contract

Status: **integration-branch contract, not a released/shipped support claim**.

Revision 25 productizes the proven v0.30 reconstruction-graph work without pretending historical
`CMPNX*` research grammars are canonical CMPCT revisions. The architecture decision and semantic-ownership map
live in `docs/V030_CANONICAL_PRODUCT_ARCHITECTURE.md` and `docs/V030_CONVERGENCE_RULES.md`.

## 13. Revision-25 profiles and magic

Revision 25 currently permits two complete content profiles:

| Profile | Header magic | Tail magic | Content semantics |
|---|---|---|---|
| Geometry-Mosaic | `CMP25G4\0` | `C25G4TL\0` | G0–G4 physical Geometry over the bounded Mosaic/pre-fallback graph |
| PrefixGraph depth-1 | `CMP25PG\0` | `C25PGTL\0` | direct whole-file roots plus bounded raw-prefix Zstd references |

Both header/tail identities are exactly eight bytes.

`CMPNX*` identities—including `CMPNX11` and `CMPNXP1`—remain research-only. A canonical r24/r25 reader
must reject or explicitly classify them as research input; it must not infer revision 24 merely because
the magic is not one of the revision-25 identities.

## 14. Complete-artifact profile and product selection

Revision 25 has two nested exact-selection boundaries.

**Inside the r25 tournament:**

1. every r25 candidate reconstructs the exact same staged logical content tree;
2. Geometry and PrefixGraph are priced as complete archives, including metadata and recovery copies;
3. independent mechanism savings are never added arithmetically;
4. selected PrefixGraph references have dependency depth <= 1;
5. selected decoded-context amplification remains <= 8x;
6. a real r25 candidate must be **strictly smaller** than the accepted-v0.29 complete historical research floor before it is eligible for product publication.

**At the product boundary:**

7. the encoder builds a genuine canonical r24 artifact for the same original filesystem tree and the r25 tournament as independent complete candidates;
8. those two candidates may execute concurrently so the exact comparison does not impose an avoidable serial double-encode latency;
9. r25 publishes only when it is a canonical `CMP25*` profile **and strictly smaller than genuine r24**;
10. an exact r24/r25 byte-size tie conservatively publishes r24;
11. unsupported r25 filesystem shapes or an r25 tournament result that is research-only/non-winning publish the already-built genuine r24 artifact.

No estimate, staged-tree surrogate, or independent-savings sum may replace the genuine r24-vs-r25 complete-product comparison.

Footnote: accepted v0.29 remains the immutable causal compression floor for the historical 15-workload mechanism gate. Genuine r24 is the compatibility/product no-regression floor. They intentionally answer different questions and neither may be silently substituted for the other.

## 15. Authenticated filesystem manifest

The G0–G4 and PrefixGraph research grammars originally authenticated path + regular-file bytes, not the
full filesystem semantics already preserved by canonical r24. Revision 25 closes that gap with one
reserved logical member:

```text
.__cmpct_r25_internal__/filesystem-v1.msgpack
```

The manifest is stored as an ordinary content-profile member. Its exact bytes are therefore charged to
the complete archive, authenticated by the selected graph, and recovered through that profile's normal
authenticated metadata/tail path.

The manifest top-level MessagePack map is:

```text
{
  "v": 1,
  "profile": "cmpct-r25-filesystem-manifest-v1",
  "internal_path": ".__cmpct_r25_internal__/filesystem-v1.msgpack",
  "entries": [...]
}
```

Each `entries` row has exactly eight fields:

```text
[path, kind, mode, mtime_ns, uid, gid, xattrs, extra]
```

where:

- `path` is one safe canonical relative path;
- `kind` is one of `"f"` (regular), `"d"` (directory), `"l"` (symlink), or `"h"` (hardlink);
- `mode`, `uid`, and `gid` are bounded non-negative exact integers subject to reader policy;
- `mtime_ns` is a bounded **signed i64** nanosecond timestamp; negative/pre-1970 values are valid and must not be self-rejected by a conforming reader;
- `xattrs` is a list of `[name: str, value: bytes]` pairs;
- regular-file `extra` is `[logical_size: int, sha256: 32-byte bytes]`;
- directory `extra` is `nil`;
- symlink `extra` is the link target string;
- hardlink `extra` is the path of an **earlier regular-file owner**.

The direct-to-regular hardlink rule makes hardlink chains and cycles impossible by grammar and keeps
hardlink dependency depth exactly one.

The current product implementation caps the encoded manifest at **8 MiB** and applies the same finite
entry/path policies as the streamed r25 reader. The entry-count limit is enforced during source traversal,
not merely after building an unbounded in-memory manifest.

Symlink target admission is host-independent: the same target must be safe under both POSIX and Windows lexical interpretation. Backslash and slash are treated as separators for escape analysis; POSIX absolute paths, Windows drive/root/UNC forms, and any `..` component under either spelling are rejected by safe extraction.

Footnote: an archive admitted on one operating system must not become traversal-capable merely because the same authenticated link bytes are materialized by another platform later.

## 16. Content/manifest consistency and tree identities

For a valid revision-25 archive, the selected content profile's authenticated logical-member set must be
exactly:

```text
{all manifest kind="f" paths} U {reserved filesystem manifest path}
```

No directory, symlink, or hardlink alias needs an independent graph payload. Conversely, every regular
manifest entry must have a content-profile descriptor whose logical length and SHA-256 exactly match the
manifest declaration.

An extra content member, missing regular content member, mismatched length/hash, duplicate manifest path,
reserved-namespace collision, malformed xattr, invalid path, or invalid hardlink owner is a
format/verification failure.

The reserved internal manifest is not exposed as a user member by canonical list/extract APIs.

Canonical verification distinguishes three identities:

- `tree_sha256` / `user_tree_sha256`: the user-visible semantic tree used for cross-version product identity;
- `content_graph_tree_sha256`: the selected r25 graph identity, including the reserved manifest member;
- `filesystem_manifest_sha256`: the exact authenticated manifest-byte identity.

A reader must reconstruct and verify user-visible regular members before accepting the user-tree identity; it may not trust a manifest-declared digest without checking graph reconstruction.

## 17. Revision-25 resource/locality requirements

The promoted reader inherits the v0.30 streamed-reader limits. At minimum:

- PrefixGraph dependency depth <= 1;
- selected per-member decoded-context amplification <= 8x;
- maximum physical decode unit <= 8 MiB;
- bounded metadata and logical declaration sizes;
- bounded physical decode units and decoder working memory;
- bounded node/record/file counts;
- strict path validation and duplicate refusal;
- authenticated primary/tail recovery;
- physical/logical hash refusal on corruption;
- transactional extraction publication and rollback.

The reader does **not** need Geometry nomination, separator search, PrefixGraph anchor search, similarity
search, or portfolio/fallback heuristics. Those remain encoder policy.

Canonical profile dispatch must not depend on process-global mutation of research-module identities. The current release product reuses the exact semantic-owner source files inside isolated canonical module namespaces, so research imports retain their historical identities while canonical operations resolve fixed `CMP25*` profiles.

## 18. Explicit revision-24 fallback semantics

Revision 25 intentionally declines source shapes that it cannot yet preserve without weakening r24.
The canonical builder publishes a real `CMPCT24\0` archive when r25 is unsupported or does not win the complete-product tournament, including:

- sparse regular files until r25 has native sparse graph semantics rather than materialized zeroes;
- unsupported special/device/socket/FIFO entries;
- user paths colliding with the reserved r25 internal namespace;
- manifest/path/file/logical-size declarations above policy;
- source path/metadata text that cannot be represented portably by the bounded r25 MessagePack grammar;
- an internal tournament result whose actual bytes are research-only `CMPNX*`;
- any canonical r25 artifact whose exact byte size is greater than or equal to genuine r24 for the same original filesystem tree.

Fallback means using the exact independently built r24 artifact. It never means rewriting an r25/research magic to look like r24.

## 19. Revision-25 portability/conformance boundary

These bytes are reader-visible and therefore require the normal promotion gates before release:

- independent fixed-byte r25 golden vectors;
- hostile parser/resource mutations for both profile grammars and the filesystem manifest;
- shared native-reader parity for every canonical profile and genuine r24 fallback;
- signed timestamp and host-independent symlink safety parity through extraction/materialization;
- primary/tail recovery and operation-derived locality tests;
- ZIP/export interoperability with truthful unsupported-semantics behavior;
- platform/Android integration through the shared portable reader rather than independent parsers;
- direct-base performance evidence under `docs/V030_RELEASE_GATES.md`.

One executor owns the remaining v0.30 implementation and evidence dependency graph on `agent/v030-authoritative-integration`; CI/platform/native tooling provide independent execution evidence, not separate design authority. Until the exact frozen candidate satisfies all release-lock receipts, revision 24 remains the released interoperability floor.
