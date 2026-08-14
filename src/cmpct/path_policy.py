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
