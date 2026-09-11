from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from experiments.one.authenticated_archive_envelope import build_authenticated_archive, open_authenticated_archive
from experiments.one.general_law_archive import SAMPLE_POINTS, _sample_positions, build_general_law_archive


def _pattern(n: int, seed: int = 0) -> bytes:
    return bytes(((index * 73 + (index >> 3) * 19 + seed) & 0xFF) for index in range(n))


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


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
    size = 32 * 1024

    # Keep ADD8 and XOR on independent Surprise-seeded relation islands. This exercises
    # both Law classes while ensuring the product seam only emits topology the promoted
    # authenticated selective reader can lower cone-proportionally.
    base_a = _hash_stream(size, b"general-law-base-a")
    add_a = bytes(((b + 37) & 0xFF) for b in base_a)
    base_b = _hash_stream(size, b"general-law-base-b")
    xor_b = bytes((b ^ 0xA5) for b in base_b)
    (root / "00-base-a.bin").write_bytes(base_a)
    (root / "01-add8-a.bin").write_bytes(add_a)
    (root / "02-base-b.bin").write_bytes(base_b)
    (root / "03-xor-b.bin").write_bytes(xor_b)
    (root / "04-copy-xor.bin").write_bytes(xor_b)
    (root / "05-fill.bin").write_bytes(b"Z" * size)
    (root / "06-noise.bin").write_bytes(_hash_stream(size, b"general-law-noise"))
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


def test_relation_after_law_is_pruned_to_surprise_to_preserve_selective_boundary(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    size = 32 * 1024
    base = _hash_stream(size, b"nested-law-source")
    add = bytes(((b + 37) & 0xFF) for b in base)
    would_be_nested_xor = bytes((b ^ 0xA5) for b in add)
    (root / "00-base.bin").write_bytes(base)
    (root / "01-add8.bin").write_bytes(add)
    (root / "02-nested-xor-opportunity.bin").write_bytes(would_be_nested_xor)

    wire, stats = build_general_law_archive(root)
    opened = open_authenticated_archive(wire)

    assert stats.add8_roots == 1
    assert stats.xor_roots == 0
    assert stats.surprise_roots == 2
    # Third regular root must be a direct Surprise rather than a Law wrapped around Law.
    third_entry = opened.base.entries["02-nested-xor-opportunity.bin"]
    third_root = opened.program.roots[third_entry["root"]]
    assert opened.program.nodes[third_root.ref.node].op == "surprise"
    _roundtrip_all(root, wire)


def test_unrelated_hash_streams_are_cheaply_rejected_without_exact_relation_scan(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    size = 64 * 1024
    (root / "a.bin").write_bytes(_hash_stream(size, b"a"))
    (root / "b.bin").write_bytes(_hash_stream(size, b"b"))

    wire, stats = build_general_law_archive(root)
    assert stats.exact_reuse_roots == 0
    assert stats.fill_roots == 0
    assert stats.add8_roots == 0
    assert stats.xor_roots == 0
    assert stats.surprise_roots == 2
    assert stats.discovery_exact_proof_bytes == 0
    # First file: 16 fill samples. Second: 16 fill + 32 ADD8 + 32 XOR bytes.
    assert stats.discovery_sample_bytes == SAMPLE_POINTS * 6
    _roundtrip_all(root, wire)


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


def test_surprise_only_fallback_has_no_wire_tax_against_authenticated_archive_seam(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.bin").write_bytes(_hash_stream(48 * 1024, b"left"))
    (root / "b.bin").write_bytes(_hash_stream(47 * 1024, b"right"))

    law_wire, stats = build_general_law_archive(root)
    surprise_wire, _ = build_authenticated_archive(root)
    assert stats.surprise_roots == 2
    assert stats.exact_reuse_roots == stats.fill_roots == stats.add8_roots == stats.xor_roots == 0
    assert law_wire == surprise_wire


def test_safe_relative_symlink_semantics_match_existing_archive_reader(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "target.txt").write_bytes(b"target")
    link = root / "alias.txt"
    try:
        link.symlink_to("target.txt")
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    wire, stats = build_general_law_archive(root)
    opened = open_authenticated_archive(wire)
    assert stats.symlinks == 1
    assert opened.base.entries["alias.txt"]["kind"] == "symlink"
    assert opened.base.entries["alias.txt"]["target"] == "target.txt"
    assert opened.read_file("target.txt") == b"target"


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