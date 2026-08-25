from __future__ import annotations

import hashlib

from benchmarks.v030_zipfactor_streaming_identity_oracle import _stream_zip_identity
from experiments import entropygraph_v030_zipfactor_profile as BASE


def test_stream_zip_identity_matches_materialized_reconstruction() -> None:
    template = {
        "rows": [
            {
                "name": b"alpha.txt",
                "local_extra": b"",
                "version": 20,
                "flags": 0,
                "method": 8,
                "mtime": 0,
                "mdate": 0,
                "made": 20,
                "needed": 20,
                "cflags": 0,
                "cmethod": 8,
                "cmtime": 0,
                "cmdate": 0,
                "disk": 0,
                "internal_attr": 0,
                "external_attr": 0,
                "central_extra": b"",
                "central_comment": b"",
            },
            {
                "name": b"beta.bin",
                "local_extra": b"\x01\x02",
                "version": 20,
                "flags": 0,
                "method": 0,
                "mtime": 1,
                "mdate": 2,
                "made": 20,
                "needed": 20,
                "cflags": 0,
                "cmethod": 0,
                "cmtime": 1,
                "cmdate": 2,
                "disk": 0,
                "internal_attr": 1,
                "external_attr": 0x20,
                "central_extra": b"\x03",
                "central_comment": b"note",
            },
        ],
        "disk": 0,
        "disk_cd": 0,
        "comment": b"fixture",
    }
    dynamics = [
        (0x12345678, 5, 12, b"abcde"),
        (0x90ABCDEF, 4, 4, b"WXYZ"),
    ]
    materialized = BASE._rebuild_zip(template, dynamics)
    size, digest = _stream_zip_identity(template, dynamics)
    assert size == len(materialized)
    assert digest == hashlib.sha256(materialized).digest()


def test_stream_zip_identity_rejects_payload_length_mismatch() -> None:
    template = {
        "rows": [{
            "name": b"x",
            "local_extra": b"",
            "version": 20,
            "flags": 0,
            "method": 0,
            "mtime": 0,
            "mdate": 0,
            "made": 20,
            "needed": 20,
            "cflags": 0,
            "cmethod": 0,
            "cmtime": 0,
            "cmdate": 0,
            "disk": 0,
            "internal_attr": 0,
            "external_attr": 0,
            "central_extra": b"",
            "central_comment": b"",
        }],
        "disk": 0,
        "disk_cd": 0,
        "comment": b"",
    }
    try:
        _stream_zip_identity(template, [(0, 2, 2, b"x")])
    except RuntimeError as exc:
        assert "payload length mismatch" in str(exc)
    else:
        raise AssertionError("streaming identity accepted mismatched compressed payload length")
