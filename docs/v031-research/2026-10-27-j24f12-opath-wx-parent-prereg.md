# J24F12 — unreadable but writable destination parent, prospectively frozen

Date: 2026-10-27. **Research/repair candidate; no release permission.**

## Exact parent and uncertainty

Stacked on J24F11 PR #557 at `98139bceefb605f548d632882d007e1a40d8112a`, Reader blob `8c27087d0c46d734a930afdb4fb63267c7f366b7`; v0.30.0/r24 remains shipped. J24F11's new-leaf Linux O_TMPFILE branch first calls `os.open(parent, os.O_RDONLY|os.O_DIRECTORY)` before opening the unnamed temp inode. The directory **read** permission appears unnecessary for creation; ordinary existing mode-0300 (write + search) extraction directories are valid for output. Its uncaught `EACCES` risks an avoidable product regression before any physical transfer.

## Prediction and cheapest test

Under a genuinely non-root POSIX user, `mode 0300` destination directory permits create/write/traverse but denies read. The inherited J24F11 branch will reject a valid fresh S_CHUNKS and S_CDC leaf with `PermissionError EACCES`, while ordinary named-stage creation and a genuine `O_TMPFILE` + `linkat(AT_EMPTY_PATH)` using `O_PATH|O_DIRECTORY` parent descriptor succeed, preserving exact inode and SHA.

The control must test real installed CMPCT and independently built revision-24 archive, not only `os.open`. Also preserve the existing J24F11 eight cases unchanged on the same Linux host. Host lacking O_TMPFILE or permission distinction is an unsupported prerequisite, not a PASS. Original parent J24F11 Linux exact-head court: Actions #40432539116; source hash fixed above.

## Alternatives and cost

- Simply catch EACCES and fall back to named-stage creation: abandons the inode-authentic create-only guarantee on a directory where anonymous tmpfiles are perfectly supported; not preferred.
- Reopen the directory O_RDONLY: preserves the defect.
- Use `O_PATH|O_DIRECTORY` only for the Linux anonymous staging parent: allows fd-relative O_TMPFILE and linkat without directory listing/read rights. Kernel capability proof is required; do not reduce open to O_PATH-only without O_DIRECTORY.
- Rewriting output semantics/format: unnecessary.

## Kill conditions and limits

Falsify if genuine J24F11 succeeds unchanged in 0300, if O_PATH cannot produce/publish exact verified fd in the real Reader, if existing J24F11 court regresses, or if the observed behavior is an unsupported filesystem/user artifact. Both tests must check effective UID nonzero, archive SHA, output inode, output content and stage visibility subject to directory read permissions. No same-UID hostile parent-swap, existing destination, Windows, macOS, full performance, native ABI or release credit. No change to on-disk revision 24 or benchmark semantics.

## Initial independent primitive discriminator (not product proof)

On a Linux container under unprivileged UID 65534, `os.open(parent,O_RDONLY|O_DIRECTORY)` returned `EACCES` at mode 0300; `tempfile.mkstemp` succeeded; direct O_TMPFILE succeeded; parent opened `O_PATH|O_DIRECTORY` allowed `os.open('.',O_TMPFILE|O_RDWR,dir_fd=parentfd)` and `linkat(AT_EMPTY_PATH)` with exact published fd inode. This local primitive demonstration precedes implementation but is not an authentic CMPCT result.

**Decision requires source-exact genuine Reader test and inherited J24F11 court, plus broader CI before any product promotion.**
