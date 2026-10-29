#!/usr/bin/env python3
"""J24I24: source-FD relay ABA falsifier; research only, no product modifications.

A pre-dirtied shared mapping can swap one internally valid physical RAW record
without changing inode/mtime/ctime. The signed file-row SHA must still bind
logical content, even if two whole-file SHA observations happen to match.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import bounded_fd_relay as relay_module
from test_bounded_fd_relay import make_wire
from cmpct.reader import CMPCT

# Separate wire parser, deliberately not calling the relay's index/record parser.
HEAD = struct.Struct('<8sHHQQQ32s')
BLOB = struct.Struct('<4sBBHQQII32s')
PAYLOAD_A = b'A' * 1024
PAYLOAD_B = b'B' * 1024


def physical_snapshot(path: Path):
    raw = path.read_bytes()
    magic, version, flags, clen, ulen, span, _ = HEAD.unpack_from(raw)
    assert magic == b'CMPCT24\x00' and version == 24 and flags == 0
    # Single independently built direct-RAW record begins after primary index.
    start = HEAD.size + clen
    magic, codec, flags, reserved, usize, csize, mlen, crc, digest = BLOB.unpack_from(raw, start)
    assert magic == b'CMA4' and (codec, flags, reserved, mlen) == (0, 0, 0, 0)
    payload = raw[start + BLOB.size:start + BLOB.size + csize]
    assert len(payload) == usize == csize == 1024
    assert (binascii.crc32(payload) & 0xffffffff) == crc
    assert hashlib.sha256(payload).digest() == digest
    return {"wire": raw, "start": start, "end": start + BLOB.size + csize,
            "payload": payload, "blob_digest": digest.hex(),
            "file_sha256": hashlib.sha256(raw).hexdigest(), "index_compressed_bytes": clen}


def swap_record(payload: bytes) -> bytes:
    return BLOB.pack(b'CMA4', 0, 0, 0, len(payload), len(payload), 0,
                     binascii.crc32(payload) & 0xffffffff,
                     hashlib.sha256(payload).digest()) + payload


def witness(fd: int):
    s = os.fstat(fd)
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


class SharedMmapABACourt(unittest.TestCase):
    def test_control_clean_source_exact(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td)/'clean.cmpct', Path(td)/'clean.out'
            make_wire(src, PAYLOAD_A)
            result = relay_module.relay(src, dst)
            self.assertEqual(src.read_bytes(), dst.read_bytes())
            with CMPCT(dst) as reader:
                self.assertEqual(reader.read('blob.bin'), PAYLOAD_A)
                self.assertEqual(reader.verify(), 1)
            print('J24I24_CLEAN', json.dumps({"source_sha":result['source_sha256'],
                  "target_sha":result['destination_sha256'],"bytes":dst.stat().st_size}), flush=True)

    def test_control_persistent_mmap_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td)/'mutated.cmpct', Path(td)/'mutated.out'
            make_wire(src, PAYLOAD_A)
            initial = physical_snapshot(src)
            replacement = swap_record(PAYLOAD_B)
            with open(src, 'r+b') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_WRITE) as mm:
                def mutate():
                    mm[initial['start']:initial['end']] = replacement
                with self.assertRaises(ValueError):
                    relay_module.relay(src, dst, after_admit=mutate)
            self.assertFalse(dst.exists())
            self.assertNotEqual(hashlib.sha256(src.read_bytes()).hexdigest(), initial['file_sha256'])
            print('J24I24_PERSISTENT', json.dumps({"rejected":True,
                  "source_sha_changed":True,"destination_absent":True}), flush=True)

    def test_mmap_aba_crosses_source_hash_and_inode_witness(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td)/'aba.cmpct', Path(td)/'aba.out'
            make_wire(src, PAYLOAD_A)
            initial = physical_snapshot(src)
            self.assertLess(initial['end'], mmap.PAGESIZE)  # one shared dirty page
            old_record = initial['wire'][initial['start']:initial['end']]
            replacement = swap_record(PAYLOAD_B)
            self.assertEqual(len(old_record),len(replacement))
            with open(src, 'r+b') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_WRITE) as mm:
                # First dirty mark has happened *before* relay's initial fstat.
                data_offset = initial['start'] + BLOB.size
                mm[data_offset] = ord('C')
                mm[data_offset] = ord('A')
                original_stat = witness(stream.fileno())
                observations = {"injected":0,"restored":0}
                original_verify = relay_module.verify_record

                def after_admit():
                    observations['injected'] += 1
                    mm[initial['start']:initial['end']] = replacement
                    self.assertEqual(witness(stream.fileno()), original_stat)

                def observe_then_restore(fd, blob, base, size, outfd=None):
                    copied = original_verify(fd, blob, base, size, outfd)
                    observations['restored'] += 1
                    mm[initial['start']:initial['end']] = old_record
                    self.assertEqual(witness(stream.fileno()), original_stat)
                    return copied

                # Only external adversary scheduling hooks; original relay and
                # original verify_record process all unchanged logical/physical data.
                with patch.object(relay_module,'verify_record',side_effect=observe_then_restore):
                    receipt = relay_module.relay(src, dst, after_admit=after_admit)
                final_stat = witness(stream.fileno())
                self.assertEqual(original_stat,final_stat)
                self.assertEqual(observations,{"injected":1,"restored":1})

            final_source = physical_snapshot(src)
            final_dest = physical_snapshot(dst)
            self.assertEqual(final_source['wire'], initial['wire'])
            self.assertEqual(final_source['file_sha256'],receipt['source_sha256'])
            self.assertEqual(final_source['payload'], PAYLOAD_A)
            self.assertEqual(final_dest['payload'], PAYLOAD_B)
            self.assertNotEqual(final_dest['file_sha256'],final_source['file_sha256'])
            # CRC and physical SHA of B genuinely pass, so this is not malformed
            # compressed-input rejection. The *logical* SHA row still binds A.
            with CMPCT(dst) as reader:
                with self.assertRaises((IOError, ValueError, RuntimeError)):
                    reader.verify()
            print('J24I24_ABA_COUNTEREXAMPLE',json.dumps({
                "accepted": True, "source_sha_before":initial['file_sha256'],
                "source_sha_after":final_source['file_sha256'],
                "output_sha":final_dest['file_sha256'],
                "source_blob_sha":final_source['blob_digest'],
                "output_blob_sha":final_dest['blob_digest'],
                "unchanged_fstat":original_stat==final_stat,
                "physical_output_self_authenticated":True,
                "reader_logical_verify_rejected":True,
                "bytes":len(final_dest['wire']), "mutations":observations},sort_keys=True),flush=True)


if __name__=='__main__':
    unittest.main(verbosity=2)
