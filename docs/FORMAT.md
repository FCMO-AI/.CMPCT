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
