# CMPCT v0.30 native portability contract

Status: T01 implementation contract for `agent/v030-coop-native-portability`.

> Footnote: this document is additive. `docs/NATIVE_CORE.md` remains the historical contract for the mature revision-24 core; this note describes the shared dispatch layer added for v0.30 and deliberately does not reinterpret old r24 guarantees.

## 1. One parser boundary, three release outcomes

`native/cmpct-portable` is the shared memory-safe reader surface used by the portable CLI, C ABI, and Android JNI bridge.

Release identities are explicit:

| bytes | native profile | reported revision | product meaning |
|---|---|---:|---|
| `CMPCT24\0` | `r24` | 24 | mature revision-24 archive delegated to `cmpct-core` |
| `CMP25G4\0` | `g04-r25` | 25 | canonical G0-G4/Geometry revision-25 archive |
| `CMP25PG\0` | `prefixgraph-r25` | 25 | canonical PrefixGraph revision-25 archive |

Research identities remain decodable only as diagnostic/conformance inputs:

- `CMPNXG4\0` -> `research-g04`, revision **0**;
- `CMPNXP1\0` -> `research-prefixgraph`, revision **0**.

They are never silently promoted to revision 25. Android's user-facing import registry accepts only the three release identities above.

> Footnote: revision `0` is intentionally not a historical format revision. It is a hard API signal that the bytes are an experiment oracle rather than a publishable CMPCT release archive.

## 2. Revision 24 is delegated, not reimplemented

The dispatcher opens `CMPCT24\0` with `cmpct_core::Archive` and forwards range reads to the mature r24 implementation. No r24 MessagePack/blob grammar is copied into `cmpct-portable`.

The existing `native/cmpct-core` C ABI remains unchanged. `cmpct-portable` is additive and therefore cannot force an existing r24 integration to migrate just to retain its old behavior.

## 3. Revision-25 reconstruction grammar

The low-level readers are intentionally narrower than the encoder/search side. They implement only deterministic inverse operations and authenticated admission.

### G0-G4 / Geometry

The native G0-G4 reader supports the v0.30 bounded inverse grammar:

- physical codecs: raw, zstd, pinned Preflate reconstruction;
- direct logical nodes;
- depth-1 delta;
- bounded packed delta;
- bounded multi-base mosaic;
- bounded packed mosaic;
- lane geometry inverse;
- delimiter geometry inverse;
- hierarchical geometry inverse, plain and prefix-plane forms.

It enforces authenticated duplicate metadata recovery, physical record contiguity, Merkle leaf binding, payload SHA-256, physical CRC/SHA, logical-node SHA, file SHA, and tree SHA.

### PrefixGraph

The PrefixGraph reader supports:

- direct zstd members;
- depth-1 prefix-dictionary members;
- authenticated primary/tail metadata recovery;
- payload and logical SHA-256 checks;
- tree SHA verification.

The dependency depth remains one. A prefix member can depend on a direct anchor; chained prefix dependencies are rejected.

> Footnote: canonical and research identities share these reconstruction implementations. Identity constants are isolated in `src/identity.rs` specifically so a framing change cannot fork the measured decode grammar.

## 4. Dual-metadata recovery

Both r25 profiles authenticate primary and tail metadata independently.

Admission rules:

1. if both copies authenticate and agree, use them;
2. if only primary authenticates, recover from primary;
3. if only tail authenticates, recover from tail;
4. if neither authenticates, reject;
5. if both authenticate but disagree, reject;
6. the authenticated tail must bind the physical payload endpoint, preventing an accepted metadata copy from silently describing a different appended payload layout.

A valid redundant copy is recovery, not permission to ignore payload corruption. Every physical/context byte touched by a member read is still authenticated.

## 5. Canonical r25 filesystem manifest

Canonical `CMP25*` archives layer product filesystem semantics above the graph reader using the authenticated ordinary member:

`.__cmpct_r25_internal__/filesystem-v1.msgpack`

The native wrapper:

- parses the fixed `cmpct-r25-filesystem-manifest-v1` schema;
- forbids user paths in the reserved internal namespace;
- requires the graph content set to equal regular files plus the manifest itself;
- cross-checks every regular file's size/SHA against authenticated graph metadata before exposing the archive;
- hides the internal manifest from public enumeration;
- resolves backward-only hardlinks and rejects non-file owners;
- exposes directories, files, symlinks, hardlinks, mode, nanosecond mtime, uid/gid and xattrs as filesystem metadata.

Regular-file and xattr payload identities require true MessagePack binary values. A UTF-8 string with the same bytes is not accepted as a binary digest/blob.

## 6. Resource and locality policy

Metadata and reconstruction are bounded before hostile declarations can drive allocation.

