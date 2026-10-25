# O121 — Reader direct-publication FIFO exposure in S_PACK and S_VZIP (prospective preregistration)

Date: 2026-10-25 UTC. Status: **PREDICTION LOCKED BEFORE IMPLEMENTATION AND HOSTED RESULTS**.

## Repository authority and concurrent ownership

Canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, original Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, original Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, released v0.30.0 and revision 24 untouched. O106 #461 / O108 #463 demonstrate S_BLOB/S_SPARSE direct-output FIFO blocking and S_CDC replacement; #269 owns destination-safety implementation. This O121 is an **independent, science-only different-storage verification**, not a competing Reader repair or replacement for O108. Check current open PRs for same exact S_PACK/S_VZIP hostile matrix before new writes.

## Primary question and falsifiable predictions

Does the real r24 installed Reader also block on FIFO and symlink-to-FIFO leaf destinations when authentic Builder archives use **S_PACK** or **S_VZIP**, whose non-chunked extraction branch executes `self.read(rel)` then direct `os.open(...O_WRONLY|O_CREAT|O_TRUNC)`? One genuine archive per mode, reused unchanged across four output conditions: fresh leaf, existing regular leaf, FIFO without reader, symlink-to-FIFO. Prediction: both normal leaves reconstruct exact byte identity rapidly; both FIFO variants exceed an 8-second killable-child timeout **after the Reader has opened the archive index**, preserving the original FIFO object. No claim of infinite blocking. The original source and archives stay unchanged. Success of a timeout-expecting test signifies a **product vulnerability**, never a repaired product.

For S_PACK, generate one nonempty small `.txt` eligible for micro-PACK and assert the Reader's actual `row[6][0] == S_PACK`. For S_VZIP, generate a simple valid Deflate `.zip` with deterministic metadata and assert authentic `row[6][0] == S_VZIP`; do not patch the index or simulate archive bytes. If Builder legitimately chooses a different storage type, report **setup/mode prerequisite failure**, not a FIFO result, and do not silently tune the archive after seeing results. Source file name, archive SHA and digest remain invariant within each mode.

## Strong simpler controls and alternative explanations

Controls: same source-specific Reader `read` and `verify`, positive fresh and existing regular extraction, child marker emitted immediately after Reader index open, same archive fingerprint for all four leaves. The child runs installed CMPCT outside checkout, with strict timeout and cleanup. Import/startup/decompression could otherwise explain slow execution; timely normal controls and index-open receipts constrain this explanation. An immediate exception/refusal instead of timeout **falsifies** the predicted defective arm and must be preserved unchanged. S_VZIP recipe admission is a genuine prerequisite, not a performance victory. A generated storage-mode failure cannot be counted as product behavior.

## Scope and economics

Initial hosted Linux Ubuntu 24.04 Python 3.11 POSIX FIFO court: 2 genuine modes × 4 leaf classes = 8 case observations, expected four bounded 8-second timeouts, strict JUnit/JSON audit. macOS extension if source generation is portable, but no Windows FIFO claim. Payload SHA, archive SHA, exact Builder/Reader Git blob, and installed-package provenance required. This is a security/availability scientific test; no Builder/Reader/native/format/performance-gate/threshold/source change. No size, create/extract throughput, RSS, I/O, or release improvement credit. An evidence-backed result must notify Reader security owner #269 and issue #462; code repair, if warranted, remains their responsibility.

## Decision and stop law

If both modes demonstrate the predicted direct-write FIFO behavior, close the remaining genuine-physical-representation gap in the shared-output-leaf security test requirement and **do not create more storage-family variants** absent a genuinely different writing primitive. If any mode refutes prediction, capture its actual physical mechanism and reevaluate the cause. If setup preconditions fail, do not rescue through fixture retuning after observing outcomes; record as inconclusive and select another dependency-safe lane. O108 negative evidence and S_CDC staging behavior remain controls, not a reason to weaken evaluator or replace all destinations with `os.replace`.

No Discovery Engine policy rewrite or STATE.json mutation: #440 owns stale-cache reconciliation.