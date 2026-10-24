from __future__ import annotations

"""Shared lexical path policy for portable, hostile-input-safe CMPCT logical paths.

The archive stores logical paths independent of host filesystem syntax. Every parser, extractor and
platform handler must therefore agree on one lexical key before touching a destination filesystem.
"""


def canonical_logical_path(path: str, *, max_path_bytes: int | None = None) -> tuple[str, tuple[str, ...]]:
    """Return the canonical slash-separated key and path components.

    Backslashes are treated as archive separators so ``a/b`` and ``a\\b`` cannot address the same
    destination under different index keys. ``.`` is rejected rather than silently normalized because
    accepting both spellings would create the same alias class. This is lexical only: Unicode and
    platform-specific case normalization remain a future normative-format decision.
    """
    if not isinstance(path, str):
        raise ValueError('logical path is not text')
    if '\x00' in path:
        raise ValueError('NUL in logical path')
    encoded = path.encode('utf-8', 'surrogatepass')
    if max_path_bytes is not None and len(encoded) > max_path_bytes:
        raise ValueError('logical path exceeds parser limit')
    normalized = path.replace('\\', '/')
    if not normalized or normalized.startswith('/'):
        raise ValueError('absolute or empty logical path')
    parts = tuple(normalized.split('/'))
    if any(part in ('', '.', '..') for part in parts):
        raise ValueError('unsafe logical path component')
    return '/'.join(parts), parts


# Windows destination admission is deliberately separate from the portable r24 logical grammar.
# POSIX file systems can represent names such as "a:b", while Win32 interprets the colon as a
# drive/alternate-stream separator. Refusing such names only at Windows materialization keeps
# the on-disk format and ordinary POSIX readers backward-compatible.
_WIN32_RESERVED_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
    *(f"COM{i}" for i in "123456789\u00b9\u00b2\u00b3"),
    *(f"LPT{i}" for i in "123456789\u00b9\u00b2\u00b3"),
})
_WIN32_SPECIAL_CHARS = frozenset('<>:"|?*')


def canonical_windows_extraction_key(parts: tuple[str, ...]) -> str:
    """Conservative Win32 name admission and lexical collision key for extraction.

    Windows drive-relative names and alternate streams are not confined by a POSIX-style
    path-component check. Device aliases, Win32 normalization, and case-insensitive
    collisions can also change the resulting tree. This key is an admission bound, not a
    claim to model every possible NTFS Unicode collation or case-sensitive directory.
    """
    if not parts:
        raise ValueError("unsafe Windows empty member path")
    for part in parts:
        if not isinstance(part, str) or not part or part in (".", ".."):
            raise ValueError("unsafe Windows path component")
        if any(ord(ch) < 32 or ch in _WIN32_SPECIAL_CHARS for ch in part):
            raise ValueError("unsafe Windows drive, stream, or reserved character")
        if part.endswith((" ", ".")):
            raise ValueError("unsafe Windows trailing dot/space alias")
        stem = part.split(".", 1)[0].rstrip(" ").upper()
        if stem in _WIN32_RESERVED_NAMES:
            raise ValueError("unsafe Windows device name")
    return "/".join(part.casefold() for part in parts)
