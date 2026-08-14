# CMPCT portability and ZIP-parity integration contract

Status: **active pre-1.0 release gate / revision 24 unchanged**.

CMPCT is not finished when its bytes are smaller than ZIP. A replacement archive format must also be
boring to use: tap or double-click it, see a tree, open individual members without unpacking unrelated
content, extract one or all members, and hand files to other applications. ZIP's installed-base
advantage is therefore an engineering requirement, not something the project may dismiss as
"ecosystem".

This document records the portability contract separately from `docs/FORMAT.md`. It adds no on-disk
fields and does not change revision 24.

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
- revision-24 magic at offset zero: `CMPCT24\0`.

Handlers must validate magic/version rather than trusting filename or MIME alone. A file manager may
supply `application/octet-stream` for an extension it does not know; a CMPCT application may offer an
explicit "Open CMPCT" picker for that case, but should not pretend every octet-stream is CMPCT.

## Shared native archive-handler API

Android, Windows shell extensions, Apple document/Quick Look extensions, Linux desktop helpers and a
future libarchive integration should all sit on one memory-safe native core instead of implementing
format semantics independently.

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

## Android

Android is a first-class target, not a future compatibility note.

### Tap/open behavior

The Android application should declare `ACTION_VIEW` handling for the CMPCT MIME aliases and accept
readable `content:` URIs. The activity must inspect the revision magic itself before opening the
archive. When a provider reports only a generic binary MIME type, the app should still permit explicit
selection through the Storage Access Framework and validate by magic.

### Archive-as-directory behavior

The preferred Android integration is a `DocumentsProvider` backed by the native CMPCT core:

- archive directories map to Android document directories;
- `queryChildDocuments` enumerates direct logical children from the CMPCT index;
- `openDocument` streams a selected logical member through the native read/range API;
- seek/range-capable members should not require whole-archive extraction;
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

The project should not claim "native Android support" until a real APK/AAB built from this repository
can open a revision-24 conformance archive, browse its tree, stream at least one member, and extract it
correctly on an emulator/device test.

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

File association must point to the native handler/browser, not to a Python source checkout.

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

A benchmark where ZIP wins should become either a fixed regression, a documented irreducible platform
constraint, or a deliberately rejected tradeoff backed by evidence. "ZIP is old and ubiquitous" is
not a reason to stop engineering.

## Current implementation status

Implemented today:

- revision-24 random/member/range reads in the Python oracle;
- extraction and ZIP export;
- a fair parity harness separating library and fresh-process timing;
- Linux MIME registration source;
- explicit portability contract and release gates;
- an initial memory-safe Rust core under `native/cmpct-core/` that authenticates/decodes the revision-24 primary index, enumerates logical entries, rejects lexical path aliases, and exposes a tested opaque C ABI for open/close/revision/count/entry metadata/path. CI cross-checks it against the Python oracle and exercises the produced shared library from a non-Rust caller.

Not yet implemented and therefore **not to be claimed as shipped support**:

- complete memory-safe native reader/writer ABI beyond the implemented primary-index/open/enumeration seed (full hostile structural validation, recovery, member/range streaming, codec decoding, extraction and mutation are still pending);
- Android application/DocumentsProvider;
- Windows shell/browser package;
- Apple document/Quick Look package;
- Linux browser/FUSE/GVfs integration;
- upstream libarchive support;
- WASM reader.

These items are now part of the canonical path to 1.0 rather than optional post-1.0 polish.
