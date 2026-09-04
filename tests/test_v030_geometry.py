from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_geometry as geometry


def test_delimiter_transform_has_hand_derived_golden_vector() -> None:
    raw = b"aa,bb,cc"
    transformed = geometry.delimiter_forward(raw, ord(","))
    # Footnote: three 2-byte segments become two segment columns: a/b/c then a/b/c.  This byte vector
    # is derived independently of the inverse implementation, so writer/reader agreement is not the oracle.
    assert transformed == b"DGT1,\x03\x02\x02\x02abcabc"
    assert geometry.delimiter_inverse(transformed, len(raw)) == raw


def test_delimiter_transform_preserves_empty_segments_and_trailing_separator() -> None:
    raw = b",alpha,,beta,"
    transformed = geometry.delimiter_forward(raw, ord(","))
    assert geometry.delimiter_inverse(transformed, len(raw)) == raw


def test_delimiter_inverse_rejects_resource_bomb() -> None:
    prefix = bytearray(b"DGT1,")
    geometry._put_varint(prefix, geometry.MAX_DELIMITER_SEGMENTS + 1)
    with pytest.raises(RuntimeError, match="segment count"):
        geometry.delimiter_inverse(bytes(prefix), 0)


def test_regular_gap_discovery_is_content_driven() -> None:
    # The chosen separator is not a file-type rule: use a non-text control byte with regular spacing.
    raw = (b"abcdef" + b"\x1e") * 4000
    assert 0x1E in geometry._delimiter_rank(raw)


def test_regular_gap_discovery_is_invariant_to_censored_edge_phase() -> None:
    cycle = b"abcdef"
    for phase in range(len(cycle) + 1):
        raw = cycle[phase:] + b"\x1e" + (cycle + b"\x1e") * 3998 + cycle[:phase]
        assert 0x1E in geometry._delimiter_rank(raw), f"separator lost at edge phase {phase}"

    # Footnote: the first/last fragments are incomplete observations of the recurrence period. Varying their
    # phase must not change the score of the complete delimiter-to-delimiter intervals in the bounded sample.


def test_geometry_archive_round_trips_generic_delimited_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"; source.mkdir()
    rows = [f"key={i:06d},tenant={i % 37:02d},status=active,value={(i * 13) % 997:03d}" for i in range(14000)]
    # Deliberately misleading extension: transform admission must come from bytes, not a semantic suffix.
    (source / "opaque.bin").write_bytes("\n".join(rows).encode())
    (source / "noise.bin").write_bytes(bytes((i * 73 + 19) & 255 for i in range(90_000)))

    archive = tmp_path / "geometry.cmpct"
    stats = geometry._build_geometry(source, archive)
    assert stats["delimiter_nodes"] > 0
    assert stats["transform_payload_saving_bytes"] > 0
    assert stats["max_read_amplification"] == 1.0

    verified = geometry.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == geometry.treehash(source)
    restored = tmp_path / "restored"
    geometry.extract(archive, restored)
    assert geometry.treehash(restored) == geometry.treehash(source)


def test_geometry_path_policy_rejects_traversal() -> None:
    for unsafe in ("../escape", "/absolute", "a/../escape", "a\\escape", ""):
        with pytest.raises(RuntimeError):
            geometry._safe_relpath(unsafe)
