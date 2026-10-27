# J24C01b — Prospective Win32 fd-mode portability composition

**Frozen before the additional source mutation, 2026-10-27 UTC.** Parent J24C01 `e65e74e1edbed03ff46b4f4a5fae1e79000effa0`, still draft #567, stacks J24F12 #559 and O214 #564. Original J24C01 prereg `2e6ff5b89c0a0fba32e306ee1ce47a78a093c9ac` is immutable. The inherited Reader's chunked extraction still directly invokes `os.fchmod`, which Python for Windows does not implement. The separately owned J24W02 #536 at `7973dbf904ff0660971d2e112d9f77b38f37019a` has demonstrated the narrow best-effort descriptor-mode correction on three hosts (33 passed in original owner trial).

## Scoped prediction

The *exact* owner #536 mode-application guard can be transplanted into J24C01's chunked extraction without touching the Linux `O_TMPFILE`/ `O_PATH` publication path or the S_SPARSE/S_CDC effective-index admission, and without reopening the staged output by pathname. After composition, genuine S_CHUNKS/S_CDC extraction and corrupted-destination preservation should pass on Ubuntu, macOS and Windows, including `os.fchmod` absent. On Windows the O214 valid CDC extraction can be made compulsory; previous O214 skips Windows extraction only because of the independently established `os.fchmod` defect.

## Controls / falsifiers

- Import J24W02's unchanged `tests/test_chunked_extract_platform_fchmod.py`; add no blanket exception handling and leave unexpected `ValueError` propagated.
- Unchanged O212/O214 indexed physical wire tests continue; do not modify their independent judgments. Verify real Windows S_CDC extract in a separate new test, instead of editing O214's platform skip.
- Unchanged J24F11/J24F12 unprivileged Linux inode/permission courts continue; integrated CDC admission-fd witness continues.
- Falsify if absent `fchmod` causes AttributeError; malformed geometry becomes readable; a corrupted extraction truncates an existing destination; an unexpected error is swallowed; Linux fresh publication becomes a pathname rebind; or exact-source specialized CI is missing/red.
- Alternatives: avoid `os.chmod(stage_name)` after verification (mutable pathname race), ignore mode-failure exceptions blindly (masks programming errors), or rearchitect Windows staged replacement (not necessary for this portability fix).
- Scope: the existing-target post-SHA attacker publication vulnerability still exists on POSIX/Windows; platform-specific permissions metadata are not proven equivalent; full generic CI, RSS/CPU/wall/performance, recovery, 4GiB ZIP64 and release gates remain separate.

No rewrite of original prereg, no format/version/threshold mutation, no merge or release decision. Owner source is the control; this is an explicit integration experiment, not a claimed invention.
