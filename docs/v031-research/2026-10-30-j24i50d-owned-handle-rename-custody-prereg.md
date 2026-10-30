# J24I50d — public native verification ABI source-handle custody, preregistered

**2026-10-30 UTC.** Dependent on draft #807 at exact observed HEAD `4012c76c29e2b0f8bb6e09f917df9f8cabedb787`; published v0.30.0/r24 unchanged. This is a narrow **C-ABI implementation/evidence** extension, not a new decoder or Python Reader integration. Commit this protocol *before* its test changes.

## Primary falsifiable question

Does `cmpct_verify_complete(handle, out_count)` keep verifying **the actual originally opened file identity** after a POSIX rename/replacement of the pathname that created `handle`, or does it accidentally follow the new pathname? The native Archive already holds a `Mutex<File>`; that source ownership ought to survive path rebinding, but the *new C ABI* has not yet faced an independent foreign-caller test.

## Exact controls / expected observations

1. Begin with the checked-in **independent** revision-24 WAV/FLAC golden from `tests/conformance/v24-wavflac.json`, validate the pinned archive SHA and open one C-ABI handle to its original pathname.
2. Rename the *same* physical original into a retained sibling path; write an **index-admissible, one-bit corrupted physical-CMA4 SHA** replacement at the original pathname. The original and replacement have distinct content SHA, equal length, and the corruption retains the decoded WAV bytes.
3. Existing **pre-rename native handle** must return `CMPCT_OK` and exactly one owner; a **fresh C-ABI handle** opened by the now-rebound original pathname must return a nonzero verification status and reset its count to zero. Fresh CLI `cmpct-native verify` on replacement must return nonzero with zero stdout. CLI invoked on retained sibling original must succeed. All independent file hashes and file identity must be checked.
4. Restore names only after all assertions; temporary files must be under `TemporaryDirectory` and no concurrency actor is required.

A success shows source-custody of **the opened inode/handle on Ubuntu/Linux POSIX**. It does not establish in-place mutation isolation, Python `CMPCT.verify()` delegation, Windows rename semantics, archive-level authentication against an authorized writer, journal recovery parity, or speedup. A failure in which the existing handle verifies replaced corrupt bytes is a product blocker. Inability to rename an opened inode on an OS which disallows it is environmental, not a native-core integrity win.

## Stronger alternative and debt

The simpler control is a post-rebind *fresh handle*: if both old and fresh handles fail, either cached file identity was lost or the test construction is faulty; a retained original-file CLI success disambiguates. Native #788 already has an **internal Rust** source-FD mutation control; the incremental value here is crossing a shipping public C-ABI boundary with the same original frozen golden. This does not justify revisiting FLAC seek, decompression optimization, release changes or shared discovery state.

## Evidence gate

Run the already-existing native-core workflow on the **exact final commit** after test integration, preserve actual action/run ID and result; no positive conclusion based only on local source inspection, unrelated earlier green CI or changed source SHA. Do not weaken existing assertions or thresholds. The observed #807 parent `4012c76c` had 11/11 workflows SUCCESS before this prospective addition; parent outcomes remain inherited evidence only.
