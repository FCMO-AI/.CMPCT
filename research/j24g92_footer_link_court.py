#!/usr/bin/env python3
"""J24G92: physical r24 parent-link rewire vs installed Reader and strict preflight.

Research-only. Preserve the released engine, frozen evaluator, and format.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile

import msgpack
import zstandard as zstd
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from cmpct.validation import preflight_archive

BASE_HEAD = '129edec976efe8bb604584517de39553487fec34'
PREREG = '0b27b674ee76263882cfee0883a2150091f2a65e'
READER_BLOB = 'e716233403dabd0966863c45635e18fa5ac6afb8'
FOOTER = struct.Struct('<8sBBBBQQQ32s')
PREV_OFFSET = struct.calcsize('<8sBBBBQQ')
assert FOOTER.size == 68 and PREV_OFFSET == 28


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def attest() -> dict:
    def git(*args):
        return subprocess.check_output(['git', *args], text=True).strip()
    head = git('rev-parse', 'HEAD')
    for ancestor in (PREREG, BASE_HEAD):
        subprocess.run(['git', 'merge-base', '--is-ancestor', ancestor, 'HEAD'], check=True)
    assert git('rev-parse', 'HEAD:src/cmpct/reader.py') == READER_BLOB
    return {'head': head, 'parent': BASE_HEAD, 'prereg': PREREG,
            'reader_blob': READER_BLOB}


def footer(raw: bytes, pos: int) -> dict:
    assert 0 < pos and pos + FOOTER.size <= len(raw)
    magic, kind, codec, flags, reserved, cs, us, previous, ph = FOOTER.unpack_from(raw, pos)
    assert magic == b'CMPTF24\x00' and kind in (0, 1) and flags == reserved == 0
    assert cs > 0 and us > 0 and cs <= pos and 0 <= previous < pos
    comp = raw[pos - cs:pos]
    assert codec in (0, 1)
    payload = comp if codec == 0 else zstd.ZstdDecompressor().decompress(comp, max_output_size=us)
    assert len(payload) == us and hashlib.sha256(payload).digest() == ph
    return {'pos': pos, 'prev': previous, 'kind': kind, 'payload_sha': ph.hex(),
            'payload': msgpack.unpackb(payload, raw=False)}


def lineage(raw: bytes) -> list[dict]:
    chain = []
    seen = set()
    pos = len(raw) - FOOTER.size
    while pos:
        assert pos not in seen and len(chain) < 70
        seen.add(pos)
        entry = footer(raw, pos)
        chain.append(entry)
        pos = entry['prev']
    assert chain[-1]['kind'] == 0 and all(f['kind'] == 1 for f in chain[:-1])
    return chain[::-1]


def independent_rows(chain: list[dict]) -> set[str]:
    files = {row[0] for row in chain[0]['payload']['files']}
    for entry in chain[1:]:
        delta = entry['payload']
        assert delta['blobs'] == [] and len(delta['ops']) == 1
        op = delta['ops'][0]
        assert len(op) == 2 and op[0] == 'del' and op[1] in files
        files.remove(op[1])
    return files


def inspect_reader(path: Path) -> dict:
    try:
        with CMPCT(path) as reader:
            names = sorted(reader.by)
            assert reader.verify() == len(names)
            content = {name: sha(reader.read(name)) for name in names}
            return {'accepted': True, 'paths': names, 'sha256_by_path': content,
                    'footer': reader.latest_footer_pos, 'delta_depth': reader.delta_depth}
    except Exception as exc:
        return {'accepted': False, 'error': type(exc).__name__, 'detail': str(exc)[:500]}


def inspect_preflight(path: Path) -> dict:
    try:
        return {'accepted': True, 'result': preflight_archive(path)}
    except Exception as exc:
        return {'accepted': False, 'error': type(exc).__name__, 'detail': str(exc)[:500]}


def one_case(root: Path, n: int, evidence: Path) -> dict:
    source = root / f'source_{n}'
    source.mkdir()
    original_hashes = {}
    for i in range(n):
        name = f'f{i:05d}.dat'
        content = hashlib.sha256(f'j24g92-{n}-{i}'.encode()).digest()
        (source / name).write_bytes(content)
        original_hashes[name] = sha(content)

    normal = root / f'{n}-normal.cmpct'
    Builder(source, workers=1, reproducible=False).build(normal)
    for i in range(3):
        append_delete(normal, f'f{i:05d}.dat')
    raw = normal.read_bytes()
    initial_chain = lineage(raw)
    assert len(initial_chain) == 4
    original_set = independent_rows(initial_chain)
    assert original_set == set(original_hashes) - {
        'f00000.dat', 'f00001.dat', 'f00002.dat'}

    latest, predecessor, grandparent = initial_chain[-3:][::-1]
    assert latest['prev'] == predecessor['pos']
    assert predecessor['prev'] == grandparent['pos']

    # Deliberately leave the SHA-256 authenticated payload *unaltered*.
    rewired = bytearray(raw)
    struct.pack_into('<Q', rewired, latest['pos'] + PREV_OFFSET, grandparent['pos'])
    rewired = bytes(rewired)
    altered_chain = lineage(rewired)
    altered_set = independent_rows(altered_chain)
    expected_rewired = original_set | {'f00001.dat'}
    assert altered_set == expected_rewired and len(altered_chain) == 3
    assert footer(raw, latest['pos'])['payload_sha'] == footer(
        rewired, latest['pos'])['payload_sha']
    changed_positions = [i for i, (a, b) in enumerate(zip(raw, rewired)) if a != b]
    assert len(raw) == len(rewired) and 1 <= len(changed_positions) <= 8
    assert all(latest['pos'] + PREV_OFFSET <= i <
               latest['pos'] + PREV_OFFSET + 8 for i in changed_positions)

    bad_digest = bytearray(raw)
    bad_digest[-1] ^= 0x5A
    bad_parent = bytearray(raw)
    struct.pack_into('<Q', bad_parent, latest['pos'] + PREV_OFFSET, len(raw) + 100)
    variants = {'normal': raw, 'rewired': rewired,
                'bad_digest': bytes(bad_digest), 'out_of_bounds': bytes(bad_parent)}
    answers = {}
    for label, data in variants.items():
        p = root / f'{n}-{label}.cmpct'
        p.write_bytes(data)
        assert p.stat().st_size == len(data)
        answers[label] = {
            'physical_bytes': len(data), 'whole_file_sha256': sha(data),
            'reader': inspect_reader(p), 'preflight': inspect_preflight(p)}
        shutil.copyfile(p, evidence / f'{n}-{label}.cmpct')

    baseline = answers['normal']
    assert baseline['reader']['accepted'] and baseline['preflight']['accepted']
    assert set(baseline['reader']['paths']) == original_set
    assert baseline['reader']['delta_depth'] == 3
    for name, digest in baseline['reader']['sha256_by_path'].items():
        assert original_hashes[name] == digest

    # A corrupted *stored digest* should select the preceding valid generation.
    bad = answers['bad_digest']['reader']
    assert bad['accepted'] and set(bad['paths']) == original_set | {'f00002.dat'}
    candidate = answers['rewired']['reader']
    if candidate['accepted']:
        assert set(candidate['paths']) in (original_set, expected_rewired)
        for name, digest in candidate['sha256_by_path'].items():
            assert original_hashes[name] == digest
    preflight = answers['rewired']['preflight']
    if preflight['accepted']:
        assert preflight['result']['files'] in (len(original_set), len(expected_rewired))
    accepted_rewire = (candidate['accepted'] and
                       set(candidate['paths']) == expected_rewired and
                       candidate['footer'] == latest['pos'])
    preflight_rewire = (preflight['accepted'] and
                        preflight['result']['files'] == len(expected_rewired) and
                        preflight['result']['latest_footer'] == latest['pos'])
    return {
        'n': n, 'original_footer_payload_sha256': latest['payload_sha'],
        'modified_footer_payload_sha256': footer(rewired, latest['pos'])['payload_sha'],
        'changed_byte_positions': changed_positions,
        'baseline_members': len(original_set),
        'independent_rewired_members': len(expected_rewired),
        'independent_resurrected_member': 'f00001.dat',
        'installed_reader_silent_rewire': accepted_rewire,
        'installed_preflight_silent_rewire': preflight_rewire,
        'reader_preflight_agree': accepted_rewire == preflight_rewire,
        'answers': answers,
    }


def main() -> None:
    evidence = Path(os.environ.get('J24G92_EVIDENCE', 'evidence/j24g92'))
    evidence.mkdir(parents=True, exist_ok=True)
    report = {
        'schema': 'cmpct-j24g92-footer-link-installed-court-v1',
        'source': attest(), 'host': platform.platform(), 'python': sys.version,
        'product_source_modified': False, 'product_credit': 0,
        'status': 'STARTED', 'cases': {},
    }
    try:
        with tempfile.TemporaryDirectory(prefix='cmpct-j24g92-') as tmp:
            root = Path(tmp)
            for n in (16, 128):
                report['cases'][str(n)] = one_case(root, n, evidence)
        report['reader_h1'] = [
            x['installed_reader_silent_rewire'] for x in report['cases'].values()]
        report['preflight_h2'] = [
            x['installed_preflight_silent_rewire'] for x in report['cases'].values()]
        report['decision'] = ('REWIRE_ACCEPTED' if all(report['reader_h1']) else
                              'REWIRE_REJECTED' if not any(report['reader_h1']) else
                              'HOSTILE_SHAPE_DEPENDENT')
        report['status'] = 'PASS'
    except BaseException as exc:
        report['status'] = 'FAIL'
        report['fatal'] = {'type': type(exc).__name__, 'detail': str(exc)}
        raise
    finally:
        (evidence / 'receipt.json').write_text(
            json.dumps(report, sort_keys=True, indent=2) + '\n')
        print('J24G92_REPORT', json.dumps({
            'status': report['status'], 'decision': report.get('decision'),
            'cases': {k: {
                'reader': v['installed_reader_silent_rewire'],
                'preflight': v['installed_preflight_silent_rewire'],
                'parity': v['reader_preflight_agree'],
            } for k, v in report['cases'].items()},
        }, sort_keys=True))


if __name__ == '__main__':
    main()
