"""Streaming identity verifier for the pre-selector r25 ZIP-factor profiles.

The existing verifier reconstructs every logical ZIP into a temporary ``bytes`` object and then hashes that object.
This module emits the exact same ZIP byte sequence directly into SHA-256 while counting its length. It therefore
preserves complete logical-file identity verification while removing the second full-size allocation/copy of every
restored ZIP. It is preparatory optimization only: selector/native/Android/recovery promotion remain unchanged.
"""
from __future__ import annotations

import hashlib
import struct

from experiments import entropygraph_v030_zipfactor_profile as BASE


def rebuilt_zip_identity(template: dict, dynamics: list[tuple[int, int, int, bytes]]) -> tuple[int, bytes]:
    """Return the exact rebuilt ZIP ``(size, sha256)`` without materializing the ZIP."""
    if len(dynamics) != len(template["rows"]):
        raise RuntimeError("ZIP-factor dynamic member count mismatch")

    digest = hashlib.sha256()
    position = 0
    offsets: list[int] = []

    def emit(raw: bytes) -> None:
        nonlocal position
        digest.update(raw)
        position += len(raw)

    for row, (crc, csize, usize, payload) in zip(template["rows"], dynamics, strict=True):
        if len(payload) != csize:
            raise RuntimeError("ZIP-factor compressed payload length mismatch")
        offsets.append(position)
        emit(struct.pack(
            "<IHHHHHIIIHH",
            BASE.LOCAL,
            row["version"],
            row["flags"],
            row["method"],
            row["mtime"],
            row["mdate"],
            crc,
            csize,
            usize,
            len(row["name"]),
            len(row["local_extra"]),
        ))
        emit(row["name"])
        emit(row["local_extra"])
        emit(payload)

    cd_start = position
    for row, (crc, csize, usize, _payload), offset in zip(
        template["rows"], dynamics, offsets, strict=True
    ):
        emit(struct.pack(
            "<IHHHHHHIIIHHHHHII",
            BASE.CENTRAL,
            row["made"],
            row["needed"],
            row["cflags"],
            row["cmethod"],
            row["cmtime"],
            row["cmdate"],
            crc,
            csize,
            usize,
            len(row["name"]),
            len(row["central_extra"]),
            len(row["central_comment"]),
            row["disk"],
            row["internal_attr"],
            row["external_attr"],
            offset,
        ))
        emit(row["name"])
        emit(row["central_extra"])
        emit(row["central_comment"])

    cd_size = position - cd_start
    count = len(template["rows"])
    emit(struct.pack(
        "<IHHHHIIH",
        BASE.EOCD,
        template["disk"],
        template["disk_cd"],
        count,
        count,
        cd_size,
        cd_start,
        len(template["comment"]),
    ))
    emit(template["comment"])
    return position, digest.digest()


def assert_equivalent(template: dict, dynamics: list[tuple[int, int, int, bytes]]) -> None:
    """Development guard: prove streaming identity equals the materialized reference implementation."""
    restored = BASE._rebuild_zip(template, dynamics)
    size, digest = rebuilt_zip_identity(template, dynamics)
    if size != len(restored) or digest != hashlib.sha256(restored).digest():
        raise RuntimeError("streaming ZIP-factor identity diverged from reference reconstruction")
