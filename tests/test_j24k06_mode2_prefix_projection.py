"""J24K06: independent two-stream VZIP coordinate oracle and hostile mode2 length lies.

This fixture has no archive Builder, Reader, or validator dependency: only the
range primitive is under test. The expected stream is constructed directly
from a skeleton and raw zlib Deflate bytes.
"""
from __future__ import annotations

import copy
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
