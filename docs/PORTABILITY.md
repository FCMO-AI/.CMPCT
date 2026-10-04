# CMPCT portability and ZIP-parity integration contract

Status: **released portability floor r24; provisional v0.30 r25/shared-reader integration active and still release-gated**.

CMPCT is not finished when its bytes are smaller than ZIP. A replacement archive format must also be
boring to use: tap or double-click it, see a tree, open individual members without unpacking unrelated
content, extract one or all members, and hand files to other applications. ZIP's installed-base
advantage is therefore an engineering requirement, not something the project may dismiss as
"ecosystem".

This document records the portability contract separately from `docs/FORMAT.md`. Revision 24 remains
the released interoperability floor; the v0.30 integration branch additionally exercises provisional
revision-25 profiles through one shared native portability layer. No r25 portability claim is shipped
until the exact frozen candidate closes T01 and the strict release lock accepts its platform receipts.

## Product requirement

A shipping CMPCT stack must make `.cmpct` behave as a first-class archive/document on supported
platforms:

1. the extension and magic are recognizable;
2. opening the file launches a CMPCT-capable archive browser rather than a text editor or generic
   unknown-file dialog when a handler is installed;
3. the browser exposes the logical directory tree without extracting the entire archive;
4. opening one member reads only the metadata/blobs required for that member whenever the storage
   representation permits it;
5. extracting the tree preserves CMPCT's stronger filesystem semantics where the destination supports
   them;
6. a legacy ZIP can be exported explicitly when an external system genuinely requires ZIP;
7. compatibility must not permanently duplicate every payload into a hidden ZIP shadow inside every
   `.cmpct` file.

The last rule matters. A permanent ZIP projection would make the default archive pay twice for data
solely to accommodate software that has not learned CMPCT. `export-zip` remains the compatibility
endpoint while native handlers and upstream integrations make CMPCT directly consumable.

## Provisional media type and sniffing

Until a public media-type registration is completed, integrations should use:

- canonical project MIME: `application/vnd.fcmo.cmpct`;
- compatibility alias: `application/x-cmpct`;
- filename extension: `.cmpct`;
- released revision-24 magic at offset zero: `CMPCT24\0`;
- provisional v0.30 canonical r25 magics: `CMP25G4\0` and `CMP25PG\0`.

Handlers must validate magic/version rather than trusting filename or MIME alone. A file manager may
supply `application/octet-stream` for an extension it does not know; a CMPCT application may offer an
explicit "Open CMPCT" picker for that case, but should not pretend every octet-stream is CMPCT.
Research-only `CMPNX*` identities are not canonical product revisions and must not be accepted merely
because the extension is `.cmpct`.

## Shared native archive-handler API

Android, Windows shell extensions, Apple document/Quick Look extensions, Linux desktop helpers and a
future libarchive integration should all sit on one memory-safe native core instead of implementing
format semantics independently.

Revision 24 continues to use the mature `native/cmpct-core/` foundation. The v0.30 integration branch
adds `native/cmpct-portable/` as one shared dispatcher across genuine r24 fallback plus both fixed r25
profiles. Platform integrations must consume that shared dispatcher rather than copy the r25
MessagePack/Geometry/PrefixGraph grammar.

The minimum read-only handler surface is:

- `open(source)` with bounded hostile-input validation;
- `archive_info()`;
- `list_children(path)` / `stat(path)`;
- `read(path)` for intentionally materialized small members;
- `read_range(path, offset, length)`;
- `open_member_stream(path)` for sequential zero/full-copy extraction;
- `extract_member(path, destination, policy)`;
- `extract_tree(destination, policy)`;
- `verify(path|archive)`;
- typed errors for unsupported revision/codec, corrupt metadata, resource limits and unsafe paths.

The mutation surface can follow once the read-only ABI is stable. Platform integrations must not parse
MessagePack/index/blob structures themselves after the shared core exists.

### Performance contract for the handler

The native handler is also the answer to current CLI startup losses. A mature ZIP utility does not
need to start CPython, import the encoder, load mutation code and initialize unrelated features merely
to list an archive. The native CLI and platform handlers must keep the read-only dependency cone
small and load optional codecs only when an archive actually requires them.

For compressed direct members, an implementation may temporarily decode one bounded member to serve a
range if the codec is not independently seekable, but it must never silently inflate the whole archive.
The current native Zstd/WAV-FLAC/Deflate paths follow that rule and cap one direct decode/reconstruction
at 256 MiB. Revision-24 fixed and CDC chunk maps are range-local in the shared core: a request decodes
only chunks intersecting the requested range. Revision-24 sparse maps are also range-local: holes are
synthesized as zeroes while only stored chunks in intersecting extents are decoded, so browsing a
sparse VM/disk image does not allocate or inflate its logical size.

For provisional r25, selected member operations must expose observed decoded-context accounting and stay
inside the <=8x release policy. Missing locality data is a hard evidence failure, not a numeric zero.
The canonical product API exercises the same logical member-read operation for r25 and genuine r24
fallback so platform claims cannot hide behind research-era “not applicable” labels.

## Revision-25 filesystem portability contract

