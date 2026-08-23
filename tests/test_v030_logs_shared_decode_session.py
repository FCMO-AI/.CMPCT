from __future__ import annotations

import gzip
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_logs_inverse_profile as P
from experiments import entropygraph_v030_logs_inverse_profile_v2 as V2


def _source(root: Path) -> bytes:
    root.mkdir()
    raw = (b"2026-08-22T14:00:00Z worker=7 event=cache-hit latency_us=31\n" * 8192)
    (root / "events.log").write_bytes(raw)
    (root / "events.log.gz").write_bytes(gzip.compress(raw, compresslevel=6, mtime=0))
    (root / "other.bin").write_bytes((b"ABCD" * 16384) + bytes(range(256)) * 64)
    return raw


def test_full_verify_decodes_each_authenticated_pack_at_most_once(tmp_path: Path):
    source = tmp_path / "source"
    _source(source)
    archive_path = tmp_path / "logs.cmpct"
    stats = V2.build(source, archive_path, allowed_inverse_codecs={"gzip", "zstd"})
    assert stats["edge_detection"]["inverse_edges"] >= 1

    with V2.Archive(archive_path) as archive:
        original = archive._read_pack
        calls: list[int] = []

        def counted(index: int):
            calls.append(index)
            return original(index)

        archive._read_pack = counted  # type: ignore[method-assign]
        verified = archive.verify_all()
        assert verified["ok"] is True
        assert len(calls) == len(set(calls))
        assert verified["full_operation_unique_packs_decoded"] == len(set(calls))
        assert verified["full_operation_unique_members_restored"] == len(archive.files)
        assert verified["max_member_read_amplification"] <= V2.MAX_MEMBER_AMPLIFICATION
        assert verified["max_decode_unit_bytes"] <= V2.MAX_DECODE_UNIT


def test_selective_read_keeps_cold_cache_operation_boundary(tmp_path: Path):
    source = tmp_path / "source"
    expected = _source(source)
    archive_path = tmp_path / "logs.cmpct"
    V2.build(source, archive_path, allowed_inverse_codecs={"gzip", "zstd"})

    with V2.Archive(archive_path) as archive:
        index = archive._paths().index("events.log")
        original = archive._read_pack
        calls: list[int] = []

        def counted(pack_index: int):
            calls.append(pack_index)
            return original(pack_index)

        archive._read_pack = counted  # type: ignore[method-assign]
        first, first_context = archive.read_member(index)
        first_calls = len(calls)
        second, second_context = archive.read_member(index)
        second_calls = len(calls) - first_calls

        assert first == expected == second
        assert first_context == second_context
        assert first_context / len(expected) <= V2.MAX_MEMBER_AMPLIFICATION
        # Each public read starts with a fresh dependency/pack cache. The archive-wide optimization therefore
        # cannot make the selective-read locality benchmark accidentally warm-cache itself.
        assert first_calls >= 1
        assert second_calls == first_calls


def test_full_extract_restores_exact_files_with_shared_session(tmp_path: Path):
    source = tmp_path / "source"
    _source(source)
    archive_path = tmp_path / "logs.cmpct"
    V2.build(source, archive_path, allowed_inverse_codecs={"gzip", "zstd"})
    output = tmp_path / "out"
    V2.extract(archive_path, output)
    assert {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file()
    } == {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }


def test_full_extract_does_not_repeat_filesystem_resolution_for_authenticated_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source = tmp_path / "source"
    _source(source)
    archive_path = tmp_path / "logs.cmpct"
    V2.build(source, archive_path, allowed_inverse_codecs={"gzip", "zstd"})
    output = tmp_path / "out"

    def forbidden_resolve(*_args, **_kwargs):
        raise AssertionError("authenticated logs extraction must not resolve every destination path")

    # Archive metadata has already passed the bounded lexical path parser before ``Archive.extract`` runs.
    # The hot extraction loop must therefore join those authenticated POSIX components directly rather than
    # triggering one or more filesystem traversals for every member.
    monkeypatch.setattr(Path, "resolve", forbidden_resolve)
    V2.extract(archive_path, output)
    assert (output / "events.log").read_bytes().startswith(b"2026-08-22T14:00:00Z")


def test_metadata_parser_remains_fail_closed_for_parent_traversal():
    unsafe = msgpack.packb(
        [
            P.PROFILE,
            P.LEVEL,
            [[0, "../escape", 1, b"x" * 32, ["raw", 0, 0, 1]]],
        ],
        use_bin_type=True,
    )
    archive = object.__new__(V2.Archive)
    with pytest.raises(RuntimeError, match="unsafe logs profile path"):
        archive._parse_meta(unsafe)
