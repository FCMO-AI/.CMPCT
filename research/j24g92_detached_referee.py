#!/usr/bin/env python3
"""Independent r24 J24G92 wire referee: stdlib, msgpack, zstandard, no CMPCT import."""
import hashlib
import json
import pathlib
import struct
import sys
import msgpack
import zstandard as zstd

F = struct.Struct('<8sBBBBQQQ32s')
assert F.size == 68

def sha(data):
    return hashlib.sha256(data).hexdigest()


def footer(raw, pos):
    assert 0 < pos and pos + F.size <= len(raw)
    magic, kind, codec, flags, res, cs, us, prev, ph = F.unpack_from(raw, pos)
    assert magic == b'CMPTF24\x00' and kind in (0, 1) and flags == res == 0
    assert 0 < cs <= pos and 0 < us and 0 <= prev < pos
    comp = raw[pos-cs:pos]
    assert codec in (0, 1)
    if codec == 0:
        payload = comp
    else:
        payload = zstd.ZstdDecompressor().decompress(comp, max_output_size=us)
    assert len(payload) == us and hashlib.sha256(payload).digest() == ph
    return {'pos': pos, 'prev': prev, 'kind': kind, 'payload_sha': ph.hex(),
            'index': msgpack.unpackb(payload, raw=False)}


def chain(raw):
    found = []
    p = len(raw) - F.size
    visited = set()
    while p:
        assert p not in visited and len(found) < 8
        visited.add(p)
        entry = footer(raw, p)
        found.append(entry)
        p = entry['prev']
    assert found[-1]['kind'] == 0 and all(x['kind'] == 1 for x in found[:-1])
    return found[::-1]


def reconstruct(c):
    names = {x[0] for x in c[0]['index']['files']}
    for entry in c[1:]:
        delta = entry['index']
        assert delta['blobs'] == [] and len(delta['ops']) == 1
        op = delta['ops'][0]
        assert len(op) == 2 and op[0] == 'del' and op[1] in names
        names.remove(op[1])
    return names


def audit(root, n, record):
    files = {label: (root / f'{n}-{label}.cmpct').read_bytes()
             for label in ('normal', 'rewired', 'bad_digest', 'out_of_bounds')}
    base = files['normal']
    changed = files['rewired']
    assert len({len(x) for x in files.values()}) == 1
    for label, raw in files.items():
        meta = record['answers'][label]
        assert len(raw) == meta['physical_bytes']
        assert sha(raw) == meta['whole_file_sha256']
    original = chain(base)
    rewired = chain(changed)
    assert len(original) == 4 and len(rewired) == 3
    assert original[-1]['pos'] == rewired[-1]['pos']
    assert original[-1]['payload_sha'] == rewired[-1]['payload_sha']
    assert original[-1]['prev'] == original[-2]['pos']
    assert rewired[-1]['prev'] == original[-3]['pos']
    assert F.unpack_from(base, len(base)-F.size)[-1] == (
        F.unpack_from(changed, len(changed)-F.size)[-1])
    edits = [i for i, (a, b) in enumerate(zip(base, changed)) if a != b]
    assert edits == record['changed_byte_positions'] and len(edits) <= 8
    assert all(original[-1]['pos'] + 28 <= i <
               original[-1]['pos'] + 36 for i in edits)

    original_names = reconstruct(original)
    changed_names = reconstruct(rewired)
    assert changed_names - original_names == {'f00001.dat'}
    assert not original_names - changed_names
    assert len(original_names) == n-3 and len(changed_names) == n-2
    assert sha(base) != sha(changed)
    for invalid in (files['bad_digest'], files['out_of_bounds']):
        try:
            chain(invalid)
        except (AssertionError, ValueError):
            pass
        else:
            raise AssertionError('malformed footer accepted by detached wire court')

    for label, names in [('normal', original_names), ('rewired', changed_names)]:
        reader = record['answers'][label]['reader']
        if reader['accepted'] and (
                label == 'normal' or record['installed_reader_silent_rewire']):
            assert set(reader['paths']) == names
            for name, digest in reader['sha256_by_path'].items():
                i = int(name[1:6])
                actual = hashlib.sha256(f'j24g92-{n}-{i}'.encode()).digest()
                assert digest == sha(actual)
    bad = record['answers']['bad_digest']['reader']
    assert bad['accepted']
    assert set(bad['paths']) == original_names | {'f00002.dat'}
    return {'n': n, 'full_bytes': len(base), 'field_bytes_changed': len(edits),
            'original_files': len(original_names), 'altered_files': len(changed_names),
            'sha_protected_payload_unchanged': True,
            'original_sha': sha(base), 'altered_sha': sha(changed),
            'installed_reader_h1': record['installed_reader_silent_rewire'],
            'installed_preflight_h2': record['installed_preflight_silent_rewire']}


def main():
    root = pathlib.Path(sys.argv[1])
    receipt = json.loads((root/'receipt.json').read_text())
    assert receipt['status'] == 'PASS'
    assert receipt['source']['reader_blob'] == 'e716233403dabd0966863c45635e18fa5ac6afb8'
    result = {
        'schema': 'j24g92-detached-referee-v1',
        'source_head': receipt['source']['head'],
        'limitation': 'metadata and installed receipt attestation only; no independent CMPCT Reader import',
        'cases': {},
    }
    for n in (16, 128):
        result['cases'][str(n)] = audit(root, n, receipt['cases'][str(n)])
    (root/'detached-referee.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({n: (
        x['field_bytes_changed'], x['installed_reader_h1'], x['installed_preflight_h2'])
        for n, x in result['cases'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