The authenticated r25 filesystem manifest is part of complete archive bytes and must survive the same
platform boundary as regular content. Shared readers/materializers therefore preserve the following
cross-platform rules:

- canonical user paths are safe relative paths and the reserved r25 internal namespace is unavailable
  to user input;
- `mtime_ns` is a bounded **signed i64** nanosecond value, including valid pre-1970 timestamps;
- safe symlink admission/extraction rejects escape under **both POSIX and Windows lexical semantics**,
  independent of the host currently reading the archive;
- slash and backslash are both interpreted as separators for traversal checks;
- POSIX absolute paths, Windows drive/root/UNC forms and any `..` component are rejected in safe mode;
- hardlinks point directly to an earlier regular-file owner, keeping dependency depth one and avoiding
  alias cycles;
- metadata remains authenticated even when a destination filesystem/user cannot apply uid/gid/xattrs or
  exact timestamps; host application of those attributes is best-effort and must never fabricate values.

Footnote: validation and materialization are separate trust boundaries. The shared native materializer
repeats the portable link-target rule immediately before `symlink()` and restores signed timestamps with
checked add/sub around the Unix epoch, so an archive cannot become unsafe or semantically different merely
because it moved between operating systems.

## Android

Android is a first-class target, not a future compatibility note.

### Tap/open behavior

The Android application should declare `ACTION_VIEW` handling for the CMPCT MIME aliases and accept
readable `content:` URIs. The activity must inspect the revision magic itself before opening the
archive. When a provider reports only a generic binary MIME type, the app should still permit explicit
selection through the Storage Access Framework and validate by magic.

### Archive-as-directory behavior

The preferred Android integration is a `DocumentsProvider` backed by the shared native CMPCT reader:

- archive directories map to Android document directories;
- `queryChildDocuments` enumerates direct logical children from the authenticated archive tree;
- `openDocument` streams a selected logical member through the native read/range API;
- seek/range-capable members should not require whole-archive extraction;
- sparse logical holes must stay cheap; callers requesting a small region must not materialize the whole sparse member;
- virtual/reconstructed files remain ordinary readable documents to client apps;
- write flags stay disabled until transactional mutation semantics are exposed safely through the
  native ABI.

This gives Android's system document UI a real tree rather than forcing the user to "extract all"
before they can inspect a single file.

### Android distribution reality

An application can register itself as a handler, but recognition of an unknown extension is not
magically injected into every unrelated third-party file manager. Robust Android coverage therefore
has three layers:

1. CMPCT app + explicit Storage Access Framework opening works without upstream OS changes;
2. MIME-correct senders/providers can invoke the app directly;
3. broader ecosystem recognition should be pursued upstream in commonly used file-manager/archive
   libraries once the native core and format specification are stable.

### Current v0.30 Android boundary

The Android integration now links its parser-free JNI shim against `libcmpct_portable` rather than the
r24-only core directly. This is an architectural integration fact, **not yet a release-complete platform
claim**. The repository carries r25 Android instrumentation under
`integrations/android/app/src/androidTest/java/ai/fcmo/cmpct/CmpctAndroidR25Test.java`, and
`.github/workflows/android.yml` requires the packaged JNI dependency to be relocatable and to resolve to
the shared portable library rather than silently falling back to an independent/r24-only parser path.

The earlier r24 Android 10 emulator acceptance remains useful evidence: a real APK was built/installed,
revision-24 conformance archives opened through JNI into the Rust core, a read-only `DocumentsProvider`
root was exposed, and a member streamed byte-exactly. v0.30 must now rerun the relevant Android/shared
reader matrix on the exact frozen r25/r24 candidate.

**Physical ARM64 Android evidence remains mandatory for v0.30 release.** An emulator-only green is not a
substitute, and no document should describe physical-device acceptance as complete until the exact
platform receipt exists.

## Linux / freedesktop desktops

Linux integration should install a Shared MIME-info definition containing both the `.cmpct` glob and
revision magic. The repository carries the source registration under `integrations/linux/`.

The next layers are:

- a desktop application association for the native CMPCT browser;
- thumbnail/metadata helpers where useful;
- optional FUSE/GVfs-style mount integration for applications that expect directories;
- upstream libarchive support after the normative format and native parser are defensible.

Upstream libarchive support is strategically important because it turns CMPCT support into inherited
support for many downstream tools instead of a separate shell plugin for every desktop.

## Windows

The Windows deliverable should register a stable ProgID for `.cmpct` and open files in the CMPCT
archive browser. Later shell integration may add Explorer commands, icons/thumbnails and a virtual
filesystem/mount surface, but the first acceptance gate is simpler: double-click, browse tree, open a
member, extract one/all.

File association must point to the native handler/browser, not to a Python source checkout. The r25
safe-symlink rule is intentionally host-independent so an archive validated elsewhere cannot become a
Windows traversal vector when finally materialized here.

## Apple platforms

Apple integrations should declare a CMPCT Uniform Type Identifier conforming to document/data types,
associate `.cmpct` with that type, and register document support. A document-browser application can
then open CMPCT from Files/iCloud providers, while Quick Look thumbnail/preview extensions can provide
archive metadata or a compact file listing without full extraction.

