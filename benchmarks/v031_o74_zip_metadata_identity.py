#!/usr/bin/env python3
"""O74: prove standard ZIP metadata equality is not a content-identity certificate.

Pure-stdlib deterministic CRC32 suffix inversion and actual ZIP writer/reader.
Optionally verify separate physical ZIPs through installed CMPCT r24 end-to-end.
Research evidence only; changes no shipping encoder, parser or benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import time
import zipfile
import zlib

N = 64 * 1024


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def crc_patch(prefix: bytes, target: int) -> bytes:
    """Solve exactly for a four-byte suffix giving target ZIP CRC32.

    For a fixed prefix and fixed 32-bit suffix length, CRC differences form a
    linear GF(2) mapping; basis vectors are obtained from the *actual* zlib CRC.
    """
    zero = prefix + bytes(4)
    crc_zero = zlib.crc32(zero)
    pivot_rows: dict[int, tuple[int, int]] = {}
    for bit in range(32):
        variant = prefix + (1 << bit).to_bytes(4, 'little')
        delta = zlib.crc32(variant) ^ crc_zero
        mask = 1 << bit
        while delta:
            pivot = delta.bit_length() - 1
            if pivot not in pivot_rows:
                pivot_rows[pivot] = (delta, mask)
                break
            old_delta, old_mask = pivot_rows[pivot]
            delta ^= old_delta
            mask ^= old_mask
    if len(pivot_rows) != 32:
        raise AssertionError('CRC32 suffix mapping unexpectedly not full rank')
    rhs = target ^ crc_zero
    patch_mask = 0
    while rhs:
        pivot = rhs.bit_length() - 1
        delta, mask = pivot_rows[pivot]
        rhs ^= delta
        patch_mask ^= mask
    patch = patch_mask.to_bytes(4, 'little')
    if zlib.crc32(prefix + patch) != target:
        raise AssertionError('independent zlib CRC target disagreement')
    return patch


def zip_wire(raw: bytes) -> bytes:
    # Fixed ZIP metadata, same member name and standard Deflate level 6.
    member = zipfile.ZipInfo('payload.bin', (1980, 1, 1, 0, 0, 0))
    member.compress_type = zipfile.ZIP_DEFLATED
    member.external_attr = 0o600 << 16
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', allowZip64=False) as z:
        z.writestr(member, raw, compress_type=zipfile.ZIP_DEFLATED,
                   compresslevel=6)
    return mem.getvalue()


def parse_zip(physical: bytes, expected: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(physical), 'r') as z:
        if z.namelist() != ['payload.bin']:
            raise AssertionError('unexpected ZIP member table')
        info = z.getinfo('payload.bin')
        read = z.read('payload.bin')
        if read != expected:
            raise AssertionError('ZIP decompression source mismatch')
        meta = (
            info.filename, info.CRC, info.file_size, info.compress_size,
            info.compress_type, info.flag_bits, info.date_time,
            info.create_system, info.external_attr, info.header_offset,
        )
        header_offset = info.header_offset
        header = physical[header_offset:header_offset + 30]
        if len(header) != 30 or struct.unpack_from('<I', header)[0] != 0x04034B50:
            raise AssertionError('missing standard ZIP local header')
        filename_len, extra_len = struct.unpack_from('<HH', header, 26)
        comp_start = header_offset + 30 + filename_len + extra_len
        comp_end = comp_start + info.compress_size
        if comp_end > len(physical):
            raise AssertionError('invalid compressed stream bounds')
        return {
            'meta': meta,
            'header': physical[:comp_start],
            'compressed': physical[comp_start:comp_end],
            'tail': physical[comp_end:],
        }


def run(require_cmpct: bool) -> dict:
    a = hashlib.shake_256(b'CMPCT-O74-raw-a-v1').digest(N)
    b_prefix = hashlib.shake_256(b'CMPCT-O74-raw-b-v1').digest(N - 4)
    target = zlib.crc32(a)
    b = b_prefix + crc_patch(b_prefix, target)
    # Independent exactness checks: source differs despite equal ZIP CRC and length.
    if a == b or sha(a) == sha(b):
        raise AssertionError('control source equality defeats discriminator')
    if len(a) != len(b) or zlib.crc32(b) != target:
        raise AssertionError('CRC patch failed')
    # Validate the GF(2) inversion algorithm against known suffixes not used for
    # the collision. This does not depend on a CMPCT parser or its Builder.
    for suffix in (0, 1, 0x12345678, 0xFFFFFFFF):
        expected = suffix.to_bytes(4, 'little')
        got = crc_patch(b_prefix, zlib.crc32(b_prefix + expected))
        if got != expected:
            raise AssertionError('CRC patch solver control failed')
    zip_a, zip_b = zip_wire(a), zip_wire(b)
    p_a, p_b = parse_zip(zip_a, a), parse_zip(zip_b, b)
    metadata_equal = p_a['meta'] == p_b['meta']
    header_equal = p_a['header'] == p_b['header']
    tail_equal = p_a['tail'] == p_b['tail']
    same_physical_length = len(zip_a) == len(zip_b)
    distinct_compressed = sha(p_a['compressed']) != sha(p_b['compressed'])
    disposition = ('FULL_METADATA_COLLISION' if all((metadata_equal,
        header_equal, tail_equal, same_physical_length,
        distinct_compressed)) else 'NARROW_OR_FAIL')
    report = {
        'schema': 'cmpct-o74-zip-metadata-identity-v1',
        'disposition': disposition,
        'bytes_per_expanded_payload': N,
        'zip_crc32_both': f'{target:08x}',
        'expanded_sha256': [sha(a), sha(b)],
        'compressed_stream_sha256': [sha(p_a['compressed']), sha(p_b['compressed'])],
        'original_zip_sha256': [sha(zip_a), sha(zip_b)],
        'original_zip_sizes': [len(zip_a), len(zip_b)],
        'central_directory_metadata_equal': metadata_equal,
        'identical_complete_local_headers': header_equal,
        'identical_complete_central_directory_and_eocd_tail': tail_equal,
        'same_physical_zip_length': same_physical_length,
        'different_compressed_stream': distinct_compressed,
        'simulated_crc_only_alias_is_lossless': a == b,
        'zip_metadata': {'filename': p_a['meta'][0], 'crc32': p_a['meta'][1],
                         'usize': p_a['meta'][2], 'csize': p_a['meta'][3],
                         'method': p_a['meta'][4], 'flags': p_a['meta'][5]},
        'product': 'UNMEASURED',
    }
    if require_cmpct:
        from cmpct.builder import Builder
        from cmpct.reader import CMPCT
        with tempfile.TemporaryDirectory(prefix='cmpct-o74-') as td:
            root = Path(td) / 'source'
            root.mkdir()
            (root / 'zip-a.zip').write_bytes(zip_a)
            (root / 'zip-b.zip').write_bytes(zip_b)
            archive = Path(td) / 'product.cmpct'
            t = time.perf_counter()
            Builder(root, workers=1, reproducible=True,
                    reproducible_epoch_ns=0).build(archive)
            creation_wall_s = time.perf_counter() - t
            with CMPCT(archive) as ar:
                if ar.verify() < 1:
                    raise AssertionError('CMPCT verifier refused valid archive')
                if ar.read('zip-a.zip') != zip_a or ar.read('zip-b.zip') != zip_b:
                    raise AssertionError('CMPCT conflated distinct ZIP content')
                dest = Path(td) / 'restored'
                ar.extractall(dest)
                if (dest / 'zip-a.zip').read_bytes() != zip_a:
                    raise AssertionError('CMPCT first ZIP reconstruction mismatch')
                if (dest / 'zip-b.zip').read_bytes() != zip_b:
                    raise AssertionError('CMPCT second ZIP reconstruction mismatch')
            report['product'] = {
                'status': 'EXACT_SEPARATE_ZIPS',
                'archive_sha256': sha(archive.read_bytes()),
                'archive_size': archive.stat().st_size,
                'create_wall_s_single_unreplicated': creation_wall_s,
                'note': 'single hosted correctness run only, no performance credit',
            }
    # No positive full-tuple proof if compression produced different lengths;
    # the weaker CRC+usize collision still exists and is recorded honestly.
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-cmpct', action='store_true')
    parser.add_argument('--output', type=Path)
    opts = parser.parse_args()
    result = run(opts.require_cmpct)
    raw = json.dumps(result, sort_keys=True, indent=2)
    if opts.output:
        opts.output.parent.mkdir(parents=True, exist_ok=True)
        opts.output.write_text(raw + '\n', encoding='utf-8')
    print(raw)
    if result['disposition'] != 'FULL_METADATA_COLLISION':
        raise SystemExit('O74 full-fingerprint prediction not established')


if __name__ == '__main__':
    main()
