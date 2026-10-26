# O184 — signed r24 timestamps versus ZIP DOS export: prospective falsifier
Date: 2026-10-26 UTC. Product branch: `agent/v031-development`; release: v0.30.0, format revision 24. Research branch: `agent/phased3-v031-o184-zip-dos-boundary-interoperability-20261026`. This preregistration precedes the scientific instrument.

## Primary question
Can an authentic Linux-created revision-24 CMPCT archive containing a regular member whose authenticated `mtime_ns` is before 1970 be verified and exported to ordinary ZIP *with exact member content* on Windows using the unchanged installed Reader?

## Baseline and mechanism
At the frozen base, `src/cmpct/reader.py::_zip_dos_time` calls `time.localtime(mtime_ns / 1_000_000_000)` before clamping the ZIP year field into 1980..2107. Revision-24 physical records permit signed nanosecond times, while DOS ZIP has a narrower year range. Python delegates `localtime` to the host runtime, which can reject negative timestamps on Windows. Therefore Windows ZIP export may raise although `CMPCT.verify()` succeeds. This is a **hypothesis**, not yet a product failure. A separate semantic concern: clamping only the *year* while retaining month/day/time is not equivalent to clipping the complete date to ZIP's boundary; any compatibility policy must be explicit.

## Stronger simpler control and competing explanations
- The ordinary 2001-02-03 UTC timestamp and a contemporary mtime control should export exactly with authenticated member bytes.
- A 1960-01-02 timestamp is representable as signed nanoseconds and as POSIX file mtime, but outside DOS ZIP; if all hosts export correctly, the Windows negative-time hypothesis is false.
- A 2108 date is above the DOS year but within signed-i64 nanoseconds; it can reveal upper-bound clipping differences, independent of the Windows negative-time concern.
- Alternative causes to separate: Builder rejects the old time; artifact transfer changes SHA; Windows Reader fails earlier; a ZIP writer requires a particular timestamp for non-time reasons; target locale alters DOS local clock.
- The independent `zipfile.ZipFile` reader must confirm ZIP CRC and extracted member bytes, not merely an export return code. Include source-module Git SHA custody and single identical archive across hosts.

## Predictions and kill condition
1. Linux producer builds one genuine r24 archive containing pre-1970 and normal members, verifies it, records SHA and authenticated source mtime.
2. Each consumer independently installs real CMPCT, hashes installed Reader bytes against Git, verifies the exact source archive and attempts `export_zip`.
3. Predicted negative: Windows export fails in host `localtime` on pre-1970, while Linux/macOS export ZIP successfully. If Windows succeeds with exact members, **falsify** the Windows-localtime failure hypothesis.
4. If any producer cannot build the exact input, or consumer source/SHA differs, classify infrastructure/custody as BLOCKED, **not** product failure.
5. If DOS year-clipping produces a semantically surprising but valid ZIP, record the precise `ZipInfo.date_time` and treat compatibility policy as independent from crash classification.

## Evidence and scope
Cheapest decisive rung: source derivation, then one fully authenticated cross-host direct product test. No codec/format changes, no frozen test or comparator edits, no release credit from negative evidence. Any optional follow-on fix must retain all original output bytes and ordinary ZIP behavior, preserve archive identity, avoid weakening DOS range constraints, and survive real Windows/macOS/Linux plus same-source controls. Do not change ZIP publication or destination-inode owners (#492, #512, #514); this work only examines temporal metadata conversion and source Reader installed behavior.

## Cost and boundaries
The instrument has modest fixed fixture bytes; no compression, memory, create, or release-grade performance claim. Neither ZIP DOS timestamps nor Python host `localtime` can promise exact preservation of subsecond/pre-1980 CMPCT metadata. Work must preserve the original r24 source and explicitly disclose ZIP's lossy metadata compatibility boundary. Concurrency check: adjacent ZIP publication/Win32-mtime PRs exist, but no exact negative-time ZIP export owner was found by title or issue search. No shared discovery STATE.json write.
