from __future__ import annotations

from pathlib import Path

import pytest

from experiments.one.authenticated_archive_envelope import build_authenticated_archive, open_authenticated_archive
from experiments.one.general_law_archive import SAMPLE_POINTS, _sample_positions, build_general_law_archive


def _pattern(n: int, seed: int = 0) -> bytes:
    return bytes(((index * 73 + (index >> 3) * 19 + seed) & 0xFF) for index in range(n))


def _roundtrip_all(root: Path, wire: bytes) -> None:
    opened = open_authenticated_archive(wire)
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(root).as_posix()
        expected = path.read_bytes()
        assert opened.read_file(rel) == expected
        if expected:
            start = min(7, len(expected) - 1)
            length = min(4096, len(expected) - start)
            actual, stats = opened.read_range(rel, start, length)
            assert actual == expected[start : start + length]
            assert stats.fallback is False
            assert stats.proof_payload_bytes >= length
            assert stats.verify_cpu_ns >= 0


def test_general_tree_uses_laws_and_surprise_without_changing_reader_ontology(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    base = _pattern(32 * 1024, 11)
    (root / "00-base.bin").write_bytes(base)
    (root / "01-copy.bin").write_bytes(base)
    (root / "02-add8.bin").write_bytes(bytes(((b + 37) & 0xFF) for b in base))
    xor_source = (root / "02-add8.bin").read_bytes()
    (root / "03-xor.bin").write_bytes(bytes((b ^ 0xA5) for b in xor_source))
    (root / "04-fill.bin").write_bytes(b"Z" * (32 * 1024))
    (root / "05-noise.bin").write_bytes(_pattern(32 * 1024, 97))
    (root / "nested").mkdir()
    (root / "nested" / "tiny.txt").write_bytes(b"tiny")
    (root / "empty").write_bytes(b"")

    wire, stats = build_general_law_archive(root)
    _roundtrip_all(root, wire)
    opened = open_authenticated_archive(wire)

    assert stats.exact_reuse_roots >= 1
    assert stats.add8_roots >= 1
    assert stats.xor_roots >= 1
    assert stats.fill_roots >= 1
    assert stats.surprise_roots >= 1
    assert stats.authentication_source_reread_bytes == 0
    assert stats.source_read_bytes == stats.logical_file_bytes
    assert stats.max_predictor_bytes <= max(p.stat().st_size for p in root.rglob("*") if p.is_file())
    assert {node.op for node in opened.program.nodes} <= {"surprise", "concat", "repeat", "fill", "xor", "add8"}


def test_identical_tree_build_is_byte_deterministic(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    first = _pattern(12 * 1024, 5)
    (root / "a").write_bytes(first)
    (root / "b").write_bytes(bytes(((b + 3) & 0xFF) for b in first))
    (root / "c").write_bytes(_pattern(9000, 91))

    wire_a, stats_a = build_general_law_archive(root)
    wire_b, stats_b = build_general_law_archive(root)
    assert wire_a == wire_b
    assert stats_a == stats_b


def test_false_add8_sample_is_exact_proofed_then_falls_back(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    source = _pattern(4097, 17)
    target = bytearray(((b + 7) & 0xFF) for b in source)
    sampled = set(_sample_positions(len(source)))
    adversary = next(index for index in range(len(source)) if index not in sampled)
    target[adversary] ^= 0x01
    (root / "a.bin").write_bytes(source)
    (root / "b.bin").write_bytes(bytes(target))

    wire, stats = build_general_law_archive(root)
    assert stats.add8_roots == 0
    assert stats.discovery_exact_proof_bytes >= len(source) * 2
    _roundtrip_all(root, wire)


def test_law_bearing_complete_archive_beats_same_authenticated_surprise_seam_on_exact_copy(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    payload = _pattern(128 * 1024, 29)
    (root / "a.bin").write_bytes(payload)
    (root / "b.bin").write_bytes(payload)

    law_wire, law_stats = build_general_law_archive(root)
    surprise_wire, surprise_stats = build_authenticated_archive(root)
    assert law_stats.exact_reuse_roots == 1
    assert len(law_wire) < len(surprise_wire)
    assert law_stats.wire_bytes == len(law_wire)
    assert surprise_stats.wire_bytes == len(surprise_wire)
    _roundtrip_all(root, law_wire)


def test_sample_gate_is_fixed_size_for_large_inputs():
    positions = _sample_positions(10_000_000)
    assert len(positions) == SAMPLE_POINTS
    assert positions[0] == 0
    assert positions[-1] == 9_999_999


def test_non_directory_source_fails_closed(tmp_path: Path):
    source = tmp_path / "file"
    source.write_bytes(b"x")
    with pytest.raises(Exception, match="archive source must be a directory"):
        build_general_law_archive(source)
