# J24K10 — Fully charge source-copy ownership before promoting amortized VZIP geometry

Date: 2026-10-28 UTC. **Prospective preregistration before experiment implementation**.
Parent: J24K09 #653 at exact `2d30cc6da41c136f3b1a412ccf3f1f5686dca54a`.
Released main v0.30.0/r24 unchanged. No product mutation, merge or release authority.

## Primary question
J24K09b proved a nominal 4.79–4.88x 64-query speedup from physically proving
4,096 VZIP owner headers once. It assumed an immutable source snapshot and charged
only the proof table, not acquisition of an isolated source. What happens if
**every independent selective session pays an entire private disk-file copy**
before reusing any verified geometry? Does unrelated archive size reverse the
decision? Existing O24/O26 #377/#379 already own full-copy and Linux memfd
ownership semantics; this is a **separate VZIP session-economics cross-over oracle**,
not a new snapshot safety claim or competing Reader implementation.

## Distinct hypotheses / decision rule
H1: at small source size and Q=64, one copied-and-prevalidated session is faster
than per-query physical BHDR checks for both 512 and 4,096 preceding streams.
H2: padding the **same** source geometry with 64 MiB of unrelated bytes reverses
at least one low-query decision; no unconditional per-session copy promotion follows.
Falsify H1/H2 by the actual raw median matrix. Do not garden thresholds.
If copy loses even at Q=64, retire generic full-copy per-session ownership;
if it wins in some cells, retain only a bounded eligibility hypothesis and
separately demand a real immutable/atomic owner boundary before product promotion.

## Frozen experiment shape
Use the unchanged `research/j24k09_physical_witness_economics.py::fixture`,
`cmpct.codec.range_vzip`, and the exact installed
`cmpct.reader.CMPCT._vzip_physical_stream_size` from the parent.
The fixture uses authentic BHDR framing but is **not a complete revision-24
archive**: this is a component oracle. Run on Windows Server 2022, Ubuntu 24.04
and macOS 14 with Python 3.11 and a normally installed CMPCT wheel.
Hold recipe, source bytes, output length (one suffix byte), and OS fixed per pair.
Use N={512,4096} STORED streams, Q={1,8,64} queries/session,
and unrelated zero-semantics archive padding={0,64MiB}; 12 cells per host.
Five deterministic ABBA cycles per cell, yielding ten raw measurements per
strategy, with order alternation. Two arms:

A: source mmapped, `range_vzip` checks each skipped BHDR on every query.
B: create one entirely new scratch-file copy per sample, charge all copied
bytes and wall/CPU time, mmap it, validate every preceding BHDR on that copy,
charge the temporary Python size table, then perform Q queries with table reuse.
Unlink and unmap each copied source after the sample. No copy or proof is gifted.
Original source staging and fixture creation occur *outside both arms*;
all per-session work is inside both timing boundaries. The scratch copy has
no `fsync` (durability not required for temporary decoding), so these are
**optimistic lower-cost** copy economics, not power-fail-durable ownership.

For each cell preserve source SHA-256, exact source/scratch bytes, zero-copy
baseline, copied byte counts, extra index memory, wall/CPU raw samples,
median and paired ratio. Check returned suffix against independent `b"G"`.
Leave an independent stdlib receipt auditor that recalculates medians, tests
the full frozen matrix, checks raw sample counts and rejects tampering.

## Alternative explanations / adversarial limits
- Python component simulation is not end-to-end Reader open/range or a real
  signed archive; no product or release credit.
- Unrelated padding changes copy bytes but deliberately not VZIP decoding work.
  A full archive with other members could add different costs.
- A writable scratch file protects against replacement of the *original inode*
  after copy, but **is not immutable against a same-user writer**.
- A sequential copy of a mutable original is **not an atomic point-in-time
  snapshot**; O26 sealed memfd is Linux-only and itself charges full bytes.
- Original source may change within an individual range; neither base nor
  candidate proves cryptographic partial SHA. This experiment assumes a
  quiescent source only for honest economics.
- `mmap` does not itself grant source immutability. A copied snapshot also
  exports disk bytes, read/write I/O, startup/system-call burden, and reader
  maintenance/portability obligations. RSS and disk cache effects require a
  higher-rung independent measurement.
- Results are reported per cell, including negative/Q=1 regressions and
  unsupported platform behavior. No inherited comparator, hard invariant,
  CI threshold, or release policy may be altered.

## Concurrency / ownership
Parent #653 owns J24K09 physical stream correctness and source edits.
This branch adds only research code, an opt-in workflow and immutable evidence.
O26 #379 owns sealed-source semantics. Do not touch parent Reader, codec,
Discovery `STATE.json` (owned by #574), or other agents' work.
After an exact-head scientific court report source/CI truth, not merely the
existence of a PR. Handoff should identify the cheapest *safe* next decision
and whether full-file copying is economically viable under realistic archive
size distributions, not a magical universal snapshot.
