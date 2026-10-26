# O157 — Authenticated Reader ZIP-stage pathname custody: hosted negative result
**Decision:** `STAGE_CLOSE_REOPEN_EXTERNAL_FILE_OVERWRITE_CONFIRMED_POSIX_BOTH_STAGED_OWNERS`  
**Evidence classification:** Source-exact *negative installed-product* research, not a successful product hardening or release result.  
**Observed:** 2026-10-26 UTC; no numeric version or format change.

## Frozen prior question and provenance
Preregistration was committed **before** the adversarial test/workflow:
- `docs/v031-research/2026-10-26-o157-zip-stage-identity-prereg.md`; Git commit `961741a0f7b253591861d0865f92a74c2be10f97`.
- Published CMPCT v0.30.0, revision-24 format unchanged.
- Experimental PR [#497](https://github.com/FCMO-AI/.CMPCT/pull/497), stacked on O149 PR [#492](https://github.com/FCMO-AI/.CMPCT/pull/492). The O150 source is independently installed from [#491](https://github.com/FCMO-AI/.CMPCT/pull/491).
- O149 exact commit `ca01d885fedc8ffc343b9c3c624eddd134158452`, Reader Git blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`.
- O150 exact commit `48bbb41661f8b19d369c50b06bec1018cd4400e9`, Reader blob `f38662c8db4132895778951263d83d24022f9296`.
- Unmodified Builder-independent r24 RAW fixture `tests/conformance/v24-direct-codecs.json`, Git blob `d10b7dab9126d39e819a74279c186363a163f2ef`, input archive SHA-256 `5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d`.
- Result-bearing test/workflow HEAD `4c8bf56611f4a7b29d5faf35da47c3d32056e521`; test Git blob `ad1cd2c1bf2d8334c8f382f0e1917fc15e02c2dc`.

## Why this question was unclaimed
O143 PR #489 had proved regular-ZIP output truncation during source corruption. O149 and O150 repair ordinary failure atomicity by writing through a random exclusive-created sibling then `os.replace` onto the requested destination. O151 PR #493 already compares permissions and success-path symlink handling; O153 PR #495 already measures ordinary successful ZIP economics. **Neither demonstrates that the original stage inode remains the writer's object between creation and publication.** Both product source versions explicitly close the new stage fd before reopening its pathname.

## Smallest decisive experiment
Use only actual installed unchanged Readers outside the checkout, and ordinary synthetic files inside one isolated temporary directory:
1. A no-pivot control exports the frozen independent `raw.bin` archive to a preexisting valid ZIP. Expected and observed: final output ZIP is readable, source untouched, unrelated 715-byte regular-file sentinel unchanged.
2. An adversarial interleaving hooks only `os.close`: after confirming by `os.fstat(fd)` and `os.lstat(stage)` that the just-exclusive-created stage is the same regular inode as the still-open descriptor, close that original descriptor, unlink just that stage path and substitute a symlink to a **different unrelated regular file**. Let the real Reader's unmodified ZIP writer reopen the stage pathname and publish normally. Test code never writes into the unrelated victim. The actor must have permission to alter the output directory; this is deterministic scheduling of a possible concurrent-directory interleaving, not a spontaneous/real-world attack.
3. Independently audit the exact installed Reader blob, unchanged original fixture, JUnit success and emitted structured evidence. A **PASS on the pivot case denotes reproduction of a safety defect**, not an approved safe implementation.

## Real hosted observations
GitHub Actions [run 40277368542](https://github.com/FCMO-AI/.CMPCT/actions/runs/40277368542) at exact test HEAD `4c8bf56611f4a7b29d5faf35da47c3d32056e521`: **4/4 matrix jobs SUCCESS** (Ubuntu 24.04 × O149/O150, macOS 14 × O149/O150), each 2/2 tests PASS, **8 PASS / 0 FAIL / 0 SKIP**. Source fingerprint verification, installed-package location, JUnit and independent JSON/log audit all succeeded.

| Host | Installed product | No-pivot control | Post-close stage symlink-pivot outcome | Raw artifact |
|---|---|---|---|---|
| Ubuntu 24.04 | O149 | exact ZIP, sentinel unchanged | **external regular victim rewritten; target becomes symlink** | `12630498349` |
| macOS 14 | O149 | exact ZIP, sentinel unchanged | **external regular victim rewritten; target becomes symlink** | `12630508216` |
| Ubuntu 24.04 | O150 | exact ZIP, sentinel unchanged | **external regular victim rewritten; target becomes symlink** | `12630922050` |
| macOS 14 | O150 | exact ZIP, sentinel unchanged | **external regular victim rewritten; target becomes symlink** | `12630443503` |

For every negative pivot: original external sentinel was **715 bytes**, SHA-256 `00f3529689790e3773cb11daaac162923ee47faba30e75e13d06cfbf14cd6a99`. After the actual product ZIP writer followed the stage symlink, it became a **176-byte valid ZIP**, SHA-256 `910e3be250460beac06083166a0641ed1398506ae40949e56efd3c3c73a564db`, containing the authentic `raw.bin` member with exact bytes `0..63`. The requested ZIP output path had become **a symlink to the external victim**. The original CMPCT archive remained unchanged. All four ordinary no-pivot controls emitted that same ZIP SHA and did **not** modify the victim.

Source-specific complete job IDs:
- Ubuntu O149 `121422848977`; macOS O149 `121422849107`.
- Ubuntu O150 `121422849226`; macOS O150 `121422849119`.

Raw original artifact IDs are from run `40277368542`; artifact retention is 30 days. The tester/repro source and this decision file are durable in PR #497.

## Scientific interpretation and strongest criticism
The defect is an **identity/ownership break** across a close-then-reopen gap. `O_EXCL` prevents pre-existing name collision/symlink at allocation time but does not guarantee that the newly created inode owns the pathname after the descriptor is discarded. The subsequent pathname-based ZIP writer follows a different symlink to an unrelated *regular* file, so checks excluding nonregular requested destinations or the CMPCT source inode are insufficient. It is a pathname/custody issue, **not** an SHA-256 collision, ZIP content mismatch, or demonstrated remote exploit without filesystem-directory write authority.

The test uses a deterministic test-only scheduling hook instead of probabilistic races; this increases causal precision but does not estimate real exploit probability. The required adversary/cooperating actor must be capable of removing/replacing entries in the output directory during ZIP export. No claim is made for Windows, ACL/xattr, nonstandard network mounts, power loss, concurrent mutation of source, or arbitrary independent races. The verified O149/O150 gain—preservation of old regular ZIP on ordinary decode/write error—remains valid *within its tested assumptions*.

A simple `os.fdopen`-retained descriptor would likely prevent the writer from following the substituted symlink, but **it does not by itself establish safe publication**: an attacker could still substitute a symlink in the stage pathname before the final `os.replace`, causing the requested destination to become an alias. Both **write ownership** and **publish ownership** must be verified under an explicit trusted-directory/OS portability model. Stage pathname randomization is not a durable lock.

## PARETOBONK decision, coordination, and counterfactual
**Primary question:** can both existing staged ZIP candidates safely retain the exclusive-create inode across stage writes when the pathname changes? **Answer: no under the preregistered POSIX interleaving, four independent hosted negative witnesses.** The current family is therefore **narrowed**: ordinary failure atomicity is real; adversarial mutable-directory pathname custody is **not established and is contradicted**. Separate owners for the two product implementations remain; this PR implements only a test, not a third repair.

**Counterfactual discriminator:** checking at code review whether an exclusive-create fd stays open until all writes (and whether rename publishes that same object) could have highlighted the gap even before CI. The single injected close/reopen interleaving was the cheapest instrument capable of turning that risk into a causal external-file-write witness; the normal control excluded generic ZIP corruption.

**Policy:** neither the normative Discovery Engine nor `docs/discovery/STATE.json` was edited; the latter is a staleable cache with an independent owner. No frozen benchmark, evaluator, comparator, format semantics, historical release record, package or native code modified.

## Next highest-value actionable product question
Choose **one** existing O149/O150 product owner and test a descriptor-retained/private-directory staging design that (1) never follows an attacker-replaced stage filename for writes, (2) cannot publish an attacker-substituted symlink or overwrite the protected CMPCT source on publication, (3) preserves the O143 failure-atomicity gains and original O135/O140 ordinary destination guards, (4) has explicit POSIX/Windows and same-directory threat assumptions, and (5) prices exported temporary bytes, CPU/wall, I/O, RSS, metadata/inode/hardlink semantics using the official untouched release parity gate. Continue to honor the exact O157 negative test as an adversarial acceptance control. No immediate merge, release, or version bump.

**Scientific negative: CONFIRMED. Product repair: NOT IMPLEMENTED. Release credit: ZERO.**
