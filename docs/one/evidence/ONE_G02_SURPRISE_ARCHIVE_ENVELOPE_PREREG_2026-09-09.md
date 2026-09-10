# ONE-G0.2 complete Surprise archive envelope preregistration — 2026-09-09

Date: 2026-09-09 America/Mexico_City  
Experimental state: **ONE-G0.2**

## Mission lock

Genesis now has strong mechanism evidence for Law discovery, exact proof, native whole-root reconstruction and authenticated selective cones, but those mechanisms must not be stitched together after the fact and called a complete archive. Before the September 11 comparison, ONE needs a smallest honest **system seam** that can represent a source tree as an ordinary ONE Program, serialize it through the existing ONE wire, reopen it, address files by logical path and answer ranges without inventing a second compression ontology.

The first seam should be deliberately unambitious in compression: **Surprise-only fallback plus a Surprise manifest**. It establishes the complete-artifact denominator that future Law compilation must beat. It is not itself a claim that ONE has absorbed all historical CMPCT filesystem/recovery semantics.

## Hypothesis

A deterministic source tree containing regular files, directories and symbolic links can be represented using only the existing ONE grammar—Surprise, Concat/slicing and roots—such that:

- complete artifact bytes are measurable through the existing canonical experimental `ONE0` wire;
- reopening the wire reconstructs every regular file byte-exactly and verifies root SHA-256;
- a path/range request reconstructs only the requested range of the selected file through the existing `RangeEvaluator`, rather than reconstructing unrelated files;
- the manifest itself is ordinary Surprise, not a new reader opcode or hidden codec;
- unsafe paths and unsupported filesystem entry kinds fail closed;
- no ONE Law discovery is performed by the reader.

## Representation

The research archive Program has:

- one ordinary root named `@manifest` whose bytes are canonical JSON stored as Surprise;
- one root per regular file, named by a deterministic internal identifier (`f000000`, ...), backed by Surprise chunks and a Concat when multiple chunks are needed;
- manifest records sorted by relative POSIX path mapping logical paths to internal roots and recording the entry kind and minimal source semantics under test;
- directories and symlinks live only in the manifest because they contain no regular-file payload bytes.

The outer representation remains the existing ONE Program and existing `ONE0` wire. No `ARCHIVE`, `ZIP`, `MOSAIC`, `ZSTD`, or other reader-visible codec operation is introduced.

## Deliberate scope boundary

This G0.2 seam proves **complete regular-file byte identity + directories + symlink targets + safe logical path/range addressing**. It does not yet claim canonical preservation of ownership, timestamps, ACLs/xattrs, hardlink identity, sparse physical allocation, transactional generations, recovery parity or ZIP export. Those remain explicit Genesis gate capability/debt fields; they must not be silently marked as present merely because file bytes round-trip.

That limitation is intentional. A narrow honest complete seam is preferable to a last-minute 'full archive' claim that quietly loses CMPCT semantics.

## Falsifiers

`HOLD_SURPRISE_ARCHIVE_ENVELOPE` if any of the following occurs:

1. the same supported source tree does not produce byte-identical wire on repeated builds;
2. any regular file fails complete byte/SHA parity after wire decode;
3. any supported path/range returns bytes different from direct source slicing;
4. a range request evaluates an unrelated file root or requires complete reconstruction of the selected root merely to return a small slice;
5. manifest order or internal root assignment depends on filesystem enumeration order;
6. absolute paths, `.`/`..` components, NUL paths, escaping symlink extraction targets or unsupported special files are accepted without an explicit policy;
7. serialization uses anything other than the existing ONE wire/grammar for data representation;
8. the reader performs discovery;
9. tests claim filesystem/recovery semantics outside the deliberate scope above.

## Required hostile vectors

Before promotion, test at least:

- empty directory;
- empty regular file;
- nested regular files;
- a file larger than the Surprise chunk size, proving Concat/sliced range semantics;
- duplicate file contents (still stored independently in this fallback—dedup is future Law compilation, not an implicit special codec);
- safe relative symlink;
- traversal-like path rejection at manifest parse/extraction boundary;
- malformed manifest root, missing file root, length mismatch and root hash mismatch;
- repeat build determinism.

## Economic interpretation

The Surprise-only artifact is expected to be larger than raw logical file bytes because it pays Program, root, path, manifest and integrity overhead. That is useful: it creates a complete-system baseline against which Law compilation must demonstrate **net archive savings after metadata and integrity**, rather than quoting isolated payload savings.

No size/speed gate is preregistered for this fallback beyond bounded/no-pathological behavior. Its job is semantic integration. Performance promotion belongs to later Law-bearing archive candidates measured against this exact seam and the frozen CMPCT comparators.
