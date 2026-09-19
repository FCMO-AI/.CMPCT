from __future__ import annotations

import io
import struct
import zipfile

import pytest

from experiments import entropygraph_v030_zipfactor_eocd_parser as EOCD
from experiments import entropygraph_v030_zipfactor_profile as BASE


def _zip_bytes(*, compression: int, comment: bytes = b"") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=compression, allowZip64=False) as zf:
        zf.comment = comment
        zf.writestr("a.txt", b"alpha\n" * 128)
        zf.writestr("nested/b.bin", bytes(range(256)) * 8)
        zf.writestr("empty", b"")
    return out.getvalue()


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
@pytest.mark.parametrize("comment", [b"", b"ordinary-comment", b"comment-PK\x05\x06-false-eocd"])
def test_fused_parser_is_exactly_equivalent_on_owned_valid_zip_subset(compression: int, comment: bytes) -> None:
    raw = _zip_bytes(compression=compression, comment=comment)
    mature = BASE._parse_zip(raw)
    fused = EOCD.parse_zip(raw)
    assert mature is not None
    assert fused == mature


def _first_central_offset(raw: bytes) -> int:
    eocd = raw.rfind(b"PK\x05\x06", max(0, len(raw) - EOCD.MAX_EOCD_SEARCH))
    assert eocd >= 0
    fields = EOCD.EOCD_HDR.unpack_from(raw, eocd)
    return int(fields[6])


def _mutate_u16(raw: bytes, offset: int, value: int) -> bytes:
    out = bytearray(raw)
    struct.pack_into("<H", out, offset, value)
    return bytes(out)


def _mutate_u32(raw: bytes, offset: int, value: int) -> bytes:
    out = bytearray(raw)
    struct.pack_into("<I", out, offset, value)
    return bytes(out)


@pytest.mark.parametrize(
    "mutation",
    [
        "central-method-mismatch",
        "central-crc-mismatch",
        "central-local-offset-gap",
        "local-data-descriptor-flag",
        "local-encryption-flag",
    ],
)
def test_fused_parser_matches_mature_fail_closed_boundary(mutation: str) -> None:
    raw = _zip_bytes(compression=zipfile.ZIP_DEFLATED)
    central = _first_central_offset(raw)
    local = 0

    if mutation == "central-method-mismatch":
        current = struct.unpack_from("<H", raw, central + 10)[0]
        candidate = _mutate_u16(raw, central + 10, 0 if current == 8 else 8)
    elif mutation == "central-crc-mismatch":
        current = struct.unpack_from("<I", raw, central + 16)[0]
        candidate = _mutate_u32(raw, central + 16, current ^ 0x01020304)
    elif mutation == "central-local-offset-gap":
        candidate = _mutate_u32(raw, central + 42, 1)
    elif mutation == "local-data-descriptor-flag":
        flags = struct.unpack_from("<H", raw, local + 6)[0]
        candidate = _mutate_u16(raw, local + 6, flags | 0x0008)
    elif mutation == "local-encryption-flag":
        flags = struct.unpack_from("<H", raw, local + 6)[0]
        candidate = _mutate_u16(raw, local + 6, flags | 0x0001)
    else:  # pragma: no cover - parametrization is closed above.
        raise AssertionError(mutation)

    assert BASE._parse_zip(candidate) is None
    assert EOCD.parse_zip(candidate) is None


def test_fused_parser_rejects_truncated_and_trailing_topology_exactly_like_mature_parser() -> None:
    raw = _zip_bytes(compression=zipfile.ZIP_DEFLATED)
    cases = [raw[:-1], raw + b"trailing", raw[:20]]
    for candidate in cases:
        assert EOCD.parse_zip(candidate) == BASE._parse_zip(candidate)
        assert EOCD.parse_zip(candidate) is None
