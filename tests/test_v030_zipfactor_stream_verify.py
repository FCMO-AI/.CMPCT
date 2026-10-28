from __future__ import annotations

import hashlib
import io
import zipfile

from experiments import entropygraph_v030_zipfactor_profile as BASE
from experiments import entropygraph_v030_zipfactor_stream_verify as STREAM

_DATE = (2022, 2, 2, 0, 0, 0)


def _zip_raw(seed: int, members: int) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for index in range(members):
            info = zipfile.ZipInfo(f"member-{index:02d}.txt", _DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            raw = "".join(
                f"seed={seed} member={index} row={row:04d} value={(seed * 997 + index * 31 + row * 17) % 65521}\n"
                for row in range(80 + index * 11)
            ).encode()
            zf.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return buffer.getvalue()


def _template_and_dynamics(raw: bytes) -> tuple[dict, list[tuple[int, int, int, bytes]]]:
    parsed = BASE._parse_zip(raw)
    assert parsed is not None
    template = BASE._parse_template(BASE._serialize_template(parsed))
    dynamics = [
        (int(local["crc"]), int(local["csize"]), int(local["usize"]), local["payload"])
        for local in parsed["locals"]
    ]
    return template, dynamics


def test_streaming_rebuild_identity_matches_materialized_reference_across_unseen_shapes() -> None:
    for seed, members in ((7, 1), (19, 3), (43, 7)):
        source = _zip_raw(seed, members)
        template, dynamics = _template_and_dynamics(source)
        restored = BASE._rebuild_zip(template, dynamics)
        size, digest = STREAM.rebuilt_zip_identity(template, dynamics)
        assert restored == source
        assert size == len(restored)
        assert digest == hashlib.sha256(restored).digest()


def test_streaming_rebuild_identity_rejects_payload_length_mismatch() -> None:
    source = _zip_raw(71, 2)
    template, dynamics = _template_and_dynamics(source)
    crc, csize, usize, payload = dynamics[0]
    bad = list(dynamics)
    bad[0] = (crc, csize + 1, usize, payload)
    try:
        STREAM.rebuilt_zip_identity(template, bad)
    except RuntimeError as exc:
        assert "compressed payload length mismatch" in str(exc)
    else:
        raise AssertionError("streaming identity accepted inconsistent compressed payload length")
