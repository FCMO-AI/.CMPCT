"""J24K09 held-out synthetic VZIP mixed-stream geometry.

Lower-rung deterministic oracle, not a signed archive or product benchmark.
Test every new physical witness against an independently concatenated byte truth.
"""
from __future__ import annotations

import copy
import random
import zipfile
import zlib

import pytest

from cmpct.codec import range_vzip


def _deflate(raw):
    c = zlib.compressobj(6, zlib.DEFLATED, -15)
    return c.compress(raw) + c.flush()


def test_seeded_heldout_mixed_physical_streams_and_suffix_perturbations():
    rng = random.Random(24092026)
    trials = 180
    valid_ranges = 0
    bad_offsets = 0
    positive_mode_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for trial in range(trials):
        n = rng.randrange(1, 10)
        literals = [rng.randbytes(rng.randrange(0, 12)) for _ in range(n)]
        literals.append(rng.randbytes(rng.randrange(3, 12)))
        skeleton = b"".join(literals)
        contents = {0: skeleton}
        streams = {}
        rows = []
        assembled = []
        for k in range(n):
            idx = k + 1
            raw = rng.randbytes(rng.randrange(1, 91))
            tag = rng.randrange(4)
            method = zipfile.ZIP_STORED if tag == 0 else zipfile.ZIP_DEFLATED
            mode = 0 if tag == 0 else tag - 1
            stream = raw if method == zipfile.ZIP_STORED else _deflate(raw)
            contents[idx] = raw
            streams[idx] = stream
            rows.append([idx, method, mode, idx, len(stream), 6])
            assembled.extend((literals[k], stream))
            positive_mode_counts[tag] += 1
        assembled.append(literals[-1])
        truth = b"".join(assembled)
        recipe = [0, [len(x) for x in literals], rows, b"\0" * 32, len(truth), 0]
        calls = []
        def content(idx):
            return contents[idx]
        def stream(mode, idx, level):
            calls.append(("decode", idx))
            return streams[idx]
        def physical_size(method, mode, rawref, streamref):
            idx = rawref if method == zipfile.ZIP_STORED else streamref
            calls.append(("size", idx))
            return len(streams[idx])
        for _ in range(12):
            start = rng.randrange(len(truth) + 1)
            length = rng.randrange(len(truth) - start + 1)
            got = range_vzip(recipe, content, stream, start, length, physical_size)
            assert got == truth[start:start+length], (trial, start, length)
            valid_ranges += 1

        # The final skeleton is long enough to hold a suffix probe even after
        # a -1 declared-size mutation.  Select each prior nonmode2 owner.
        for i, row in enumerate(rows):
            if row[1] == zipfile.ZIP_DEFLATED and row[2] == 2:
                continue
            for delta in (-1, 1):
                candidate = copy.deepcopy(recipe)
                candidate[2][i][4] += delta
                candidate[4] += delta
                offset = len(truth) - 2
                assert offset >= 0 and offset + 1 <= candidate[4]
                with pytest.raises(IOError, match="selective reconstruction length mismatch"):
                    range_vzip(candidate, content, stream, offset, 1, physical_size)
                bad_offsets += 1
    assert valid_ranges == 2160
    assert bad_offsets > 250
    assert all(v > 0 for v in positive_mode_counts.values())
