from __future__ import annotations

import copy
import zipfile

from experiments import entropygraph_v030_zipfactor_eocd_parser as ZIP
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_profile as BASE


def _zip(path, *, payload: bytes = b"A" * 256, comment: bytes = b"") -> bytes:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.comment = comment
        archive.writestr("same/member.txt", payload)
    return path.read_bytes()


def test_framing_reference_is_exact_mature_signature_projection(tmp_path):
    parsed = ZIP.parse_zip(_zip(tmp_path / "a.zip"))
    assert parsed is not None
    assert ZIP.framing_reference(parsed) == BASE._signature(parsed)


def test_inline_parser_returns_identical_object_and_same_static_match(tmp_path):
    left = ZIP.parse_zip(_zip(tmp_path / "left.zip", payload=b"A" * 256))
    raw_right = _zip(tmp_path / "right.zip", payload=b"B" * 256)
    assert left is not None
    reference = ZIP.framing_reference(left)

    ordinary = ZIP.parse_zip(raw_right)
    inline, match = ZIP.parse_zip_with_framing(raw_right, reference)
    assert ordinary is not None and inline == ordinary
    # CRC/payload/sizes are dynamic and do not belong to the framing signature.
    assert match is FUSED._same_framing_signature(left, ordinary) is True


def test_inline_parser_distinguishes_valid_framing_drift_from_malformed_zip(tmp_path):
    left = ZIP.parse_zip(_zip(tmp_path / "left.zip"))
    assert left is not None
    reference = ZIP.framing_reference(left)

    drift_raw = _zip(tmp_path / "drift.zip", comment=b"different-static-comment")
    drift = ZIP.parse_zip(drift_raw)
    inline, match = ZIP.parse_zip_with_framing(drift_raw, reference)
    assert drift is not None and inline == drift
    assert FUSED._same_framing_signature(left, drift) is False
    assert match is False

    malformed = bytearray(drift_raw)
    malformed[0:4] = b"NOPE"
    inline_bad, match_bad = ZIP.parse_zip_with_framing(bytes(malformed), reference)
    assert inline_bad is None
    assert match_bad is False


def test_inline_match_tracks_every_exact_static_owned_field(tmp_path):
    raw = _zip(tmp_path / "source.zip")
    parsed = ZIP.parse_zip(raw)
    assert parsed is not None
    reference = ZIP.framing_reference(parsed)

    # The direct reference projection is immutable and must preserve the exact mature owned-field sets. Mutating any
    # one projected value must turn a valid parse into framing drift without changing parse validity.
    for section, row_index, value_index in (
        (0, 0, 0),  # local version
        (0, 0, 5),  # local name
        (1, 0, 0),  # central made-by
        (1, 0, 8),  # central comment
        (2, None, 0),  # EOCD disk
        (2, None, 2),  # EOCD comment
    ):
        mutated = copy.deepcopy(reference)
        # tuple projection is intentionally immutable: rebuild only the selected row/value in the test reference.
        top = list(mutated)
        if section < 2:
            rows = list(top[section])
            row = list(rows[row_index])
            current = row[value_index]
            row[value_index] = (current + b"x") if isinstance(current, bytes) else int(current) + 1
            rows[row_index] = tuple(row)
            top[section] = tuple(rows)
        else:
            row = list(top[section])
            current = row[value_index]
            row[value_index] = (current + b"x") if isinstance(current, bytes) else int(current) + 1
            top[section] = tuple(row)
        inline, match = ZIP.parse_zip_with_framing(raw, tuple(top))
        assert inline == parsed
        assert match is False
