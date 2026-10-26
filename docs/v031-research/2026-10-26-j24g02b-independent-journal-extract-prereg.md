# J24G02b preregistration — physical extractall from independently frozen signed generations

Date: 2026-10-26 UTC. Status: **FROZEN BEFORE NEW EXTRACTION TEST**.

## Authority and baseline
On O7/#358 Reader HEAD `2c5334392c57f9c0f685c3751712acf0e242efae` the newly imported unchanged J24G01/#481 seven-case test verified logical `read`, `read_range`, index generation selection and `verify` across Ubuntu, macOS and Windows on source `44e3992040ec18a3d255682a3c5176efca25b2bb` (Actions `40254137562`, 7 PASS per host). **Those tests do not call `extractall`**. It is not yet demonstrated that the genuine indexed Reader physically materializes the same last signed generation as the logical API on all hosts.

## New primary falsifiable question
Does `CMPCT.extractall` on O7 physically write exactly the signed latest-valid tree for all four frozen J24G01 variants—base, committed, bad successor and incomplete successor—without resurrecting a deleted path?

H4 prediction: on a fresh output directory, `extractall(metadata=False)` creates exactly the expected relative regular-file paths and content bytes from frozen `tests/conformance/v24-committed-journal.json`, with explicit lack of `keep.txt` on successor variants. SHA-256 is checked against the committed independently authored manifest; archive bytes and donor test remain unchanged. Disproof: any missing/extra file, wrong byte/hash, unexpected refusal, failed generation selection or platform divergence.

## Controls and cheapest decisive method
The already-passing unchanged seven-case logical Reader oracle is the stronger semantic control; calling `extractall` with no symlink/hardlink, permission, inode or timestamp complexity isolates publication of signed ordinary files rather than introducing unrelated filesystem issues. A Writer-derived archive is not an independent control. One small additional pytest file and use of the existing three-host source-custody workflow is the cheapest decision. Do not claim transaction durability, concurrent writes, hostile destination safety or native ABI from this court. Do not modify the inherited golden fixture, O7 implementation or existing tests.

## Decision / limitations
The material consequence is an independent externally authored signed-journal contract spanning both logical and physical product outputs. Disk bytes and filenames are verified, not measured compression/performance. Negative or failed runs are preserved. The new court remains research conformance evidence until exact-head CI and higher release gates pass.
