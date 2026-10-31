#!/usr/bin/env python3
"""Bind a final CMPCT wheel's console entry points to its source TOML contract.

Run *after final wheel retag and existing whole-wheel RECORD/root preflight* and
*before pip install*. This is a CMPCT publication profile, not generic PEP 427
validation, publisher authentication, or installed-launcher byte attestation.
The actual installed CLI must also be smoked on each target OS.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

MAX_WHEEL_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 8192
MAX_ENTRY_POINTS_BYTES = 65536
MAX_SOURCE_MANIFEST_BYTES = 256 * 1024
# Keep the public console command in the shipping package. The source manifest
# can evolve its callable; the generated executable still needs a real smoke.
CMPCT_TARGET = re.compile(r"cmpct(?:\.[A-Za-z_][A-Za-z0-9_]*)+:[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$", re.ASCII)


def _expected(manifest: Path) -> tuple[str, str, str]:
    try:
        import tomllib  # build-gate Python >= 3.11; installed product still supports 3.10
    except ImportError as exc:
        raise ValueError('publication CLI guard requires Python 3.11+ to parse TOML with the stdlib') from exc
    # Parse and hash one exact source-descriptor snapshot rather than reopening
    # a mutable pathname after deriving the expected entrypoint contract.
    with manifest.open('rb') as stream:
        source_bytes = stream.read(MAX_SOURCE_MANIFEST_BYTES + 1)
    if len(source_bytes) > MAX_SOURCE_MANIFEST_BYTES:
        raise ValueError('source manifest exceeds publication size bound')
    try:
        data = tomllib.loads(source_bytes.decode('utf-8', errors='strict'))
    except UnicodeError as exc:
        raise ValueError('source manifest must be UTF-8') from exc
    project = data.get('project')
    if not isinstance(project, dict) or project.get('name') != 'cmpct':
        raise ValueError('source manifest project name is not cmpct')
    version = project.get('version')
    if not isinstance(version, str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('source manifest does not identify a fixed CMPCT version')
    scripts = project.get('scripts')
    if not isinstance(scripts, dict) or list(scripts.keys()) != ['cmpct']:
        raise ValueError('CMPCT publication must declare exactly the cmpct console script')
    target = scripts['cmpct']
    if not isinstance(target, str) or not CMPCT_TARGET.fullmatch(target):
        raise ValueError('source CMPCT console target is not a local qualified callable')
    if 'gui-scripts' in project and project['gui-scripts']:
        raise ValueError('source manifest unexpectedly declares GUI scripts')
    return version, target, hashlib.sha256(source_bytes).hexdigest()


def _parse_entry_points(payload: bytes) -> dict[str, str]:
    if len(payload) > MAX_ENTRY_POINTS_BYTES:
        raise ValueError('entry_points.txt exceeds bound')
    try:
        text = payload.decode('utf-8', errors='strict')
    except UnicodeError as exc:
        raise ValueError('entry_points.txt must be UTF-8') from exc
    parser = configparser.ConfigParser(interpolation=None, strict=True, delimiters=('=',))
    parser.optionxform = str  # Default case-folding can falsely accept a different script name.
    try:
        parser.read_file(io.StringIO(text))
    except configparser.Error as exc:
        raise ValueError('invalid console entrypoint metadata') from exc
    if parser.defaults() or parser.sections() != ['console_scripts']:
        raise ValueError('wheel must declare only the expected console_scripts section')
    return dict(parser.items('console_scripts', raw=True))


def inspect(wheel: Path | str, manifest: Path | str) -> dict[str, object]:
    wheel = Path(wheel)
    manifest = Path(manifest)
    version, target, source_sha = _expected(manifest)
    if not wheel.is_file() or wheel.stat().st_size > MAX_WHEEL_BYTES:
        raise ValueError('final wheel missing or oversized')
    if not wheel.name.startswith(f'cmpct-{version}-') or not wheel.name.endswith('.whl'):
        raise ValueError('wheel filename is not for source CMPCT version')
    entry = f'cmpct-{version}.dist-info/entry_points.txt'
    # Keep read and digest on one wheel descriptor to avoid post-verification
    # pathname substitution. Whole-wheel RECORD/root safety is owned by #867.
    with wheel.open('rb') as stream:
        with zipfile.ZipFile(stream) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ENTRIES:
                raise ValueError('final wheel exceeds member bound')
            candidates = [i for i in infos if i.orig_filename.endswith('/entry_points.txt')]
            if len(candidates) != 1 or candidates[0].orig_filename != entry or candidates[0].is_dir():
                raise ValueError('expected exactly one version-bound entry_points.txt')
            if candidates[0].file_size > MAX_ENTRY_POINTS_BYTES:
                raise ValueError('entry_points.txt exceeds size bound')
            entry_bytes = archive.read(candidates[0])
            options = _parse_entry_points(entry_bytes)
            if options != {'cmpct': target}:
                raise ValueError('wheel console entrypoint differs from authoritative source manifest')
            entry_sha = hashlib.sha256(entry_bytes).hexdigest()
        stream.seek(0)
        sha = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
        wheel_sha = sha.hexdigest()
    return {
        'schema': 'cmpct-final-wheel-cli-contract-v1',
        'result': 'PASS', 'wheel': wheel.name, 'wheel_sha256': wheel_sha,
        'source_manifest_sha256': source_sha,  # diagnostic raw checkout bytes; may be CRLF on Windows
        # Windows Git checkouts can normalize source line endings differently.
        # Preserve exact local bytes above, but compare portable *contract*
        # semantics across hosts rather than treating CRLF as implementation drift.
        'source_semantic_sha256': hashlib.sha256(json.dumps(
            {'name': 'cmpct', 'version': version, 'cmpct': target},
            sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(),
        'entry_points_sha256': entry_sha,
        'console_script': {'name': 'cmpct', 'target': target},
        'scope': 'source-bound final-wheel console metadata; not generated launcher identity, pip trust, or publisher signature',
    }


def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('wheel', type=Path)
    args.add_argument('--source-manifest', type=Path, default=Path('pyproject.toml'))
    args.add_argument('--output', type=Path)
    o = args.parse_args()
    try:
        receipt = inspect(o.wheel, o.source_manifest)
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError, UnicodeError) as exc:
        receipt = {'schema': 'cmpct-final-wheel-cli-contract-v1', 'result': 'REJECT', 'reason': str(exc)}
    payload = json.dumps(receipt, sort_keys=True, indent=2) + '\n'
    print(payload, end='')
    if o.output is not None:
        o.output.write_text(payload, encoding='utf-8')
    return 0 if receipt['result'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
