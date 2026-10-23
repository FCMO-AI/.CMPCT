"""Bounded-memory, verified and transactional sparse member materialization.

Extraction must prove the same logical SHA-256 that Reader.read checks: authentic
physical blobs and valid extent boundaries alone do not authenticate the zeros/offsets
that make up the full logical member. No existing destination is truncated before proof.
"""
from __future__ import annotations

import hashlib
import os
import tempfile

_ZERO = b'\x00' * (1024 * 1024)


def write_sparse_verified(reader, row, full: str) -> None:
    rel, _, mode, _, size, expected, storage = row
    if size < 0 or not isinstance(expected, (bytes, bytearray)) or len(expected) != 32:
        raise IOError(f'invalid sparse logical commitment: {rel}')
    # Reuse the independent short same-directory staging name from the chunked
    # extractor. Valid 255-byte POSIX basenames must not exceed NAME_MAX in staging.
    fd, tmp = tempfile.mkstemp(prefix='.cmpct-part-',
                               dir=os.path.dirname(full) or '.')
    committed = False
    digest = hashlib.sha256()

    def hash_holes(length: int) -> None:
        while length:
            n = min(length, len(_ZERO))
            digest.update(memoryview(_ZERO)[:n])
            length -= n

    try:
        os.ftruncate(fd, size)
        cursor = 0
        for offset, extent_length, blob_ids in storage[1]:
            if offset < cursor or extent_length < 0 or offset + extent_length > size:
                raise IOError(f'invalid sparse extent boundary: {rel}')
            hash_holes(offset - cursor)
            physical_cursor = offset
            for blob_id in blob_ids:
                chunk = reader._blob(blob_id)
                if len(chunk) > offset + extent_length - physical_cursor:
                    raise IOError(f'sparse extent overrun: {rel}')
                digest.update(chunk)
                data = memoryview(chunk)
                while data:
                    if hasattr(os, 'pwrite'):
                        n = os.pwrite(fd, data, physical_cursor)
                    else:
                        os.lseek(fd, physical_cursor, os.SEEK_SET)
                        n = os.write(fd, data)
                    if n <= 0:
                        raise IOError(f'short sparse write: {rel}')
                    data = data[n:]
                    physical_cursor += n
            if physical_cursor != offset + extent_length:
                raise IOError(f'sparse extent length mismatch: {rel}')
            cursor = physical_cursor
        hash_holes(size - cursor)
        if digest.digest() != bytes(expected):
            raise IOError(f'sparse logical integrity failure: {rel}')
        # Keep staging private until verification; failure must preserve existing target bytes.
        try:
            os.fchmod(fd, mode or 0o666)
        except OSError:
            pass
        os.close(fd)
        fd = -1
        os.replace(tmp, full)
        committed = True
    finally:
        if fd >= 0:
            os.close(fd)
        if not committed:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
