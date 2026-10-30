# J24P05 — Pre-result: physically valid wheel names versus installed-path identity (30 October 2026)

**DRAFT SCIENCE ONLY; stacked on the exact J24P04 candidate #854 at 57bc9a00a6dbba079131de15f88995fd75ea91b6. NOT product/release authority.** No new wire format, compressor, ABI, benchmark, threshold, or packaging owner mutation.

## Unresolved question
Does the J24P04 independent physical wheel validator accept a fully SHA-256 RECORD-valid macOS wheel with two distinct ZIP names which a case-insensitive APFS filesystem maps to the **same installed pathname**, potentially replacing the exact native binary whose Mach-O slice/OS claims passed the gate? The authentic positive control must remain accepted. A second negative control uses a filename that is distinct under APFS casefold.

## Preregistered hypothesis, alternative, decision
H1: a wheel with native `cmpct/cmpct_core.cpython-311-darwin.so` plus `cmpct/CMPCT_CORE.cpython-311-darwin.so`, unique raw ZIP member names and rehashed complete RECORD, passes the current physical validator even though the two names casefold-identically. A normal installation/extraction onto a case-insensitive filesystem may then overwrite the native file; detect with distinct inert byte payloads and hash of resulting path, NEVER load or execute the injected member.

Strong simpler control: original single-native wheel and a second non-colliding `cmpct/unrelated.bin` should pass, leaving native hash unchanged; duplicate exact ZIP filename must be rejected as already covered.

Disproof: current validator rejects collision before admission, or native path cannot collide under tested filesystem/install workflow. If macOS runner filesystem is case-sensitive, record `NO_MAC_COLLISION_HOST` rather than manufacturing a product failure.

Competing explanation: real installers may reject case-colliding wheels or may preserve the intended member regardless of order. Both outcomes must be measured before claiming installed-semantic failure. ZIP member validation alone is not a publisher signature nor an installation proof.

## Evidence ladder and economics
1. Offline synthesize a correctly hashed/recorded wheel with **a real inherited Mach-O payload** (not a renamed test stub), plus an inert conflicting member, and verify `inspect()` result under exact source `#854@57bc9a00a6dbba079131de15f88995fd75ea91b6`.
2. On macOS 15, measure filesystem equivalence and install (or benign extraction) order in isolated temporary target with Python wheel installer semantics. Check raw file hashes; do not run the altered native binary. Also test Linux control.
3. Only if decision-changing, propose a generic bounded wheel member-path uniqueness check including Unicode normalization and casefold; do not change the owner #854's validator concurrently.

**Kill/narrow condition:** reject unsafe installed identity if physically demonstrated; otherwise preserve scope as `STATIC_ADMISSION_GAP_ONLY`, not an actual wheel exploit. Host A/B must preserve same input/source identity. Release credit zero.

## Coordination and concurrency
This is a source-exact **independent adversarial replication**, not a competing implementation of #854 or #850. Only new J24P05 research/court files may be changed here; any guard fix belongs to owner #854 and publishing integration to #850. Do not update shared docs/discovery/STATE.json (stale cache owned separately). Keep predictions and negatives append-only.
