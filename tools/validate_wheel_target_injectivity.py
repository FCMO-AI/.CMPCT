#!/usr/bin/env python3
"""Conservative read-only wheel-member -> installed-package path injectivity guard.

This is a *portable naming* preflight, not a cryptographic provenance proof or
an installer emulator. In an ordinary venv, wheel root members and PEP 427's
.data/purelib and .data/platlib members can all land in site-packages. The
mapping must not allow two distinct ZIP members to claim one package pathname.

The guard additionally rejects dangerous spelling aliases, including Unicode
normalization and case aliases, without relying on the current host filesystem.
Package RECORD hashes and runtime installation checks belong to separate gates.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
import zipfile
from pathlib import Path

MAX_ENTRIES = 8192
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_NAME_BYTES = 4096
MAX_COMPONENTS = 256
DATA_SECTIONS = frozenset({'purelib', 'platlib', 'headers', 'scripts', 'data'})
WINDOWS_DEVICES = frozenset({'CON', 'PRN', 'AUX', 'NUL'}) | {f'COM{i}' for i in range(1, 10)} | {f'LPT{i}' for i in range(1, 10)}


def _name_parts(name: str) -> tuple[str, ...]:
    if not name or name.startswith('/') or name.endswith('//') or '\\' in name or '\x00' in name:
        raise ValueError(f'unsafe wheel member spelling: {name!r}')
    if len(name.encode('utf-8')) > MAX_NAME_BYTES:
        raise ValueError('wheel member name too long')
    # ZIP paths are POSIX-style. A trailing slash is a directory marker, not
    # an empty descendant, but may never be used to disambiguate two files.
    parts = name.rstrip('/').split('/')
    if len(parts) > MAX_COMPONENTS or not parts or any(not p or p in ('.', '..') for p in parts):
        raise ValueError(f'noncanonical wheel path: {name!r}')
    for part in parts:
        if any(ord(c) < 32 for c in part) or part.endswith((' ', '.')) or ':' in part:
            raise ValueError(f'nonportable wheel path component: {part!r}')
        if part.split('.')[0].upper() in WINDOWS_DEVICES:
            raise ValueError(f'Windows device-name component: {part!r}')
    return tuple(parts)


def _portable_key(parts: tuple[str, ...]) -> tuple[str, ...]:
    # Deliberately conservative portability boundary across Windows/APFS,
    # not a claim to replicate every host's case folding algorithm exactly.
    return tuple(unicodedata.normalize('NFD', c).casefold() for c in parts)


def _target_namespace(parts: tuple[str, ...], data_roots: frozenset[str]) -> tuple[str, tuple[str, ...]]:
    if parts[0] not in data_roots:
        return 'site', parts
    if len(parts) < 3 or parts[1] not in DATA_SECTIONS:
        raise ValueError('malformed or unknown PEP 427 .data scheme path')
    section = parts[1]
    # The ordinary venv site-packages target is shared by root/purelib/platlib.
    if section in ('purelib', 'platlib'):
        return 'site', parts[2:]
    return section, parts[2:]


def validate(path: str | Path) -> dict[str, object]:
    path = Path(path)
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('wheel exceeds byte limit')
    with zipfile.ZipFile(path) as whl:
        infos = whl.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ValueError('wheel exceeds entry limit')
        named = [(i, _name_parts(i.filename)) for i in infos]
        dist_infos = {p[0][:-10] for _, p in named if len(p) == 2 and p[0].endswith('.dist-info') and p[1] == 'WHEEL'}
        if len(dist_infos) != 1:
            raise ValueError('expected exactly one root .dist-info/WHEEL file')
        wheel_stem = next(iter(dist_infos))
        data_roots = frozenset({wheel_stem + '.data'})
        seen: dict[tuple[str, tuple[str, ...]], str] = {}
        files: set[tuple[str, tuple[str, ...]]] = set()
        count = 0
        for info, parts in named:
            namespace, target = _target_namespace(parts, data_roots)
            # An unrecognized .data prefix is not assumed safe or ignored.
            if parts[0].endswith('.data') and parts[0] not in data_roots:
                raise ValueError('unexpected .data root')
            key = (namespace, _portable_key(target))
            if key in seen:
                raise ValueError(f'installed target collision: {seen[key]!r} vs {info.filename!r}')
            seen[key] = info.filename
            if not info.is_dir():
                files.add(key)
            count += 1
        for namespace, components in seen:
            for end in range(1, len(components)):
                ancestor = (namespace, components[:end])
                if ancestor in files:
                    raise ValueError(f'installed file shadows descendant: {seen[ancestor]!r} vs {seen[(namespace, components)]!r}')
        return {'result': 'PASS', 'wheel': path.name, 'members': count,
                'site_targets': sum(ns == 'site' for ns, _ in seen),
                'scheme_targets': count - sum(ns == 'site' for ns, _ in seen),
                'scope': 'portable static member-to-target injectivity; not installer/installed-byte proof'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wheel', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.wheel), sort_keys=True))
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print(json.dumps({'result': 'REJECT', 'wheel': args.wheel.name, 'reason': str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
