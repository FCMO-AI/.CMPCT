"""J24K09: small independent stream-coordinate oracle; no archive fixtures."""
from __future__ import annotations

import zipfile
import pytest

from cmpct.codec import range_vzip


def _recipe(method=zipfile.ZIP_STORED, mode=0):
    # Logical layout is ABC + pq + WXYZ. The skeleton owns ABCWXYZ.
    return [0, [3, 4], [[1, method, mode, 2, 2, -1]],
            b"", 9, 0]


@pytest.mark.parametrize("method,mode", [
    (zipfile.ZIP_STORED, 0),
    (zipfile.ZIP_DEFLATED, 0),
    (zipfile.ZIP_DEFLATED, 1),
])
def test_skipped_physical_stream_uses_size_only(method, mode):
    calls = []
    def content(idx):
        calls.append(("content", idx))
        if idx == 0:
            return b"ABCWXYZ"
        raise AssertionError("skipped content must not be decoded")
    def stream(*args):
        raise AssertionError("skipped compressed stream must not be decoded")
    def physical_size(m, sm, rawref, streamref):
        calls.append(("size", m, sm, rawref, streamref))
        assert (m, sm, rawref, streamref) == (method, mode, 1, 2)
        return 2
    assert range_vzip(_recipe(method, mode), content, stream, 6, 2, physical_size) == b"XY"
    assert calls == [("content", 0), ("size", method, mode, 1, 2)]


@pytest.mark.parametrize("wrong_size", [0, 1, 3, 1024])
def test_skipped_physical_stream_size_mismatch_fails_closed(wrong_size):
    def content(idx):
        if idx == 0:
            return b"ABCWXYZ"
        raise AssertionError("should not need skipped content")
    with pytest.raises(IOError, match="selective reconstruction length mismatch"):
        range_vzip(_recipe(), content, lambda *args: b"pq", 6, 1,
                   lambda *args: wrong_size)


def test_no_work_after_early_or_empty_ranges():
    def content(idx):
        assert idx == 0
        return b"ABCWXYZ"
    def fail(*args):
        raise AssertionError("a prior stream witness must not run")
    assert range_vzip(_recipe(), content, fail, 0, 1, fail) == b"A"
    assert range_vzip(_recipe(), fail, fail, 2, 0, fail) == b""


def test_no_callback_uses_expensive_but_safe_standalone_control():
    calls = []
    def content(idx):
        calls.append(idx)
        return b"ABCWXYZ" if idx == 0 else b"pq"
    assert range_vzip(_recipe(), content, lambda *args: b"pq", 6, 2) == b"XY"
    assert calls == [0, 1]
