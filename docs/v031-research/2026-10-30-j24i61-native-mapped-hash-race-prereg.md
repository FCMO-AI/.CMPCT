# J24I61 — Bind the reported native SHA to the executable mapped inode, not a pathname reopened later

**2026-10-30 UTC — prospective preregistration before modifying any native-custody instrument or test.** DRAFT evidence-integrity research only; no CMPCT product/format/ABI/release/threshold modification. Parent exact source: #837 `1ea579c5837d3b783614f423c423a121878dc0ca`. Existing mechanism owner #790 is explicitly preserved.

## Baseline and primary falsifiable question
#837's hosted post-ABBA fresh-process receipt from Actions #41075337668 (artifact #12988780098, ZIP SHA-256 `1d43e55fb359db5ec779607d9da25508efe61bbaa6d5ba5c5665d8819999490b`) reports equal candidate/base ELF SHA256 `f60f0b0a5d4874044124dc215e556f76522ef0cca9a2da94cdeccef96085dacf`. This is valid fresh-process evidence *within the existing probe's assumptions*, never timed-process attestation. Static source audit identifies a narrower integrity gap: the probe checks `Path.stat()` against `/proc/self/maps`, **then later reopens the pathname** to hash bytes. The pathname can be rebound between those two operations. The resulting `sha256` field need not refer to the previously checked mapped inode.

**Question:** Can a deterministic, externally synchronized same-name replacement after the mapped-inode check make the original probe claim the replacement SHA as the SHA of a different ELF still mapped/executable? Then can one descriptor-based, fail-closed identity check eliminate this false attestation without modifying the measured ABBA workload?

## Mechanism, simpler control and alternatives
Control: existing #790 positive two-ELF discrimination, wrong SHA, dirty Python, symlink/escape, missing file and precheck same-name inode rebind hostile tests. Simpler *pathname post-stat only* would reduce but not close the stat/hash gap; a newly opened FD with `fstat` tied to mapped (device, inode) plus reading from **that same FD**, post-hash metadata and pathname re-check covers name rebind on the tested Linux host. The memory mapping is not a bytewise atomic snapshot of a concurrently writable inode, and this protocol must not claim otherwise.

Independent deterministic oracle: on a Linux gcc test fixture, load ELF A, allow the probe to validate A's original mapped dev/inode, then intentionally rename A and place valid but different ELF B at the **same name immediately before the digest step**. Assert the *inherited* probe either returns success with B's SHA (falsifying its claim) or fails; after the repair, require explicit rejection of the path/FD rebind, or a correct attest of A with precisely stated claim boundary. Do not rely on probabilistic thread timing or flaky sleep intervals; inject the replacement through a test-only hook at an exact probe seam. Also require original existing 10 hostile controls and original post-ABBA workflow step order to pass.

## Kill/stop and scope
If the inherited probe already cannot accept the deterministic rebind, document that negative and make no redundant implementation. If a patch cannot bind hash to mapped inode with a bounded, portable Linux-only FD path and cannot pass existing tests, abandon it as nonpromotable research. Never weaken release zero-byte size, timing (>5% and >3ms), manifest, ABI, semantic or test strength. Do not rewrite #790's donor precedent as though this mechanism were proven there.

## Expected evidence and costs
1. A pre-fix deterministic failing/false-attestation witness with two physically different shared-object SHAs and observed mapped dev/inode.
2. Smallest post-fix implementation plus independent test, run locally where possible, followed by exact-head Linux GitHub CI; do not credit CI queued/pending as PASS.
3. FD-hash streaming bounded to 1 MiB, two additional fstat/path identity checks, negligible but *unmeasured* after-ABBA overhead; no timed product effect because the diagnostic remains after the original comparator.
4. Preserve source SHA checks, executable /proc mapping, original wheel receipt control, and original raw A/B/B/A timing evidence. Update owner #790 after decision, without editing their PR.

## Promotion boundary
This is instrumentation correctness; even strong result cannot certify timed subprocess native identity, in-place concurrent byte stability, Windows/macOS mappings, full transitive import graph, same-runner cache/scheduler isolation, real product speed, or v0.31 release. Previous official #835 FAIL and current #837 PASS remain distinct observed trials. 