Important ceilings include:

- metadata decode unit: 8 MiB;
- MessagePack nesting: 64;
- MessagePack nodes: 1,000,000;
- G0-G4 chunk: 512 KiB;
- G0-G4 decode unit: 8 MiB;
- declared decoder memory: 96 MiB;
- mosaic bases: 4;
- residual pack: 256 KiB;
- bounded record/node caches;
- maximum member read amplification: **8x**.

`member-stats` reports both logical bytes and unique decoded-context bytes. The <=8x gate is checked from actual context consumed by the native read, not only from an encoder declaration.

The release locality contract is **member-selective**, not arbitrary sub-member random access. r25 range reads authenticate the selected member while copying only the requested window. r24 retains its mature exact range implementation.

## 7. C ABI

Public declarations live in:

`native/cmpct-portable/include/cmpct_portable.h`

The surface provides:

- open / close;
- truthful release revision;
- entry count, metadata, UTF-8 path;
- bounded range reads;
- whole-member convenience reads with locality stats;
- profile verification.

The archive handle is opaque to C/C++ callers. Status codes distinguish I/O, format, resource-limit, UTF-8, range, unsupported-operation, authenticated-integrity, and panic-boundary failures.

> Footnote: the Rust implementation catches unwinds at exported entrypoints. A malformed archive may return an error; it must not unwind through C/JNI.

## 8. CLI

`cmpct-portable` exposes:

```text
cmpct-portable info <archive>
cmpct-portable list <archive>
cmpct-portable verify <archive>
cmpct-portable read <archive> <member>
cmpct-portable member-stats <archive> <member>
cmpct-portable extract <archive> <destination>
cmpct-portable export-zip <archive> <destination.zip>
```

`read` writes only member bytes to stdout. Diagnostics and locality measurements have separate commands so the reader remains safe in pipelines.

Extraction is transactional: content is reconstructed into a sibling staging tree and becomes the destination only after the archive operation succeeds. Existing destinations are backed up for the commit step and restored on publication failure.

## 9. ZIP compatibility export

The compatibility exporter emits an ordinary Deflate ZIP readable by stock ZIP implementations.

- regular files are materialized as files;
- hardlinks are materialized as regular files because ZIP has no portable hardlink semantic;
- directories are represented as ZIP directories;
- symlinks are currently refused rather than silently converted into regular text files.

That refusal is intentional: compatibility must not become data-semantic corruption.

## 10. Android

Android remains parser-free above Rust:

`Java -> cmpct_jni.cpp -> libcmpct_portable.so -> cmpct-portable -> {cmpct-core | canonical r25 reader}`

`integrations/android/build-native.sh` cross-compiles the portable cdylib for:

- arm64-v8a;
- armeabi-v7a;
- x86_64;
- x86.

The JNI method signatures remain stable for the app. The linker dependency changes from the r24-only `libcmpct_core.so` to `libcmpct_portable.so`.

Android CI checks the packaged ELF's `DT_NEEDED` table to require `libcmpct_portable.so`, reject a direct `libcmpct_core.so` dependency, and reject host filesystem paths. The existing Android 10 x86_64 emulator test remains the executable device gate; all four ABIs are compiled in the APK build.

The import registry performs a cheap eight-byte release-magic classification before native open and then requires the native-reported revision to agree with that magic. This prevents research `CMPNX*` archives from becoming user-visible DocumentsProvider roots.

## 11. Conformance evidence model

`tests/conformance/v030-r25-portable.json` contains **builder-independent research-grammar** byte vectors. They cover reconstruction semantics without claiming final CMP25 release framing.

`tests/native_v030_portable.py` exercises those exact bytes through both the Python reference reader and Rust, plus:

- logical byte/SHA identity;
- <=8x member locality;
- primary-damaged / tail-valid recovery;
- tail-damaged / primary-valid recovery;
- both-metadata-damaged refusal;
- payload-corruption refusal;
- C ABI enumeration/read/verify;
- transactional extraction;
- stock Python `zipfile` export consumption.

Final canonical CMP25 golden receipts are a cross-lane dependency on T03's frozen productization handoff. Until T03 reaches `REVIEW`, research vectors must not be relabeled as release goldens.

## 12. Known platform fidelity boundary

The manifest parser preserves mode, nanosecond mtime, uid, gid, and xattrs. Portable extraction restores mode/mtime where the host API permits it and keeps ownership/xattr data available to platform-specific restoration code. Symlink creation is supported on Unix; Windows refuses it until the archive contract can distinguish a link-to-file from a link-to-directory without guessing.

A refusal is preferable to a false fidelity claim. T01 handoff evidence must state any remaining host-specific metadata setter gap rather than describing parsed metadata as restored metadata.
