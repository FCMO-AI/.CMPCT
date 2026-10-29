"""J24G55: real Builder + 64 committed deletions + checkpoint identity gate.

Unlike the cheap abstract 64-generation state model this checks actual r24
footers, signed fsmeta, and native xattr fidelity across the checkpoint.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from cmpct.validation import preflight_archive, _load_effective_index, ParserLimits

KEY = "com.fcmo.cmpct.j24g55-ckpt" if sys.platform == "darwin" else "user.cmpct_j24g55_ckpt"
A, Z = "a-owner.bin", "z-owner.bin"
EXPECTED = {A: b"checkpoint-A\x00\xfe", Z: b"checkpoint-Z\x00\xff"}


def _set(path: Path, value: bytes):
    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/xattr", "-wx", KEY, value.hex(), str(path)],
                       check=True, capture_output=True, text=True)
    else:
        os.setxattr(path, KEY, value, follow_symlinks=False)


def _get(path: Path):
    if sys.platform == "darwin":
        out = subprocess.run(["/usr/bin/xattr", "-px", KEY, str(path)],
                             check=True, capture_output=True, text=True)
        return bytes.fromhex("".join(out.stdout.split()))
    return os.getxattr(path, KEY, follow_symlinks=False)


def _mapped(index: dict):
    return {
        index["files"][ordinal][0]: {
            str(k): bytes(v) for k, v in pairs}
        for ordinal, pairs in index.get("fsmeta", {}).get("xattrs", [])
    }


def _judge(archive: Path, expected_files: int, expected_depth: int):
    preflight = preflight_archive(archive)
    assert preflight["files"] == expected_files
    with archive.open("rb") as stream:
        logical, _, footer, depth = _load_effective_index(
            stream, os.fstat(stream.fileno()).st_size, ParserLimits())
    assert footer and depth == expected_depth
    with CMPCT(archive) as reader:
        assert len(reader.files) == expected_files
        assert reader.delta_depth == expected_depth
        assert reader.verify() == expected_files
        assert reader.index == logical
        assert _mapped(logical) == _mapped(reader.index)
        assert set(_mapped(logical)) == {A, Z}
        for name, value in EXPECTED.items():
            assert _mapped(logical)[name][KEY] == value


@pytest.mark.skipif(sys.platform not in ("linux", "darwin"), reason="native POSIX xattr checkpoint")
def test_real_64th_delete_writes_identity_preserving_checkpoint(tmp_path: Path):
    tree = tmp_path / "tree"
    tree.mkdir()
    for name in (A, Z):
        (tree / name).write_bytes((name.encode() + b"\x00") * 7)
        _set(tree / name, EXPECTED[name])
        assert _get(tree / name) == EXPECTED[name]
    intermediates = [f"m{i:02d}.bin" for i in range(64)]
    for i, name in enumerate(intermediates):
        (tree / name).write_bytes(f"removable-{i}".encode())
    archive = tmp_path / "checkpoint.cmpct"
    Builder(tree, workers=1, reproducible=False).build(archive)
    _judge(archive, 66, 0)
    # All 64 operations are authentic signed generations. A checkpoint at the
    # 64th write must not resurrect the ordinals from the deleted members.
    for name in intermediates[:63]:
        append_delete(archive, name)
    _judge(archive, 3, 63)
    append_delete(archive, intermediates[63])
    _judge(archive, 2, 0)
    with CMPCT(archive) as reader:
        restored = tmp_path / "restored"
        reader.extractall(restored, metadata=True, require_xattrs=True)
    for name, value in EXPECTED.items():
        assert _get(restored / name) == value
        assert (restored / name).read_bytes() == (tree / name).read_bytes()
    assert sorted(path.name for path in restored.iterdir()) == [A, Z]
