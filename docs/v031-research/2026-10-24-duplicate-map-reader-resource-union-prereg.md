# CMPCT v0.31 — duplicate-key rejection × Reader constructor resource ownership

Status: **prospective integration test, before source mutation**. Date: 2026-10-24.
Base: PR #316 `1ed92767e6438d9bb8835ddc7ae27160440c2014` (authenticated duplicate MessagePack root fields reject in Python/preflight/Rust).
Independent owner: PR #283 `7ac0376ffed9` (Reader constructor closes owned fd/mmap on failed open).
Published release v0.30.0, on-disk revision 24 unchanged. This branch does not alter either owner.

## Scientific question and predicted falsifier
Can a validly authenticated but semantically ambiguous index, rejected by PR #316's Python Reader, leave an acquired descriptor live while an exception and traceback are retained? Ordinary file reading acquires `open(path,'rb')` before invoking `_load_index`; PR #316 raises during MessagePack unpack; absent PR #283's `try/finally` ownership guard, traceback lifetime can retain the file. **Prediction:** exact PR #316 rejects ambiguous index but fails an explicit no-GC descriptor-closed assertion; the source-exact union of PR #283 constructor and PR #316 decoding policy will reject the same archive *and* close the descriptor before the exception escapes.

## Cheapest controls / competing explanations
- Reuse three builder-independent frozen direct-codec r24 archives from PR #316, plus its actual `forge_authenticated_duplicate` generator. Do not invent a malformed checksum or bypass real parser.
- Use PR #283's retained-exception/spy style; never depend on CPython garbage-collection timing.
- Positive controls: unchanged independent archive opens and closes; canonical path rejection after mmap closes **both** handles; synthetic mapper failure closes fd.
- Alternative: relying on `__del__`/GC may eventually close the descriptor, but cannot satisfy deterministic rejection-time ownership. Injecting catch/close exclusively into the new MessagePack policy would miss other constructor exceptions.
- Kill condition: any failure to reject an authenticated duplicate; any fd/mmap still open while exception traceback is retained; any lost valid r24 functionality; change to r24 wire, thresholds or parser semantics.

## Ownership, economics, and promotion
Compose the **exact PR #283 constructor block** into PR #316, preserving its parser code byte-for-byte and introducing one interaction test. Provenance should retain both original source heads and original negative evidence. Test/workflow carries only small CI overhead. No release-size/performance improvement is claimed; full CI and product parity remain separate prerequisites. No edits to PR #283 or #316, no modifications to Discovery STATE.json.
