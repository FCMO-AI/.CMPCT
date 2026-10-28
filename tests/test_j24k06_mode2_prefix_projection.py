"""J24K06: independent two-stream VZIP coordinate oracle and hostile mode2 length lies.

This fixture has no archive Builder, Reader, or validator dependency: only the
range primitive is under test. The expected stream is constructed directly
from a skeleton and raw zlib Deflate bytes.
"""
from __future__ import annotations

import copy
import random
import zlib
import zipfile

import pytest

from cmpct.codec import range_vzip


def _deflate(raw: bytes, level: int = 6) -> bytes:
    co = zlib.compressobj(level, zlib.DEFLATED, -15)
    return co.compress(raw) + co.flush()


def _fixture():
    raw1 = b"alpha-beta-" * 37
    raw2 = b"gamma-delta-" * 43
    cp1, cp2 = _deflate(raw1), _deflate(raw2)
    literals = [b"AB", b"MIDDLE", b"TAIL"]
    skeleton = b"".join(literals)
    exact = literals[0] + cp1 + literals[1] + cp2 + literals[2]
    recipe = [
        0, list(map(len, literals)),
        [[1, zipfile.ZIP_DEFLATED, 2, 1, len(cp1), 6],
         [2, zipfile.ZIP_DEFLATED, 2, 2, len(cp2), 6]],
        b"\0" * 32, len(exact), 0,
    ]
    content = {0: skeleton, 1: raw1, 2: raw2}
    calls = []

    def get_content(idx):
        return content[idx]

    def get_stream(mode, idx, level):
        calls.append((mode, idx, level))
        return _deflate(content[idx], level) if mode == 2 else {1: cp1, 2: cp2}[idx]

    return recipe, exact, calls, get_content, get_stream, len(cp1), len(cp2)


def test_valid_two_mode2_streams_match_independent_concat_for_selective_offsets():
    recipe, exact, calls, get_content, get_stream, cp1, cp2 = _fixture()
    # A prefix that ends before the first regenerated Deflate stream must remain lazy.
    assert range_vzip(recipe, get_content, get_stream, 0, 1) == b"A"
    assert calls == []
    # Empty reads must not regenerate skipped mode2 streams, even at EOF.
    for empty_start in (0, 2 + cp1, len(exact) - 1, len(exact)):
        calls.clear()
        assert range_vzip(recipe, get_content, get_stream, empty_start, 0) == b""
        assert calls == []
    with pytest.raises(ValueError, match="range outside virtual ZIP"):
        range_vzip(recipe, get_content, get_stream, len(exact) + 1, 0)
    starts = [0, 1, 2, 3, 2 + cp1 - 1, 2 + cp1,
              2 + cp1 + 6, 2 + cp1 + 6 + cp2 - 1,
              len(exact) - 1, len(exact)]
    for start in starts:
        for count in [0, min(1, len(exact) - start), len(exact) - start]:
            got = range_vzip(recipe, get_content, get_stream, start, count)
            assert got == exact[start:start + count]
    # A suffix beyond the two compressed streams must traverse both for
    # coordinate proof, not silently trust either declared length.
    calls.clear()
    assert range_vzip(recipe, get_content, get_stream, len(exact) - 1, 1) == exact[-1:]
    assert calls == [(2, 1, 6), (2, 2, 6)]


@pytest.mark.parametrize("which,delta", [(0, 1), (0, -1), (1, 1), (1, -1)])
def test_signed_mode2_length_lie_before_suffix_fails_closed(which, delta):
    recipe, exact, calls, get_content, get_stream, cp1, cp2 = _fixture()
    forged = copy.deepcopy(recipe)
    forged[2][which][4] += delta
    forged[4] += delta
    # This logical suffix remains inside the declared recipe bounds. A
    # length-only result postcondition cannot detect a shifted last literal.
    start = len(exact) - 2 if delta >= 0 else len(exact) - 3
    with pytest.raises(IOError, match="virtual ZIP selective reconstruction length mismatch"):
        range_vzip(forged, get_content, get_stream, start, 1)


