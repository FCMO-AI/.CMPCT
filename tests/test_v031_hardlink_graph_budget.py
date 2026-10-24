"""Real signed-r24 O1 hardlink-chain preflight correctness controls.

Predicted negative on unmodified #339: an indirect missing terminal may raise
KeyError instead of ValidationError, despite authenticated index bytes.
"""
from __future__ import annotations

from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_DIR, K_FILE, K_HARDLINK, K_SYMLINK, MAGIC, S_BLOB, sha, zc, zd
from cmpct.validation import ValidationError, preflight_archive


def _source(tmp_path: Path) -> Path:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a00000000.bin").write_bytes(b"ONE-REAL-OWNER")
    archive = tmp_path / "source.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    return archive


def _signed_mutation(source: Path, target: Path, rows_factory) -> None:
    wire = source.read_bytes()
    magic, version, flags, csize, usize, dsize, digest = HDR.unpack_from(wire)
    assert magic == MAGIC and version == 24
    plain = zd(wire[HDR.size:HDR.size + csize], usize)
    assert sha(plain) == digest
    index = msgpack.unpackb(plain, raw=False)
    assert len(index["files"]) == 1
    owner = index["files"][0]
    assert owner[0] == "a00000000.bin" and owner[1] == K_FILE
    index["files"] = rows_factory(owner)
    decoded = msgpack.packb(index, use_bin_type=True)
    compressed = zc(decoded, 12)
    physical = wire[HDR.size + csize:HDR.size + csize + dsize]
    assert len(physical) == dsize
    new_digest = sha(decoded)
    target.write_bytes(
        HDR.pack(MAGIC, version, flags, len(compressed), len(decoded), dsize, new_digest)
        + compressed + physical + compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(decoded), 0, new_digest)
    )
    after = target.read_bytes()
    assert after[HDR.size + len(compressed):HDR.size + len(compressed) + dsize] == physical
    assert after[HDR.size:HDR.size + len(compressed)] == after[-FTR.size - len(compressed):-FTR.size]


def _alias(owner, name: str, target: str):
    return [name, K_HARDLINK, owner[2], owner[3], owner[4], None, [target]]


@pytest.mark.parametrize("shape,reverse", [
    ("chain", False), ("chain", True), ("star", False), ("star", True),
])
def test_signed_valid_deep_alias_graphs_are_accepted(tmp_path: Path, shape: str, reverse: bool) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "valid.cmpct"
    n = 1024

    def rows(owner):
        result = [owner]
        prev = owner[0]
        for i in range(n):
            name = f"z{i:08d}.bin"
            result.append(_alias(owner, name, prev if shape == "chain" else owner[0]))
            prev = name
        return list(reversed(result)) if reverse else result

    _signed_mutation(source, archive, rows)
    assert preflight_archive(archive)["files"] == n + 1


@pytest.mark.parametrize("shape", [
    "self_cycle", "two_cycle", "direct_missing", "indirect_missing",
    "directory_terminal", "symlink_terminal",
])
def test_signed_invalid_alias_graphs_rejected_as_validation_error(tmp_path: Path, shape: str) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "invalid.cmpct"

    def rows(owner):
        a, b = "z00000000.bin", "z00000001.bin"
        result = [owner]
        if shape == "self_cycle":
            result.append(_alias(owner, a, a))
        elif shape == "two_cycle":
            result.extend([_alias(owner, a, b), _alias(owner, b, a)])
        elif shape == "direct_missing":
            result.append(_alias(owner, a, "missing-owner"))
        elif shape == "indirect_missing":
            result.extend([_alias(owner, a, b), _alias(owner, b, "missing-owner")])
        elif shape == "directory_terminal":
            result.extend([
                ["z_directory", K_DIR, owner[2], owner[3], 0, b"", None],
                _alias(owner, a, "z_directory"),
            ])
        elif shape == "symlink_terminal":
            # Exact physical content is deliberately not decoded by structural preflight.
            result.extend([
                ["z_symlink", K_SYMLINK, owner[2], owner[3], owner[4], None, [S_BLOB, 0]],
                _alias(owner, a, "z_symlink"),
            ])
        else:
            raise AssertionError(shape)
        return result

    _signed_mutation(source, archive, rows)
    # A malformed index must be refused with the documented parser error
    # class, not leak a Python KeyError from an intermediate alias walk.
    with pytest.raises(ValidationError):
        preflight_archive(archive)