The macOS Finder opening path and the iOS/iPadOS document-browser path should use the same native core
and conformance vectors.

## Web and remote contexts

A future WASM build of the same native parser is preferable to a separate JavaScript parser. CMPCT's
explicit index and range-read semantics make browser/object-store access a natural target once remote
range sources and partial verification are implemented.

## ZIP parity gates

ZIP keeps a real advantage until all of the following are true for a supported platform:

- **size:** no unexplained material loss on the parity corpus;
- **library speed:** no stable material ZIP win for create/extract/read at equivalent semantics;
- **launch speed:** native CLI/handler startup is competitive with mature ZIP tooling;
- **selective access:** one member and byte ranges do not require whole-archive inflate;
- **filesystem fidelity:** CMPCT continues preserving semantics ZIP commonly loses;
- **recovery/integrity:** performance work does not weaken bounded validation or committed-generation
  recovery;
- **opening UX:** tap/double-click launches a usable archive tree;
- **member UX:** one member can be opened/shared without extracting unrelated content;
- **legacy escape hatch:** `export-zip` remains available and tested.

For v0.30, ZIP/export evidence must cover every product outcome that can actually publish: genuine r24
fallback, Geometry-r25 and PrefixGraph-r25. When semantics cannot be represented honestly in stock ZIP
(for example safe symlink behavior under the selected export policy), the exporter must return a typed
unsupported result rather than silently changing meaning.

A benchmark where ZIP wins should become either a fixed regression, a documented irreducible platform
constraint, or a deliberately rejected tradeoff backed by evidence. "ZIP is old and ubiquitous" is
not a reason to stop engineering.

## Current implementation status

Implemented on released/inherited r24 paths:

- revision-24 random/member/range reads in the Python oracle;
- extraction and ZIP export;
- a fair parity harness separating library and fresh-process timing;
- Linux MIME registration source;
- Windows `.cmpct` ProgID/OpenWith/Capabilities association contract and Apple exported UTType/document declarations;
- explicit portability contract and release gates;
- a canonical Android read-only preview under `integrations/android/` with `ACTION_VIEW`, Storage Access Framework import, a `DocumentsProvider`, JNI bindings, four declared Android ABIs, and an Android 10 emulator acceptance workflow;
- Android emulator conformance for revision-24 MIME/extension routing, magic refusal, RAW/Zstd/Deflate archive reads, provider enumeration/member streaming, and relocatable packaged native-library dependencies;
- the mature memory-safe Rust revision-24 core described in `docs/NATIVE_CORE.md`, including direct codecs, fixed/CDC, sparse, pack, selected virtual-ZIP semantics and fixed builder-independent conformance vectors.

Implemented on the **provisional v0.30 integration branch**, pending exact-candidate release evidence:

- `native/cmpct-portable/`, one shared dispatcher for genuine r24 plus fixed canonical r25 G0–G4 and PrefixGraph profiles;
- opaque C ABI and native CLI surfaces over that dispatcher;
- builder-independent revision-25 golden/conformance material under `tests/conformance/v030-r25-canonical.json` with independent regeneration checks;
- canonical r25 filesystem-manifest admission, user/content-graph identity cross-checking, recovery, member streaming and locality observability;
- native materializer parity for host-independent safe symlinks and signed i64 timestamps;
- parser-free Android JNI linkage to `libcmpct_portable` with explicit rejection of a packaged direct `libcmpct_core` dependency;
- r25 Android instrumentation coverage in source;
- release-path CI that binds canonical profile isolation, native parity and Android to the same shared product contract.

These are implementation facts, **not yet durable v0.30 release receipts**.

## Still required before v0.30 portability can close

- exact-fingerprint `native-r25` evidence proving G0–G4 and PrefixGraph parity, builder-independent goldens, recovery and shared-core use;
- exact-fingerprint `zip-portability` evidence proving stock ZIP tree equality where supported for r24 fallback, G0–G4 and PrefixGraph plus atomic publication;
- exact-fingerprint `platform-android` evidence for the required platform matrix, including **physical ARM64 Android**;
- current-head hostile/fuzz/resource/path coverage across the shared r25 parser/materializer;
- evidence that selective member operations report truthful observed locality and remain inside the <=8x law;
- current docs/conformance agreement after all final source changes;
- strict release-lock acceptance of those receipts on the exact frozen candidate.

Longer-term 1.0 portability remains broader than v0.30 and still includes:

- Windows shell/browser package;
- Apple document/Quick Look package;
- Linux browser/FUSE/GVfs integration;
- upstream libarchive support;
- WASM reader.

`docs/NATIVE_CORE.md` is the detailed handoff for the native capability and safety boundary.
`integrations/android/README.md` remains the Android-specific acceptance handoff and must preserve the
distinction between emulator-proven preview functionality, provisional r25 integration, and
release-complete physical-device support.

Footnote: v0.30 portability is intentionally a promotion gate, not polish. The encoder is not allowed to
publish a representation that Python can read but the shared native/platform boundary cannot independently
verify and materialize under the same semantics.
