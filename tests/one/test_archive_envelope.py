from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import os

import pytest

from experiments.one.archive_envelope import (
    CHUNK_BYTES,
    MANIFEST_ROOT,
    build_archive,
    build_program,
    open_archive,
)
from experiments.one.ir import Node, OneError, Program, Root
from experiments.one.wire import encode_program


def _tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def _fixture(root: Path) -> dict[str, bytes]:
    (root / "empty-dir").mkdir(parents=True)
    (root / "nested").mkdir()
    (root / "empty.bin").write_bytes(b"")
    (root / "nested" / "small.txt").write_bytes(b"ONE archive seam\n" * 23)
    large = bytes((i * 37 + 11) & 255 for i in range(CHUNK_BYTES + 8193))
    (root / "large.bin").write_bytes(large)
    (root / "duplicate.bin").write_bytes((root / "nested" / "small.txt").read_bytes())
    try:
        os.symlink("nested/small.txt", root / "link")
    except (OSError, NotImplementedError):
        pass
    return _tree(root)


def test_surprise_archive_roundtrip_deterministic_and_selective(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    original = _fixture(src)

    wire_a, stats_a = build_archive(src)
    wire_b, stats_b = build_archive(src)
    assert wire_a == wire_b
    assert stats_a == stats_b
    assert stats_a.logical_file_bytes == sum(map(len, original.values()))
    assert stats_a.wire_bytes > stats_a.logical_file_bytes  # honest fallback/control overhead

    archive = open_archive(wire_a)
    for path, expected in original.items():
        assert archive.read_file(path) == expected

    start, length = CHUNK_BYTES - 31, 127
    got, stats = archive.read_range("large.bin", start, length)
    assert got == original["large.bin"][start : start + length]
    assert stats.requested_bytes == length
    assert stats.materialized_bytes <= length * 3
    assert stats.nodes_touched <= 3
    assert stats.authenticated is False  # do not borrow selective-auth evidence into this seam

    paths = archive.list_paths()
    assert "empty-dir" in paths
    if "link" in paths:
        assert archive.entries["link"]["target"] == "nested/small.txt"


def test_duplicate_contents_remain_independent_surprise_fallback(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    payload = b"same" * 4096
    (src / "a.bin").write_bytes(payload)
    (src / "b.bin").write_bytes(payload)
    program, _ = build_program(src)
    file_entries = [e for e in json.loads(program.nodes[-1].surprise)["entries"] if e["kind"] == "file"]
    assert len(file_entries) == 2
    assert file_entries[0]["root"] != file_entries[1]["root"]
    # The fallback does not smuggle dedup in as another storage mode.
    assert sum(len(n.surprise) for n in program.nodes[:-1]) == len(payload) * 2


def test_unsafe_symlink_escape_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    try:
        os.symlink("../../outside", src / "escape")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(OneError, match="escapes archive root"):
        build_archive(src)


def _replace_manifest(program: Program, document: dict) -> Program:
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    manifest_id = program.roots[MANIFEST_ROOT].ref.node
    nodes = list(program.nodes)
    nodes[manifest_id] = Node("surprise", surprise=raw, declared_length=len(raw))
    roots = dict(program.roots)
    roots[MANIFEST_ROOT] = Root(program.roots[MANIFEST_ROOT].ref, len(raw), sha256(raw).hexdigest())
    return Program(nodes=tuple(nodes), roots=roots, limits=replace(program.limits, max_output_bytes=program.limits.max_output_bytes + len(raw) + 1024, max_work_bytes=program.limits.max_work_bytes + len(raw) * 8 + 8192))


def test_missing_file_root_in_manifest_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a").write_bytes(b"abc")
    program, _ = build_program(src)
    document = json.loads(program.nodes[program.roots[MANIFEST_ROOT].ref.node].surprise)
    file_entry = next(e for e in document["entries"] if e["kind"] == "file")
    file_entry["root"] = "missing"
    malformed = _replace_manifest(program, document)
    wire, _ = encode_program(malformed)
    with pytest.raises(OneError, match="missing file root"):
        open_archive(wire)


def test_manifest_length_or_digest_disagreement_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a").write_bytes(b"abc")
    program, _ = build_program(src)
    document = json.loads(program.nodes[program.roots[MANIFEST_ROOT].ref.node].surprise)
    file_entry = next(e for e in document["entries"] if e["kind"] == "file")
    file_entry["size"] += 1
    malformed = _replace_manifest(program, document)
    wire, _ = encode_program(malformed)
    with pytest.raises(OneError, match="length mismatch"):
        open_archive(wire)


def test_special_file_fails_closed_when_available(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO unavailable")
    src = tmp_path / "src"
    src.mkdir()
    os.mkfifo(src / "pipe")
    with pytest.raises(OneError, match="unsupported archive entry kind"):
        build_program(src)
