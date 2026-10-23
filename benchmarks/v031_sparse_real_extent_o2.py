#!/usr/bin/env python3
"""O2 research-only real POSIX sparse acquisition for O1 experimental Merkle.

No CMPCT product/format changes. O1 Merkle != r24 flat logical SHA-256.
Source stability is only observed with fstat before/after, not transactionally frozen.
"""
from __future__ import annotations
import errno
import hashlib
import json
import os
import pathlib
import resource
import statistics
import tempfile
import time
import tracemalloc
from collections import Counter

from v031_sparse_merkle_collapsed_o1 import Collapsed
from v031_sparse_merkle_proof_economics_o0 import leaf_hash
from v031_sparse_merkle_independent_falsifier import reference_root

MIB = 1 << 20
LEAF = 1 << 16
MAX_DESCRIPTOR_BYTES = 4 * MIB
MAX_STEPS = 100_000
MAX_READ = 1 << 16
UNSUPPORTED = {errno.EINVAL, errno.ENOSYS, getattr(errno, 'EOPNOTSUPP', 95), getattr(errno, 'ENOTSUP', 95)}


def scan_extents(fd: int, length: int, *, seek=os.lseek, max_steps=MAX_STEPS):
    """Return sorted DATA spans, treating only affirmative SEEK_HOLE reports as zeros.

    A filesystem may classify physically allocated zeros as DATA: that is safe but costly.
    On unsupported seek, fail over to a conservative whole-file data span.
    """
    if not hasattr(os, 'SEEK_DATA') or not hasattr(os, 'SEEK_HOLE'):
        return [(0, length)] if length else [], 'whole-file-fallback', 0
    offset, spans, steps = 0, [], 0
    while offset < length:
        steps += 1
        if steps > max_steps:
            raise ValueError('extent scan step budget exceeded')
        try:
            begin = seek(fd, offset, os.SEEK_DATA)
        except OSError as exc:
            if exc.errno == errno.ENXIO:
                break  # no subsequent data: rest is an affirmative filesystem hole
            if exc.errno in UNSUPPORTED:
                return [(0, length)] if length else [], 'whole-file-fallback', steps
            raise
        if type(begin) is not int or not offset <= begin < length:
            raise ValueError('incoherent SEEK_DATA position')
        try:
            end = seek(fd, begin, os.SEEK_HOLE)
        except OSError as exc:
            if exc.errno in UNSUPPORTED:
                return [(0, length)] if length else [], 'whole-file-fallback', steps
            raise
        if type(end) is not int or not begin < end <= length:
            raise ValueError('incoherent SEEK_HOLE position')
        spans.append((begin, end))
        offset = end
    return spans, 'seek-hole-data', steps


