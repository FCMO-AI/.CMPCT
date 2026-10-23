"""Fail-closed sparse materialization: logical SHA proof and atomic publication."""
import base64
import hashlib
import json
import os
from pathlib import Path
import pytest

from cmpct.reader import CMPCT
from cmpct.sparse_extract import write_sparse_verified

FIXTURE = Path(__file__).resolve().parent / 'conformance' / 'v24-sparse.json'


def test_frozen_sparse_roundtrip_and_reject_mismatched_logical_sha(tmp_path):
    fixture = json.loads(FIXTURE.read_text())
    packed = base64.b64decode(fixture['archive']['base64'])
    assert hashlib.sha256(packed).hexdigest() == fixture['archive']['sha256']
    archive = tmp_path / 'frozen.cmpct'
    archive.write_bytes(packed)
    with CMPCT(archive) as reader:
        expected = reader.read(fixture['member']['path'])
        assert hashlib.sha256(expected).hexdigest() == fixture['member']['sha256']
        dest = tmp_path / 'output'
        reader.extractall(dest, metadata=False)
        output = dest / fixture['member']['path']
        assert output.read_bytes() == expected
        inode = os.stat(output).st_ino
        row = reader.by[fixture['member']['path']]
        row[5] = hashlib.sha256(b'forged-alternate-content').digest()
        with pytest.raises(OSError, match='sparse logical integrity failure'):
            reader.extractall(dest, metadata=False)
        assert output.read_bytes() == expected
        assert os.stat(output).st_ino == inode
        assert not list(dest.glob('.*cmpct-part-*'))


class BlobSource:
    def __init__(self, chunks, fail=False):
        self.chunks, self.fail = chunks, fail

    def _blob(self, blob_id):
        if self.fail:
            raise IOError('injected physical blob failure')
        return self.chunks[blob_id]


def test_sparse_holes_preserved_and_verified_in_bounded_memory(tmp_path):
    size = 16 * 1024 * 1024
    chunks = [b'anchor' * 31, b'tail' * 43]
    off1, off2 = 4096, size - 1024
    digest = hashlib.sha256()
    zeros = b'\x00' * 1024 * 1024

    def add_zero(n):
        while n:
            take = min(n, len(zeros))
            digest.update(memoryview(zeros)[:take])
            n -= take

    add_zero(off1)
    digest.update(chunks[0])
    add_zero(off2 - off1 - len(chunks[0]))
    digest.update(chunks[1])
    add_zero(size - off2 - len(chunks[1]))
    row = ['data', 0, 0o640, 0, size, digest.digest(),
           [3, [[off1, len(chunks[0]), [0]], [off2, len(chunks[1]), [1]]]]]
    dest = tmp_path / 'data'
    write_sparse_verified(BlobSource(chunks), row, str(dest))
    assert dest.stat().st_size == size
    with dest.open('rb') as stream:
        stream.seek(off1)
        assert stream.read(len(chunks[0])) == chunks[0]
        stream.seek(off2)
        assert stream.read(len(chunks[1])) == chunks[1]
        stream.seek(size // 2)
        assert stream.read(1024) == b'\x00' * 1024
    assert hashlib.sha256(dest.read_bytes()).digest() == row[5]


@pytest.mark.parametrize('mutate', ['bad_hash','extent_overrun','extent_underflow','overlap','blob_failure'])
def test_sparse_failure_preserves_preexisting_destination(tmp_path, mutate):
    data = b'visible-physical-data'
    size = 4096
    raw = b'\x00' * 42 + data + b'\x00' * (size - 42 - len(data))
    row = ['safe', 0, 0o644, 0, size, hashlib.sha256(raw).digest(),
           [3, [[42, len(data), [0]]]]]
    src = BlobSource([data])
    if mutate == 'bad_hash':
        row[5] = b'X' * 32
    elif mutate == 'extent_overrun':
        row[6][1] = [[size - 1, len(data), [0]]]
    elif mutate == 'extent_underflow':
        row[6][1] = [[42, len(data) + 1, [0]]]
    elif mutate == 'overlap':
        row[6][1] = [[42, len(data), [0]], [42, len(data), [0]]]
    elif mutate == 'blob_failure':
        src.fail = True
    path = tmp_path / 'safe'
    path.write_bytes(b'original-outside-target')
    inode = path.stat().st_ino
    with pytest.raises(OSError):
        write_sparse_verified(src, row, str(path))
    assert path.read_bytes() == b'original-outside-target'
    assert path.stat().st_ino == inode
    assert not list(tmp_path.glob('.*cmpct-part-*'))
