# O87 preregistration — nonregular existing destination availability (2026-10-25 UTC)

**Status:** preregistered, no O87 product observation or implementation at this commit.  
**Owner:** independent scientific falsification only; original O81 source/output-admission owner is PR #439, composition owner PR #442. Do not edit their branches.  
**Exact baseline:** PR #442 source HEAD `7efcc51154b64fd6394ddffaab599760659f6c91`, Builder Git blob `64b0cd21ad54ce7c8e8c6f5847b3c613fff6511c`, stacked on O80; released v0.30.0/r24 unchanged.

## Question and hypothesis

After the O81/O84 path-containment and hardlink-identity admission, can a pre-existing **external FIFO with no reader**, or an output symlink resolving to that FIFO, still block `Builder(root, workers=1).build(out)` indefinitely instead of rejecting unsupported nonregular destination types?

Source basis (not yet product evidence): O84 `Builder.build` checks destination containment, calls `os.stat(out)`, and only applies its output inode guard to multi-linked regular files. It eventually publishes via `Path.write_bytes()`. An earlier O84 side probe observed that Python's FIFO write can block. This preregistration does not claim the real CMPCT Builder blocks; the next experiment will test it.

**Primary predicted outcome:** a real, installed O84 Builder invoked in a disposable **killable child process** with an existing unconnected FIFO times out without returning, whereas a matched external existing *regular* file returns successfully under the same timeout, yields a revision-24 archive and survives `CMPCT.verify()` plus exact payload read. The symlink-to-FIFO case is a separate structural replication, not proof of additional platforms.

**Stronger simpler control:** directly writing a FIFO with Python `Path.write_bytes` may block, but a real Builder could reject it earlier or take another path; product-level evidence is therefore required.

**Alternative explanations:** the Builder is slow or stuck in compression/initialization, or a filesystem denies FIFO creation. Use a matched child-process regular-output control, tiny fixed input, subprocess hard timeout, and explicit setup/host preconditions. Do not interpret an unavailable FIFO primitive as product success/failure.

**Disproof:** if the installed O84 Builder rejects the nonregular target promptly without side effects, retire this inherited-availability hypothesis. If *both* regular and FIFO time out, classify as instrumentation/infrastructure ambiguity, not evidence of FIFO admission. If only symlink fails, narrow to symlink. Positive failure is precisely a caller-visible stuck process, not proof of data corruption or a universal hang guarantee.

## Evidence boundaries and safety

Cheapest decisive rung is a bounded same-host A/B against the genuine installed r24 Builder on Ubuntu and macOS; Windows named pipes are not POSIX FIFOs and are out of scope. Child processes must be killed on timeout; never execute `Builder.build` on a FIFO directly in the CI runner parent. Compare real completion/timeout and filesystem mutation; retain JUnit and runner logs. No product, on-disk format, benchmark, gate, comparator, release, or thresholds changed. This is a **negative scientific court**, not candidate product credit or a release gate.

If a product-level failure is observed, hand off the exact source HEAD, case, run identity and bounded fix alternatives to owners #439 and #442. A separate future implementation, if authorized, must distinguish nonregular external outputs from normal regular files and preserve same-input archive parity, filesystem semantics, and measured admission overhead. Not a license to silently adopt O75's `os.replace` behavior, which O78 showed can regress inode/xattr/hardlink semantics.

## Competitor PARETOBONK / next decision

- **Alternative A:** productize O80×O81 and close the owner tests; still a priority of #442 and should not be duplicated here.
- **Alternative B:** pursue VZIP inflation budget or SHA selective reads; owned by #444/#443, respectively.
- **Chosen C:** one cheap, structurally new destination-type falsifier after the O84 primitive-level signal; it can identify an unclaimed availability blocker in the owner integration with low evidence cost.
- **Decision after result:** if positive, request owner-level rejection contract + focused cross-host semantics; if negative, retire and return to exact current product/benchmark frontier.

No Discovery Engine policy or `STATE.json` update is justified by this preregistration.