def _source_identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def assemble_descriptor(fd, *, leaf_size=LEAF, max_bytes=MAX_DESCRIPTOR_BYTES,
                        seek=os.lseek, max_steps=MAX_STEPS):
    """Streaming acquisition: one leaf buffer, all descriptor rows explicitly charged.

    A row can be omitted for an allocated all-zero leaf *only after reading its bytes*.
    This matches O1's zero-leaf root, not physical hole allocation identity.
    """
    start_stat = os.fstat(fd)
    length = start_stat.st_size
    if length < 0 or length >= 1 << 64:
        raise ValueError('invalid file size')
    spans, method, steps = scan_extents(fd, length, seek=seek, max_steps=max_steps)
    rows = {}
    buffered_leaf = None
    page = None
    bytes_read = 0
    visited_allocated_leaves = 0

    def flush():
        nonlocal buffered_leaf, page, visited_allocated_leaves
        if page is None:
            return
        visited_allocated_leaves += 1
        # The complete raw logical leaf is present, zeros included; no uncharged fact.
        if any(page):
            if 48 + 40 * (len(rows) + 1) > max_bytes:
                raise ValueError('descriptor budget exceeded')
            rows[buffered_leaf] = leaf_hash(bytes(page))
        page = None
        buffered_leaf = None

    for begin, end in spans:
        at = begin
        while at < end:
            ordinal, inner = divmod(at, leaf_size)
            if buffered_leaf != ordinal:
                flush()
                buffered_leaf = ordinal
                page = bytearray(min(leaf_size, length - ordinal * leaf_size))
            count = min(end - at, leaf_size - inner, MAX_READ)
            # pread short reads must never be silently interpreted as holes.
            b = os.pread(fd, count, at)
            if len(b) != count:
                raise ValueError('short read during real extent acquisition')
            page[inner:inner + count] = b
            bytes_read += count
            at += count
    flush()
    if _source_identity(os.fstat(fd)) != _source_identity(start_stat):
        raise ValueError('source changed during acquisition')
    obj = Collapsed(length, leaf_size, rows)
    wire = obj.serialize()
    if len(wire) > max_bytes:
        raise ValueError('serialized descriptor budget exceeded')
    cold = Collapsed.reopen(wire, max_rows=(max_bytes - 48) // 40)
    if cold.root != obj.root:
        raise AssertionError('cold root inconsistency')
    return obj, wire, {
        'method': method, 'seek_steps': steps, 'allocated_extent_count': len(spans),
        'allocated_extent_bytes': sum(b - a for a, b in spans),
        'source_bytes_pread': bytes_read, 'allocated_leaves_examined': visited_allocated_leaves,
        'committed_nonzero_leaves': len(rows), 'descriptor_bytes': len(wire),
        'physical_st_blocks_512': start_stat.st_blocks,
        'logical_bytes': length,
    }


def flat_sha_fd(fd, length):
    h, pos = hashlib.sha256(), 0
    while pos < length:
        block = os.pread(fd, min(MIB, length - pos), pos)
        if not block:
            raise ValueError('short full-data control read')
        h.update(block)
        pos += len(block)
    return h.digest()


def write_case(path, name):
    if name == 'dense':
        length = 32 * MIB
    elif name == 'partial-tail':
        length = 128 * MIB + 173
    else:
        length = 128 * MIB
    with open(path, 'wb', buffering=0) as f:
        f.truncate(length)
    fd = os.open(path, os.O_RDWR)
    try:
        if name == 'clustered':
            os.pwrite(fd, b'\xA5' * (4*MIB), 8*MIB)
        elif name == 'shifted':
            os.pwrite(fd, b'\xB6' * (4*MIB), 8*MIB + LEAF//2)
        elif name == 'allocated-zero':
            os.pwrite(fd, b'\x00' * (4*MIB), 8*MIB)
        elif name == 'fragmented':
            for i in range(length // LEAF):
                os.pwrite(fd, bytes([(i % 255)+1]), i * LEAF)
        elif name == 'dense':
            block = bytes((i % 251 for i in range(MIB)))
            for i in range(length // MIB):
                os.pwrite(fd, block, i*MIB)
        elif name == 'partial-tail':
            os.pwrite(fd, b'hello'*51, 23 * MIB + 3)
            os.pwrite(fd, b'END', length-3)
        elif name != 'all-hole':
            raise ValueError(name)
        os.fsync(fd)
    finally:
        os.close(fd)
    return length


def run_one(path, name):
    length = write_case(path, name)
    fd = os.open(path, os.O_RDONLY)
    try:
        first = assemble_descriptor(fd)
        # Independent fully materialized referee *outside candidate scope*; control is costly by design.
        content = bytearray()
        off = 0
        while off < length:
            b = os.pread(fd, min(MIB, length - off), off)
            if not b:
                raise AssertionError('short independent logical read')
            content.extend(b)
            off += len(b)
        exact_ref = reference_root(content, LEAF)
        flat_ref = hashlib.sha256(content).digest()
        assert first[0].root == exact_ref
        assert flat_sha_fd(fd, length) == flat_ref
        assert Collapsed.reopen(first[1]).root == exact_ref
        # Deliberately alternate orders and preserve individual raw timing observations.
        raw = []
        for iteration in range(3):
            order = ('candidate', 'flat') if iteration % 2 == 0 else ('flat', 'candidate')
            trial = {}
            for kind in order:
                ts, cs = time.perf_counter_ns(), time.process_time_ns()
                if kind == 'candidate':
                    candidate, wire, details = assemble_descriptor(fd)
                    assert candidate.root == exact_ref
                else:
                    assert flat_sha_fd(fd, length) == flat_ref
                trial[kind] = {'wall_ms':(time.perf_counter_ns()-ts)/1e6,
                               'cpu_ms':(time.process_time_ns()-cs)/1e6}
            raw.append(trial)
        del content
        tracemalloc.start()
        candidate, wire, details = assemble_descriptor(fd)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        details['tracemalloc_candidate_peak_bytes'] = peak
        details['case'] = name
        details['independent_root_matches'] = True
        details['flat_sha_matches'] = True
        details['median_candidate_wall_ms'] = statistics.median(x['candidate']['wall_ms'] for x in raw)
        details['median_flat_wall_ms'] = statistics.median(x['flat']['wall_ms'] for x in raw)
        details['raw'] = raw
        details['merkle_root'] = candidate.root.hex()
        details['flat_sha256'] = flat_ref.hex()
        details['seek_extent_structure_authentication'] = False
        return details
    finally:
        os.close(fd)


def adversarial_controls(path):
    write_case(path, 'clustered')
    fd = os.open(path, os.O_RDONLY)
    checks = 0
    try:
        def unsupported(_fd, _pos, _whence):
            raise OSError(errno.EOPNOTSUPP, 'unsupported')
        conservative = assemble_descriptor(fd, seek=unsupported)
        assert conservative[2]['method'] == 'whole-file-fallback'
        assert conservative[2]['source_bytes_pread'] == os.fstat(fd).st_size
        with open(path,'rb') as stream:
            assert conservative[0].root == reference_root(stream.read(), LEAF)
        checks += 1
        for broken in (
            lambda _fd, pos, _whence: pos-1,
            lambda _fd, pos, _whence: pos if pos else 0,
        ):
            try:
                assemble_descriptor(fd, seek=broken)
            except ValueError:
                checks += 1
            else:
                raise AssertionError('malformed seek location accepted')
        try:
            assemble_descriptor(fd, max_steps=0)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('scan budget ignored')
        try:
            assemble_descriptor(fd, max_bytes=48)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('index budget ignored')
        assert checks == 5
        return checks
    finally:
        os.close(fd)


def main():
    if os.name != 'posix' or not hasattr(os,'SEEK_HOLE'):
        raise RuntimeError('O2 court requires POSIX SEEK_HOLE/DATA for actual-source comparison')
    cases = []
    with tempfile.TemporaryDirectory(prefix='cmpct-o2-') as tmp:
        for name in ['all-hole','clustered','shifted','allocated-zero','fragmented','dense','partial-tail']:
            cases.append(run_one(os.path.join(tmp, name+'.bin'), name))
        hostile = adversarial_controls(os.path.join(tmp, 'hostile.bin'))
    roots = {x['case']:x['merkle_root'] for x in cases}
    assert roots['all-hole'] == roots['allocated-zero']  # same logical content, different allocation!
    all_hole = next(x for x in cases if x['case']=='all-hole')
    alloc_zero = next(x for x in cases if x['case']=='allocated-zero')
    assert alloc_zero['allocated_extent_bytes'] > all_hole['allocated_extent_bytes']
    assert all(x['independent_root_matches'] and x['flat_sha_matches'] for x in cases)
    assert next(x for x in cases if x['case']=='clustered')['descriptor_bytes'] <= 4096
    assert next(x for x in cases if x['case']=='fragmented')['descriptor_bytes'] > 4096
    print(json.dumps({'status':'PASS', 'scope':'research_O2_real_POSIX_not_CMPCT_product',
                      'hostile_controls':hostile,'cases':cases},sort_keys=True))


if __name__ == '__main__':
    main()
