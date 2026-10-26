# O176 — exact Linux r24 archive on Win32 with pre-existing O167 repair: preregistration

Date: 2026-10-26 UTC. Status: **PREREGISTERED / UNEXECUTED**. This charter precedes any O176 test/workflow implementation and may not be rewritten after result-bearing execution.

## Authority and source identities

Canonical CMPCT release is v0.30.0 / r24; this is only v0.31 research. Producer/test source is O171 #508 HEAD `c932f2896096e04842d7d2705eb6131c4b0fedba`, with original O165 source fixture/receipt and *unaltered* O171 Windows physical test. Known genuine negative: O171 Windows jobs 121504911636 and its final-HEAD repetition failed after verify with unsupported `os.utime(..., follow_symlinks=False)` raising uncaught `NotImplementedError`. Candidate Reader is **existing independent O167 owner** #504 HEAD `841c32d435494f6e4d83c44cd00a1a2f8f7ab148`, stacked on O69; do not change either owner's branch.

## Primary falsifiable question

Can the exact same Linux-produced r24 binary that O171 fails to extract on Windows be verified and physically materialized, including ten typed entries, the real hardlink equivalence class, three correct usable relative symlinks and exact regular file bytes, with an **independently installed O167 Reader**, without altering the Linux producer, O171 original test, source receipt, archive format or Windows semantics?

**Prediction:** baseline Windows package from this experiment's O171-derived evidence HEAD still raises the documented `NotImplementedError`; O167's installed package completes the original O171 physical court successfully. Source HEADs may differ intentionally; separate exact Git SHA plus installed Reader byte identity must bind candidate provenance, and producer receipt still binds the unmodified Linux fixture/source. The producer binary SHA-256 must remain identical before/between/after both Windows package trials.

**Kill/narrow:** If candidate errors, fails physical type/byte/hash/symlink usability/hardlink checks, changes archive, or source custody does not prove two distinct authentic wheels, no positive claim. If baseline unexpectedly succeeds, retain new observation and refuse the planned causal contrast. If O167 fixes extraction but loses physical fidelity, narrow to availability only. A failing runner/install/source gate is infrastructure UNKNOWN, not product loss. If multiple non-O167 mechanisms differ and a positive result appears, attribute only *combined candidate-source* behavior, not causal efficacy of the 19-line fix in isolation.

## Controls, alternatives and opportunity

- Existing O171 negative is an authentic independent baseline, but repeat in the **same Windows job/same archive** to reduce environment and corpus confounds.
- Strong simpler control: inspect source exception handling; O167 already contains the fix, so do **not** create a third Reader implementation, monkeypatch, or falsified producer HEAD.
- Alternative owner O69 #425 suppresses NotImplementedError but is known to lose Win32 file/dir mtimes; O167 should preserve those via guarded leaf handles. Owner O507 #507 is a competing composition and not modified.
- The next most valuable question is actual full physical cross-host extraction, not another synthetic POSIX transfer, benchmark, or near-duplicate timestamp implementation.

## Predeclared evidence plan

One GitHub Actions Ubuntu 24.04 producer, Windows Server 2022 consumer. Linux creates one r24 file with the unaltered O165 producer. Both wheel installs are non-editable and outside source; inspect imported `cmpct.reader.__file__` and match the installed Reader's exact bytes to the appropriate checkout source, and pin original producer and O167 owner commits. On Windows first record unchanged-source baseline return code and error; then install exact pinned O167 package and run unaltered `research/o171_linux_to_windows_same_archive_court.py` from the producer/check branch. That court verifies the original receipt and all physical invariants. Preserve raw JSON, stderr, archive SHA-256 and source custody for both controls, including failure. Use bounded commands and publish artifacts even on red. No test weakening, source-hash fudging or corpus substitution.

## Scope / losses / whole-system accounting

The original O171 ten-entry fixture is small and non-hostile. Positive physical fidelity on this corpus does not prove general NTFS portability, Win32 reparse/race safety, ACL, ADS, xattrs, timestamp precision, sparse topology, process RSS, complete stored-byte economics, cold open, or full performance parity. O167 leaf-handle fallback adds real Win32 system-call/resource cost; not benchmarked here. O167 alone does not establish safe ancestor custody or crash durability. Follow original release and official r24/ZIP zero-byte/timing promotion law before merge; no merge, release or version mutation from O176. CI results always attach to exact Git HEAD and donor Git SHA.

## Counterfactual / policy

The shortest diagnostic was the already-reproduced O171 exception plus inspection of O167; only an authenticated native Windows end-to-end run can decide real cross-host fidelity. No Discovery Engine policy amendment unless repeated durable process failures justify one. `docs/discovery/STATE.json` remains staleable cache under independent reconciliation, not a lock or place to mirror this experiment.
