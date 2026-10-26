# O180 result — genuine J24W01 Win32 symlink timestamp regression

Date: 2026-10-26 UTC. Scientific result from **exact source and native Windows**, not a released-product claim.

## Preregistered question, disposition and original control
Prerecorded BEFORE the instrument was added: [O180 preregistration](2026-10-26-o180-j24w01-win32-symlink-prereg.md), commit `f7118ef0bfb62cf5604bc9d50f2301c05c4e96a5`. Hypothesis: J24W01 #507 integrates the O167 regular file/directory mtime helper while retaining the legacy `except OSError` symlink metadata branch; a genuine Linux-created r24 archive therefore verifies but fails extraction on Windows due to `NotImplementedError`.

**Result: PREDICTION CONFIRMED FOR THE EXACT J24W01 SOURCE.** The unchanged original O171 physical-fidelity court was run after same-archive historical and O167 positive controls, rather than replacing it with a convenient partial test.

**Primary hosted run:** [40318495104](https://github.com/FCMO-AI/.CMPCT/actions/runs/40318495104), parent source HEAD `4fb2221b3a2c7ee22c9cc8b006ef9bfd4d07097e`. Linux job `121557053654` **SUCCESS**; Windows job `121557441197` **SUCCESS** as a **scientific classifier**, despite a genuine candidate product RED. An overall green scientific workflow must **not** be mistaken for positive J24W01 product evidence.

**Raw evidence:** [native Windows artifact #12647767956](https://github.com/FCMO-AI/.CMPCT/actions/runs/40318495104/artifacts/12647767956), [Linux producer artifact #12648610593](https://github.com/FCMO-AI/.CMPCT/actions/runs/40318495104/artifacts/12648610593). Evidence contains original O171 JSON, all three installed-source receipts, source fingerprints, and independent disposition.

## Exact input, competing source provenance and native results
- One authentic Linux-produced archive, **1933 bytes**, SHA-256 `b4a9fcc5b3ed7f5980848c69ad88ba6ba6adc831378ba3b27dec51c94423f554`, source and destination identical before and after three installed Reader trials. O171 original signed receipt binds a ten-entry tree (five regular files, two directories, three symlinks, one physical hardlink equivalence class).
- Historical CMPCT source in the O176 stack, Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`: verify **exit 0**, extraction **exit 1**, `NotImplementedError: utime: follow_symlinks unavailable on this platform`.
- Independent O167 #504 donor `841c32d435494f6e4d83c44cd00a1a2f8f7ab148`, Reader Git blob `c50522443b88e78ee2cc8361c4ec2bddbb4f0bbb`: verify **exit 0**, extraction **exit 0**; unchanged O171 court reports `ONE_AUTHENTIC_LINUX_ARCHIVE_WIN32_SCOPED_PHYSICAL_FIDELITY_VERIFIED`, zero observed physical differences, all three usable symlinks and hardlink ownership.
- Independent J24W01 #507 donor `7436bb34e5019639b8e00541b437b5153dee7462`, Reader Git blob `88b6706ba748306b6a4a13274fff2220eec0c32a`, original O167 Win32 helper blob `70308f454c74fad7b247db6ee36aa8cc7d38c99c`: verify **exit 0**, extraction **exit 1**; original O171 court reports `WIN32_EXTRACTION_REJECTED_AFTER_VALID_VERIFY`.
- The failing J24W01 trace names the *installed* `cmpct/reader.py` **line 456**, specifically `os.utime(full,ns=(mt,mt),follow_symlinks=False)`, ending in **`NotImplementedError: utime: follow_symlinks unavailable on this platform`**. O167 handles this exception in the symlink branch; J24W01 only catches `OSError`. No metadata knob, frozen test, benchmark or exception policy was relaxed.
- The same Windows Server 2022 host confirmed native hardlink creation, file symlink creation and directory symlink creation; the failure cannot be attributed to a missing basic link privilege.
- Original O171 court Git blob `8c943128f135607dd36abd083bf1019bc9e4433a` verified intact. Independent J24W01 and O167 installations matched original Git objects except explicitly recorded CRLF-only checkout representation.

The independent disposition `research/o180_j24w01_native_disposition.py` returned:
`J24W01_SYMLINK_MTIME_REGRESSION_CONFIRMED` — **native installed-product negative**. It would have recorded an explicit hypothesis falsification if J24W01 had passed. Unexpected environment or source failure would have returned nonzero/unclassified.

## Decision, negatives and bounded implications
**Integration is not safe to promote:** #507's O160 canonical ZIP and O167 file/directory mtime acceptance cannot substitute for inherited Win32 **symlink** extraction. #507's own three-host J24W01 acceptance being green does not refute this source-exact failure because its tested scope differs. #507's official r24/ZIP performance completion also cannot override a correctness red.

The correct owner action is to preserve the existing O167 symlink-specific `(OSError, NotImplementedError)` handling while reconciling #507's Reader, then run **both** unchanged O171/O176 native cross-host physical court and original O160/O167/O149/O140 acceptance without altering comparators. A third product implementation of Win32 mtime restoration is unjustified. This PR has **no product change** and is intentionally research/draft.

### Limits and self-critique
Only an authentic small Linux → Windows Server 2022 revision-24 archive, a single host/runtime and the original O171 ten-entry physical manifest were measured. No evidence for ACL, ADS, xattrs, junction/ancestor TOCTOU, crash durability, malicious archives, cross-Windows versions or broad performance. No archive-size, create/extract throughput, memory, temporary-I/O, cold open or selective-read claim. Whole suite on the result-document HEAD must be rechecked; generic history/source-epoch controls may still be inherited reds.

## Transferable early discriminator
Static inspection of the *separate* `K_SYMLINK` timestamp path before owner composition would have exposed the omitted exception; file/directory-only O167 tests cannot certify preservation of every metadata path. This is a causal coverage lesson, not sufficient repeated evidence to modify the Discovery Engine's normative policy.

## Future executable frontier
Owner #507 can transplant the **existing original** O167 symlink guard with no new mechanism, then confirm one same-archive native red-to-green contrast and keep all ZIP/metadata controls. Release, canonical merge, version and frozen benchmark gates remain untouched.
