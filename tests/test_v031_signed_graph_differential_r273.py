"""Independent held-out signed-r24 hardlink graph differential court (R273).

A slow reference follows each alias independently. The actual product parses a
physically authentic Builder archive whose logical rows are altered and re-signed.
This does not share the optimized owner's graph-resolution code.
"""
from __future__ import annotations

import random
from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_FILE, K_HARDLINK, MAGIC, sha, zc, zd
from cmpct.validation import ValidationError, preflight_archive


def _signed_aliases(wire: bytes, target: Path, edges: dict[str, str]) -> None:
    magic, revision, flags, csize, usize, dsize, digest = HDR.unpack_from(wire)
    assert magic == MAGIC and revision == 24
    plain = zd(wire[HDR.size:HDR.size + csize], usize)
    assert sha(plain) == digest
    original = msgpack.unpackb(plain, raw=False)
    assert len(original["files"]) == 1
    owner = original["files"][0]
    assert owner[1] == K_FILE and owner[0] == "owner.bin"
    original["files"] = [owner] + [
        [alias, K_HARDLINK, owner[2], owner[3], owner[4], None, [destination]]
        for alias, destination in edges.items()
    ]
    # Intentionally challenge both lexical-row orders without changing the
    # underlying physical blob or either authenticated index copy.
    original["files"].sort(key=lambda row: row[0], reverse=(len(edges) % 2 == 1))
    index = msgpack.packb(original, use_bin_type=True)
    compressed = zc(index, 12)
    physical = wire[HDR.size + csize:HDR.size + csize + dsize]
    commitment = sha(index)
    target.write_bytes(
        HDR.pack(MAGIC, revision, flags, len(compressed), len(index), dsize, commitment)
        + compressed + physical + compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(index), 0, commitment)
    )
    restored = target.read_bytes()
    assert restored[HDR.size + len(compressed):HDR.size + len(compressed) + dsize] == physical
    assert restored[HDR.size:HDR.size + len(compressed)] == restored[-FTR.size - len(compressed):-FTR.size]


def _reference_admissible(edges: dict[str, str]) -> bool:
    """Deliberately O(N^2) oracle: prove every alias has a real terminal owner."""
    for alias in edges:
        visited = set()
        current = alias
        while current in edges:
            if current in visited:
                return False
            visited.add(current)
            current = edges[current]
        if current != "owner.bin":
            return False
    return True


def test_signed_hardlink_graph_follows_independent_reference(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "owner.bin").write_bytes(b"OWNER-R273-EXACT")
    source = tmp_path / "base.cmpct"
    Builder(root, workers=1, reproducible=True).build(source)
    wire = source.read_bytes()
    rng = random.Random(0x273A11)
    actual_positive = actual_negative = 0
    for case in range(72):
        size = 2 + (case % 17)
        aliases = [f"alias{i:04d}.bin" for i in range(size)]
        if case == 0:
            edges = {name: "owner.bin" for name in aliases}  # star
        elif case == 1:
            edges = {name: (aliases[i - 1] if i else "owner.bin") for i, name in enumerate(aliases)}  # chain
        else:
            targets = ["owner.bin", "missing.bin", *aliases]
            edges = {name: rng.choice(targets) for name in aliases}
        expected = _reference_admissible(edges)
        archive = tmp_path / f"signed-{case:02d}.cmpct"
        _signed_aliases(wire, archive, edges)
        if expected:
            assert preflight_archive(archive)["files"] == len(edges) + 1
            actual_positive += 1
        else:
            with pytest.raises(ValidationError):
                preflight_archive(archive)
            actual_negative += 1
    assert actual_positive >= 2 and actual_negative >= 30