@pytest.mark.parametrize("delta", [1, -1])
def test_overlapping_mode2_mismatch_fails_even_if_slice_length_is_correct(delta):
    recipe, exact, calls, get_content, get_stream, cp1, cp2 = _fixture()
    forged = copy.deepcopy(recipe)
    forged[2][0][4] += delta
    forged[4] += delta
    with pytest.raises(IOError, match="virtual ZIP selective reconstruction length mismatch"):
        range_vzip(forged, get_content, get_stream, 3, 1)


def test_unrelated_retained_deflate_and_stored_streams_remain_selective():
    recipe, exact, calls, get_content, get_stream, cp1, cp2 = _fixture()
    # The first Deflate stream is physically retained and the second is STORED.
    raw2 = b"gamma-delta-" * 43
    retained_cp1 = _deflate(b"alpha-beta-" * 37)
    recipe[2][0][2] = 1
    recipe[2][1][1] = zipfile.ZIP_STORED
    recipe[2][1][4] = len(raw2)
    recipe[4] = len(exact) - cp2 + len(raw2)
    reconstructed = b"AB" + retained_cp1 + b"MIDDLE" + raw2 + b"TAIL"
    assert len(reconstructed) == recipe[4]
    calls.clear()
    assert range_vzip(recipe, get_content, get_stream, len(reconstructed)-1, 1) == b"L"
    # Skipped retained/STORED data does not require regeneration.
    assert calls == []


def test_seeded_heldout_mixed_recipe_offsets_and_mode2_size_lies():
    """Exercise structural generality, not a memorized frozen-archive identity."""
    rng = random.Random(20261028)
    for trial in range(96):
        count = rng.randrange(1, 7)
        literals = [rng.randbytes(rng.randrange(0, 14)) for _ in range(count)]
        literals.append(rng.randbytes(rng.randrange(1, 14)))  # suffix always exists
        blobs = {0: b"".join(literals)}
        streams = {}
        payloads = []
        out = []
        for i in range(count):
            raw = rng.randbytes(rng.randrange(0, 90))
            idx = i + 1
            blobs[idx] = raw
            mode = rng.choice((0, 1, 2))
            if mode == 0:
                method, cp = zipfile.ZIP_STORED, raw
            else:
                method, cp = zipfile.ZIP_DEFLATED, _deflate(raw)
            streams[idx] = cp
            payloads.append([idx, method, mode, idx, len(cp), 6])
            out += [literals[i], cp]
        out.append(literals[-1])
        truth = b"".join(out)
        recipe = [0, [len(x) for x in literals], payloads, b"\0" * 32, len(truth), 0]
        calls = []

        def content(idx):
            return blobs[idx]

        def stream(mode, idx, level):
            calls.append(idx)
            return _deflate(blobs[idx], level) if mode == 2 else streams[idx]

        for _ in range(12):
            start = rng.randrange(0, len(truth) + 1)
            length = rng.randrange(0, len(truth) - start + 1)
            assert range_vzip(recipe, content, stream, start, length) == truth[start:start+length], trial
        # Independent csize mutation on one discoverable regenerated stream.
        regenerated = [i for i, p in enumerate(payloads) if p[2] == 2]
        if regenerated:
            i = rng.choice(regenerated)
            for delta in (-1, 1):
                lie = copy.deepcopy(recipe)
                lie[2][i][4] += delta
                lie[4] += delta
                # Test the last reconstructed literal: the mismatched mode2
                # stream lies strictly before this selected range.
                calls.clear()
                with pytest.raises(IOError, match="virtual ZIP selective reconstruction length mismatch"):
                    range_vzip(lie, content, stream, len(truth) - 1, 1)
                assert i + 1 in calls
