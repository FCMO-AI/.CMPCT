from __future__ import annotations

import base64
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from experiments.one.archive_envelope import CHUNK_BYTES, MANIFEST_ROOT
from experiments.one.authenticated_archive_envelope import (
    AUTH_FIELD,
    AUTH_LEAF_BYTES,
    build_authenticated_archive,
    open_authenticated_archive,
)
from experiments.one.ir import Node, OneError, Program, Root
from experiments.one.wire import decode_program, encode_program


def _fixture(root: Path) -> dict[str, bytes]:
    (root / "empty-dir").mkdir()
    (root / "empty.bin").write_bytes(b"")
    (root / "small.bin").write_bytes(bytes(range(251)))
    (root / "one-leaf.bin").write_bytes(bytes((i * 17 + 3) & 255 for i in range(AUTH_LEAF_BYTES)))
    large = bytes((i * 37 + (i >> 8) * 11 + 19) & 255 for i in range(CHUNK_BYTES + AUTH_LEAF_BYTES * 3 + 137))
    (root / "large.bin").write_bytes(large)
    (root / "duplicate.bin").write_bytes((root / "small.bin").read_bytes())
    try:
        os.symlink("small.bin", root / "link")
    except (OSError, NotImplementedError):
        pass
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def test_authenticated_archive_reopens_and_reads_only_requested_cones(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    original = _fixture(src)
    wire, build = build_authenticated_archive(src)
    archive = open_authenticated_archive(wire)

    assert build.source_reread_bytes == sum(map(len, original.values()))
    assert build.auth_manifest_delta_bytes > 0
    assert build.raw_auth_index_bytes > 0

    for path, expected in original.items():
        assert archive.read_file(path) == expected

    requests = [
        ("small.bin", 0, 64),
        ("one-leaf.bin", AUTH_LEAF_BYTES - 73, 73),
        ("large.bin", AUTH_LEAF_BYTES - 31, 127),
        ("large.bin", CHUNK_BYTES - 31, 127),
        ("large.bin", len(original["large.bin"]) - 257, 257),
        ("empty.bin", 0, 0),
    ]
    for path, start, length in requests:
        got, stats = archive.read_range(path, start, length)
        assert got == original[path][start:start + length]
        assert stats.requested_bytes == length
        if length:
            assert stats.cone_bytes <= max(AUTH_LEAF_BYTES * 2, length + AUTH_LEAF_BYTES * 2)
            assert stats.cone_bytes < len(original[path]) or len(original[path]) <= AUTH_LEAF_BYTES

    # The >1 MiB cross-chunk request must not reconstruct the whole file.
    _, stats = archive.read_range("large.bin", CHUNK_BYTES - 31, 127)
    assert stats.cone_bytes == AUTH_LEAF_BYTES * 2
    assert stats.source_read_bytes == AUTH_LEAF_BYTES * 2
    assert stats.proof_payload_bytes == AUTH_LEAF_BYTES * 2

    if "link" in archive.list_paths():
        assert archive.base.entries["link"]["target"] == "small.bin"


def _mutate_manifest(wire: bytes, mutate) -> bytes:
    program = decode_program(wire)
    manifest_id = program.roots[MANIFEST_ROOT].ref.node
    document = json.loads(program.nodes[manifest_id].surprise)
    mutate(document)
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    nodes = list(program.nodes)
    nodes[manifest_id] = Node("surprise", surprise=raw, declared_length=len(raw))
    roots = dict(program.roots)
    roots[MANIFEST_ROOT] = Root(roots[MANIFEST_ROOT].ref, len(raw), sha256(raw).hexdigest())
    delta = len(raw) - program.roots[MANIFEST_ROOT].length
    limits = replace(
        program.limits,
        max_output_bytes=program.limits.max_output_bytes + max(0, delta),
        max_work_bytes=program.limits.max_work_bytes + max(0, delta) * 6,
    )
    malformed = Program(tuple(nodes), roots, limits)
    return encode_program(malformed)[0]


def _first_file(document: dict) -> dict:
    return next(entry for entry in document["entries"] if entry["kind"] == "file" and entry["size"] > AUTH_LEAF_BYTES)


def test_bad_auth_root_fails_closed_at_open(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); _fixture(src)
    wire, _ = build_authenticated_archive(src)

    def mutate(document):
        entry = _first_file(document)
        entry[AUTH_FIELD]["root"] = "00" * 32

    with pytest.raises(OneError, match="root commitment mismatch"):
        open_authenticated_archive(_mutate_manifest(wire, mutate))


def test_malformed_auth_base64_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); _fixture(src)
    wire, _ = build_authenticated_archive(src)

    def mutate(document):
        entry = _first_file(document)
        entry[AUTH_FIELD]["levels_b64"][0] = "%%%not-base64%%%"

    with pytest.raises(OneError, match="level encoding invalid"):
        open_authenticated_archive(_mutate_manifest(wire, mutate))


def test_wrong_auth_level_width_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); _fixture(src)
    wire, _ = build_authenticated_archive(src)

    def mutate(document):
        entry = _first_file(document)
        raw = base64.b64decode(entry[AUTH_FIELD]["levels_b64"][0])
        entry[AUTH_FIELD]["levels_b64"][0] = base64.b64encode(raw[:-32]).decode()

    with pytest.raises(OneError, match="level width invalid"):
        open_authenticated_archive(_mutate_manifest(wire, mutate))


def test_internally_inconsistent_auth_tree_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); _fixture(src)
    wire, _ = build_authenticated_archive(src)

    def mutate(document):
        entry = _first_file(document)
        level = bytearray(base64.b64decode(entry[AUTH_FIELD]["levels_b64"][0]))
        level[0] ^= 1
        entry[AUTH_FIELD]["levels_b64"][0] = base64.b64encode(level).decode()

    with pytest.raises(OneError, match="tree inconsistent"):
        open_authenticated_archive(_mutate_manifest(wire, mutate))


def test_missing_auth_metadata_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); _fixture(src)
    wire, _ = build_authenticated_archive(src)

    def mutate(document):
        _first_file(document).pop(AUTH_FIELD)

    with pytest.raises(OneError, match="metadata missing"):
        open_authenticated_archive(_mutate_manifest(wire, mutate))


def test_out_of_range_request_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); _fixture(src)
    wire, _ = build_authenticated_archive(src)
    archive = open_authenticated_archive(wire)
    with pytest.raises(OneError):
        archive.read_range("small.bin", 200, 1000)
