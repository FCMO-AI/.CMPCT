#!/usr/bin/env python3
"""Read-only, conservative CMPCT *publishing* wheel pathname preflight.

This deliberately rejects *all* PEP 427 .data scheme relocation because
CMPCT's current official-style wheels do not need it. The official wheel
also permits only CMPCT package files + its one dist-info root; an arbitrary
root .pth could execute during interpreter startup before installed SHA audit.
This is not a validator
for arbitrary standards-compliant wheels, publisher signatures, payload RECORD
hashes, actual installation outputs, or OS-level race freedom. Compose it with
validate_macos_wheel_abi.py and real installed/native smoke before publishing.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import unicodedata
import zipfile
from pathlib import Path

MAX_WHEEL_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 8192
MAX_DECODED_BYTES = 512 * 1024 * 1024
MAX_RECORD_BYTES = 8 * 1024 * 1024
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
        device = unicodedata.normalize('NFKC', segment.split('.')[0]).rstrip(' ').upper()  # Win32 treats CON .txt as CON, not a harmless filename
        if device in WIN_DEVICES:
            raise ValueError(f'Windows device-name component: {segment!r}')
    return tuple(segments)


def _verify_record(wheel: zipfile.ZipFile, infos: list[zipfile.ZipInfo], record_name: str) -> None:
    """Require current payloads and metadata to match the wheel's entire RECORD.

    Pip install success is not evidence of RECORD integrity (J24P09c).
    Every member is hashed via bounded streaming before any installed code runs.
    """
    files = {info.filename: info for info in infos if not info.is_dir()}
    info = files.get(record_name)
    if info is None or info.file_size > MAX_RECORD_BYTES:
        raise ValueError('missing or oversized wheel RECORD')
    if sum(item.file_size for item in files.values()) > MAX_DECODED_BYTES:
        raise ValueError('total decoded wheel bytes exceed preflight budget')
    try:
        record = wheel.read(info).decode('utf-8')
        rows = list(csv.reader(io.StringIO(record, newline='')))
    except (UnicodeError, csv.Error, RuntimeError) as exc:
        raise ValueError('invalid wheel RECORD encoding') from exc
    names: dict[str, tuple[str, str]] = {}
    for row in rows:
        if len(row) != 3 or not row[0] or row[0] in names:
            raise ValueError('duplicate or invalid wheel RECORD row')
        names[row[0]] = row[1], row[2]
    if set(names) != set(files):
        raise ValueError('RECORD path set does not match wheel payload members')
    if names[record_name] != ('', ''):
        raise ValueError('RECORD self-row must have empty digest and size')
    for name, member in files.items():
        if name == record_name:
            continue
        row_digest, row_size = names[name]
        if row_size != str(member.file_size) or not row_digest.startswith('sha256='):
            raise ValueError(f'RECORD missing valid SHA-256 or size: {name!r}')
        digest = hashlib.sha256()
        with wheel.open(member) as source:
            for chunk in iter(lambda: source.read(1 << 20), b''):
                digest.update(chunk)
        actual = base64.urlsafe_b64encode(digest.digest()).rstrip(b'=').decode('ascii')
        if row_digest != 'sha256=' + actual:
            raise ValueError(f'RECORD SHA-256 mismatches wheel bytes: {name!r}')


def validate(path: str | Path) -> dict[str, object]:
    path = Path(path)
    if path.stat().st_size > MAX_WHEEL_BYTES:
        raise ValueError('wheel exceeds publication size bound')
    with zipfile.ZipFile(path) as wheel:
        infos = wheel.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ValueError('wheel exceeds entry count bound')
        exact_wheels = 0
        metadata_roots = set()
        seen = {}
        file_keys = set()
        for info in infos:
            parts = _components(info.orig_filename)  # Python zipfile normalizes backslashes on Windows
            # J24P07's physically measured .data/data scheme collision showed
            # a general static relocation map is NOT a trustworthy solution.
            # The current CMPCT shipping package has no .data scheme payloads.
            if unicodedata.normalize('NFKC', parts[0]).casefold().endswith('.data'):
                raise ValueError(f'CMPCT official wheel may not use .data relocation: {info.filename!r}')
            # J24P09b: a standards-compliant root .pth can execute before
            # post-install attestation, even if every cmpct/ file still matches.
            # This narrow CMPCT-only allowlist avoids that extra execution root.
            root = parts[0]
            expected_metadata_root = f"cmpct-{path.name.split('-')[1]}.dist-info" if len(path.name.split('-')) >= 3 else ""
            if root == 'cmpct':
                pass
            elif root == expected_metadata_root:
                metadata_roots.add(root)
            else:
                raise ValueError(f'wheel entry outside CMPCT publication roots: {info.filename!r}')
            if len(parts) == 2 and root == expected_metadata_root and parts[1] == 'WHEEL':
                exact_wheels += 1
            key = tuple(unicodedata.normalize('NFD', p).casefold() for p in parts)
            if key in seen:
                raise ValueError(f'portable wheel pathname collision: {seen[key]!r} vs {info.filename!r}')
            seen[key] = info.filename
            if not info.is_dir():
                file_keys.add(key)
        if exact_wheels != 1 or len(metadata_roots) != 1:
            raise ValueError(f'expected exactly one matching CMPCT .dist-info/WHEEL root: {exact_wheels}')
        # J24P09c: pip may install a wheel with altered bytes and stale RECORD.
        # Validate the *final retagged* artifact, before installation on any OS.
        _verify_record(wheel, infos, next(iter(metadata_roots)) + '/RECORD')
        for key, path_name in seen.items():
            for n in range(1, len(key)):
                ancestor = key[:n]
                if ancestor in file_keys:
                    raise ValueError(f'regular member shadows destination directory: {seen[ancestor]!r} vs {path_name!r}')
        return {'result': 'PASS', 'wheel': path.name, 'members': len(infos),
                'policy': 'CMPCT-specific two-root no-.data plus complete RECORD publication profile; no installed-state attestation'}


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
