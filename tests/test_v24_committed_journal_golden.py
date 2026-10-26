"""Independent revision-24 authenticated-journal oracle, not a Builder/Writer round trip.

The archive bytes are frozen as a shared checkpoint plus appended raw byte segments
in conformance/v24-committed-journal.json.  No tested code is involved in constructing
or re-signing those bytes.  Tests must fail on source/format drift, never regenerate
the fixture through CMPCT's encoder.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct

import pytest

from cmpct.reader import CMPCT


VECTOR = Path(__file__).parent / "conformance" / "v24-committed-journal.json"
HEADER = struct.Struct("<8sHHQQQ32s")
FOOTER = struct.Struct("<8sBBBBQQQ32s")
BLOB_HEADER = struct.Struct("<4sBBHQQII32s")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _archive_variants():
    oracle = json.loads(VECTOR.read_text(encoding="utf-8"))
    assert oracle["schema"] == "cmpct-v24-independent-committed-journal-v1"
    segments = {name: base64.b64decode(encoded, validate=True)
                for name, encoded in oracle["segments"].items()}
    base = segments["base"]
    committed = base + segments["committed_delta"]
    variants = {
        "base": base,
        "committed": committed,
        "corrupt_successor": committed + segments["invalid_successor"],
        "incomplete_successor": committed + segments["incomplete_successor"],
    }
    for name, raw in variants.items():
        receipt = oracle["archives"][name]
        assert len(raw) == receipt["bytes"], name
        assert _sha(raw) == receipt["sha256"], name
    return oracle, variants


def test_independent_v24_journal_framing():
    """Prove fixed footer offsets and ancestor signatures without invoking Writer."""
    oracle, variants = _archive_variants()
    witness = oracle["witness"]
    raw = variants["committed"]
    magic, version, flags, primary_cs, primary_us, initial_data_span, index_sha = HEADER.unpack_from(raw)
    assert magic == b"CMPCT24\\0" and version == 24 and flags == 0
    assert HEADER.size + primary_cs == witness["record_base"]
    assert initial_data_span > BLOB_HEADER.size
    assert index_sha.hex() == witness["initial_index_sha256"]

    base_footer = FOOTER.unpack_from(raw, witness["initial_footer_offset"])
    assert base_footer[0] == b"CMPTF24\\0"
    assert base_footer[1:5] == (0, 1, 0, 0)  # checkpoint, Zstd, flags, reserved
    assert base_footer[7] == 0  # no previous generation
    assert base_footer[8].hex() == witness["initial_index_sha256"]

    delta_footer = FOOTER.unpack_from(raw, witness["delta_footer_offset"])
    assert delta_footer[0] == b"CMPTF24\\0"
    assert delta_footer[1:5] == (1, 1, 0, 0)  # signed delta, Zstd
    assert delta_footer[7] == witness["initial_footer_offset"]
    assert delta_footer[8].hex() == witness["delta_index_sha256"]

    # A new physical record is appended *after* the older signed commit footer.
    next_record = witness["record_base"] + witness["new_blob_record_offset_relative_base"]
    assert next_record == len(variants["base"])
    assert raw[next_record:next_record + 4] == b"CMA4"


@pytest.mark.parametrize(
    ("archive_name", "expected_generation", "expected_depth"),
    [
        ("base", "base", 0),
        ("committed", "latest", 1),
        ("corrupt_successor", "latest", 1),
        ("incomplete_successor", "latest", 1),
    ],
)
def test_independent_v24_journal_tree(
    tmp_path: Path, archive_name: str, expected_generation: str, expected_depth: int
):
    """Latest *authenticated* commit governs names and bytes, not last magic hit."""
    oracle, variants = _archive_variants()
    p = tmp_path / (archive_name + ".cmpct")
    p.write_bytes(variants[archive_name])
    expected = oracle["expected"][expected_generation]
    with CMPCT(p) as ar:
        assert ar.delta_depth == expected_depth
        expected_footer = (
            oracle["witness"]["initial_footer_offset"]
            if expected_depth == 0
            else oracle["witness"]["delta_footer_offset"]
        )
        assert ar.latest_footer_pos == expected_footer
        assert sorted(ar.by) == sorted(expected)
        assert ar.verify() == len(expected)

        for name, receipt in expected.items():
            logical = bytes.fromhex(receipt["hex"])
            assert _sha(logical) == receipt["sha256"]
            assert ar.read(name) == logical
            assert ar.read_range(name, 0, len(logical)) == logical
            assert ar.read_range(name, 3, 7) == logical[3:10]
            assert ar.read_range(name, len(logical), 0) == b""

        if expected_generation == "latest":
            assert "keep.txt" not in ar.by  # deletion won
            assert ar.read("alpha.txt") != ar.read("archived.txt")  # put after rename


def test_invalid_delta_commit_digest_reverts_to_older_checkpoint(tmp_path: Path):
    """An unauthenticated delta footer is never a committed new filesystem tree."""
    oracle, variants = _archive_variants()
    raw = bytearray(variants["committed"])
    digest_offset = oracle["witness"]["delta_footer_offset"] + (FOOTER.size - 32)
    raw[digest_offset] ^= 1
    p = tmp_path / "bad-delta-digest.cmpct"
    p.write_bytes(raw)
    with CMPCT(p) as ar:
        assert ar.delta_depth == 0
        assert ar.latest_footer_pos == oracle["witness"]["initial_footer_offset"]
        assert sorted(ar.by) == sorted(oracle["expected"]["base"])
        assert ar.verify() == 2


def test_authenticated_index_does_not_excuse_corrupt_appended_blob(tmp_path: Path):
    """Committing the index is not equivalent to authenticating future blob bytes."""
    oracle, variants = _archive_variants()
    raw = bytearray(variants["committed"])
    data_start = (
        oracle["witness"]["record_base"]
        + oracle["witness"]["new_blob_record_offset_relative_base"]
        + BLOB_HEADER.size
    )
    assert raw[data_start:data_start+3] == b"new"
    raw[data_start] ^= 1
    p = tmp_path / "bad-physical-data.cmpct"
    p.write_bytes(raw)
    with CMPCT(p) as ar:
        assert ar.delta_depth == 1
        assert "alpha.txt" in ar.by
        with pytest.raises((IOError, OSError, ValueError)):
            ar.verify()
