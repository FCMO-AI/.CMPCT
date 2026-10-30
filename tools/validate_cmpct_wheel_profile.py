#!/usr/bin/env python3
"""Read-only, conservative CMPCT *publishing* wheel pathname preflight.

This deliberately rejects *all* PEP 427 .data scheme relocation because
CMPCT's current official-style wheels do not need it. This is not a validator
for arbitrary standards-compliant wheels, publisher signatures, payload RECORD
hashes, actual installation outputs, or OS-level race freedom. Compose it with
validate_macos_wheel_abi.py and real installed/native smoke before publishing.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
import zipfile
from pathlib import Path

MAX_WHEEL_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 8192
MAX_MEMBER_NAME_BYTES = 4096
MAX_COMPONENTS = 256
WIN_DEVICES = frozenset({'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'}) | {f'COM{i}' for i in range(1, 10)} | {f'LPT{i}' for i in range(1, 10)}
WIN_FORBIDDEN = set('<>:"|?*\\')


def _components(name: str) -> tuple[str, ...]:
    if not name or name.startswith('/') or name.endswith('//') or any(c in WIN_FORBIDDEN for c in name) or '\x00' in name:
        raise ValueError(f'unsafe wheel member spelling: {name!r}')
    if len(name.encode('utf-8')) > MAX_MEMBER_NAME_BYTES:
        raise ValueError('wheel member pathname exceeds byte budget')
    segments = name.rstrip('/').split('/')
    if len(segments) > MAX_COMPONENTS or any(not c or c in ('.', '..') for c in segments):
        raise ValueError(f'noncanonical relative wheel member: {name!r}')
    for segment in segments:
        if segment.endswith((' ', '.')) or any(ord(c) < 32 or ord(c) == 127 for c in segment):
            raise ValueError(f'nonportable wheel path component: {segment!r}')
        device = unicodedata.normalize('NFKC', segment.split('.')[0]).upper()
        if device in WIN_DEVICES:
            raise ValueError(f'Windows device-name component: {segment!r}')
    return tuple(segments)


def validate(path: str | Path) -> dict[str, object]:
    path = Path(path)
    if path.stat().st_size > MAX_WHEEL_BYTES:
        raise ValueError('wheel exceeds publication size bound')
    with zipfile.ZipFile(path) as wheel:
        infos = wheel.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ValueError('wheel exceeds entry count bound')
        exact_wheels = 0
        seen = {}
        file_keys = set()
        for info in infos:
            parts = _components(info.filename)
            # J24P07's physically measured .data/data scheme collision showed
            # a general static relocation map is NOT a trustworthy solution.
            # The current CMPCT shipping package has no .data scheme payloads.
            if unicodedata.normalize('NFKC', parts[0]).casefold().endswith('.data'):
                raise ValueError(f'CMPCT official wheel may not use .data relocation: {info.filename!r}')
            if len(parts) == 2 and parts[0].endswith('.dist-info') and parts[1] == 'WHEEL':
                exact_wheels += 1
            key = tuple(unicodedata.normalize('NFD', p).casefold() for p in parts)
            if key in seen:
                raise ValueError(f'portable wheel pathname collision: {seen[key]!r} vs {info.filename!r}')
            seen[key] = info.filename
            if not info.is_dir():
                file_keys.add(key)
        if exact_wheels != 1:
            raise ValueError(f'expected one root .dist-info/WHEEL: {exact_wheels}')
        for key, path_name in seen.items():
            for n in range(1, len(key)):
                ancestor = key[:n]
                if ancestor in file_keys:
                    raise ValueError(f'regular member shadows destination directory: {seen[ancestor]!r} vs {path_name!r}')
        return {'result': 'PASS', 'wheel': path.name, 'members': len(infos),
                'policy': 'CMPCT-specific portable no-.data publication profile; no installed-state attestation'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('wheel', type=Path)
    args = p.parse_args()
    try:
        print(json.dumps(validate(args.wheel), sort_keys=True))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        print(json.dumps({'result': 'REJECT', 'wheel': args.wheel.name, 'reason': str(exc)}, sort_keys=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
