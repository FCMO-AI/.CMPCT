# CMPCT platform integration sources

These files are packaging inputs for making `.cmpct` behave as a first-class archive/document type without changing revision-24 bytes or embedding a permanent ZIP shadow.

Implemented source contracts:

- Linux: Shared MIME-info registration with `.cmpct` glob and `CMPCT24\0` magic.
- Windows: per-user file association source with stable `FCMO.CMPCT.Archive` ProgID and a required packaged-native-browser substitution point.
- Apple: exported `com.fcmo.cmpct.archive` UTType plus document-role declaration for macOS/iOS application packaging.
- Android: `ACTION_VIEW` routing for the canonical/compatibility MIME names and a constrained octet-stream extension fallback.

These files are **not claims that platform applications ship yet**. They are deliberately handler-agnostic packaging contracts. The shipping browser/activity/document app must use the shared memory-safe native core and must validate archive magic/version after opening a file or URI; extension, MIME and UTType are routing metadata, not a security boundary.

`tests/test_portability_metadata.py` gates identifier consistency across these sources so the extension, MIME identity, ProgID/UTType and magic-validation invariant cannot drift independently.

Next portability milestones remain executable platform packages: Windows double-click browse/extract, Android DocumentsProvider tree/member streaming, Apple document-browser/Quick Look integration, and a Linux browser/mount path. Those acceptance gates should consume revision-24 conformance archives through the shared native API rather than adding platform-specific parsers.
