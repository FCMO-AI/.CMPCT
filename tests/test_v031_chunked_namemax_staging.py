"""POSIX NAME_MAX regression: verified staging must not extend a valid member basename.

Filesystem component limits are in encoded bytes, not Python code points. A
perfectly valid archive member may already occupy the entire NAME_MAX budget.
The temporary stage component must be independently short before os.replace.
"""
from __future__ import annotations

import hashlib
import os
import random
import sys

import pytest

from cmpct.builder import Builder
from cmpct.codec import S_CDC
from cmpct.reader import CMPCT


@pytest.mark.skipif(os.name != "posix", reason="POSIX NAME_MAX filesystem court")
@pytest.mark.parametrize("member", [
    "n" * 230 + ".bin",  # 234 encoded bytes: inherited control that already passed.
    "n" * 231 + ".bin",  # 235 bytes: first rejected by old stage name.
    "n" * 251 + ".bin",  # 255-byte POSIX boundary.
    pytest.param("é" * 125 + ".bin", marks=pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="raw UTF-8 POSIX component court")),
])
def test_verified_chunked_extract_accepts_max_length_component(tmp_path, member):
    component_bytes = len(os.fsencode(member))
    try:
        max_component = os.pathconf(tmp_path, "PC_NAME_MAX")
    except (OSError, ValueError):
        pytest.skip("filesystem does not expose PC_NAME_MAX")
    if max_component < component_bytes:
        pytest.skip("filesystem cannot admit this source component")

    assert component_bytes in (234, 235, 254, 255)
    source_tree = tmp_path / "source"
    source_tree.mkdir()
    original = random.Random(0xC0FFEE).randbytes(4 * 256 * 1024 + 8192)
    (source_tree / member).write_bytes(original)

    archive = tmp_path / "source.cmpct"
    Builder(source_tree, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.by[member][6][0] == S_CDC, "court must exercise streaming extraction"
        destination = tmp_path / "out"
        reader.extractall(destination, metadata=False)

    restored = (destination / member).read_bytes()
    assert hashlib.sha256(restored).digest() == hashlib.sha256(original).digest()
    assert len(restored) == len(original)
    assert not list(destination.glob(".cmpct-part-*"))
