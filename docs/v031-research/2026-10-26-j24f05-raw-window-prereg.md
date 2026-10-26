# J24F05 — bounded immutable RAW transfer preregistration

Date: 2026-10-26
Status: frozen prediction BEFORE candidate edit; product promotion unearned.

## Authority and exact baseline

- Published v0.30.0, r24 remains unchanged; prospective J24F04 owner #537 source exact `d5aa5cbc1ef1e00b6e3c8c72cdd1598192d563a3`, Reader blob `8b5910725260e7b4db155ee0b393eb48a42f7efa`.
- J24F03 #530 / Issue #531 reproduced a genuine mutable-source mmap hash-to-write integrity defect; J24F04 #537 protects via one immutable **entire physical RAW chunk**, 8/8 original POSIX hostile trials succeed, but the parser admits physical RAW chunks up to ~1 GiB.
- Separate stage pathname substitution Issue #528, output namespace and archive truncate/SIGBUS problems are NOT solved by this experiment.
- Discovery STATE.json is a stale cache; no existing J24F05 owner or same-window bounded RAW candidate found in open PR/branch scan at this cutoff.

## Primary falsifiable question

Can the J24F04 ownership fix be rehabilitated from O(physical RAW chunk) detached Python bytes to a fixed 64-KiB maximum RAW transfer snapshot while preserving exactly the original whole-file SHA/authenticated-output invariant and rollback?

## Mechanism

Borrow a validated RAW mmap view for each physical chunk but **do not duplicate its full bytes**. For each <=65536-byte window, create one immutable bytes copy, feed that exact object to SHA-256 and the temporary-stage write. Never retain any immutable window after the write returns. Sum all windows against declared chunk size, preserve final indexed logical SHA/size comparison *before* publication. Compressed/mixed chunks remain unchanged.

## Stronger/simple controls and alternatives

1. J24F04 whole-physical-chunk immutable snapshot: stronger/easier correctness control, worse worst-case memory.
2. Hash borrowed mmap then write borrowed view in <=64 KiB windows: rejected because the source actor can mutate after hashing; bytes-to-output identity must be owned.
3. Two-stage verify/read fallback: an actor can mutate between passes, rejected without an enforceable immutable-source contract.
4. Copy whole archive: excessive exported memory/temp I/O.

## Predictions and kill conditions

- Original J24F04 4 logical hostile cases (S_CHUNKS / S_CDC × post-copy vs future-copy) retain their expected safe outcomes, including rollback and exact signed SHA.
- New independent large-RAW physical archive court on both S_CHUNKS and S_CDC: each full logical input reconstructs exactly; each actual transfer write buffer is <=65536 bytes; external same-inode pwrite after first window cannot create a successful wrong-SHA publication; mutation of a future not-yet-copied window forces rejection and preserves a pre-existing destination.
- A measured Python allocation bound should rule out materializing the full >=8 MiB RAW physical chunk. Declare any noisily unmeasured RSS separately; tracemalloc is a Python-allocation proxy, not peak RSS.
- Falsify on a single successful unauthenticated output, failed valid control, actor not triggered, unexpectedly large os.write, failure to preserve old destination, or full-chunk copy demonstrated.
- Worst-case copy traffic stays one pass over RAW payload, but CPU/wall relative to J24F04, peak RSS, temporary I/O, native/Windows and complete release gates remain obligations. No projected speed/product gain is asserted.

## Evidence ladder and promotion boundary

1. Static exact-source test and local microbench/hostile proof.
2. Installed-package GitHub Actions on Ubuntu/macOS with source SHA bound and original J24F04 hostile court.
3. Exact archive parity; repeated same-runner complete extraction CPU/wall/RSS vs J24F04, legacy published r24 and strong alternatives before any merge or release.
4. Compose separately with Issue #528 final stage binding. Do not alter validators, clocks, frozen comparators, FORMAT, version, or release data.

## Ownership and handoff

This is an independent stacked child of #537 on its exact HEAD, not a replacement for the owner's draft. Preserve #537 unchanged; communicate result to #537/#530. The scientific episode is J24F05-window-snapshot, and the cheapest deciding action after code change is the large-RAW hostile court, not a full 15-row benchmark.
