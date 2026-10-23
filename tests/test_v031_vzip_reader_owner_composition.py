"""Cross-owner exact revision-24 court: VZIP rollback and owner-first hardlink extraction.

A late, valid but non-reproducible Z_FIXED Deflate member forces opaque fallback
*after* a first ZIP member aliases an earlier loose file candidate. The ZIP
also has an on-disk hardlink whose index row precedes its deferred owner.
The reference uses the same Builder/Reader with virtualization disabled, so
the full archive bytes — not only reconstructed payloads — must match.
"""
from __future__ import annotations

import os
import zipfile
import zlib

import pytest

import cmpct.builder as builder_module
from cmpct.builder import Builder
from cmpct.codec import K_HARDLINK, S_VZIP, _compressed_payload, deflate_level_for
from cmpct.reader import CMPCT


FIRST = b"shared-content-from-valid-earlier-member\n" * 311
SECOND = b"Stage VZIP candidate with repeated tokens and punctuation.\n" * 700


def test_late_vzip_fallback_preserves_complete_archive_and_out_of_order_hardlink(tmp_path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    (source / "00-common.bin").write_bytes(FIRST)
    nested = source / "10-nested.zip"

    ordinary_compressor = zipfile._get_compressor

    def fixed_deflate(compression, level=None):
        if compression == zipfile.ZIP_DEFLATED:
            return zlib.compressobj(6, zlib.DEFLATED, -15, zlib.DEF_MEM_LEVEL, zlib.Z_FIXED)
        return ordinary_compressor(compression, level)

    with zipfile.ZipFile(nested, "w") as zf:
        zf.writestr("first.txt", FIRST, compress_type=zipfile.ZIP_STORED)
        with monkeypatch.context() as mp:
            mp.setattr(zipfile, "_get_compressor", fixed_deflate)
            zf.writestr("second.txt", SECOND, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    zip_bytes = nested.read_bytes()
    with zipfile.ZipFile(nested) as zf:
        assert zf.read("first.txt") == FIRST
        assert zf.read("second.txt") == SECOND
        assert deflate_level_for(SECOND, _compressed_payload(nested, zf.infolist()[-1])) is None

    # The deferred virtual-ZIP owner will be appended to the index after its
    # hardlink alias. Earlier Reader implementations materialized in index order.
    alias = source / "20-alias.zip"
    os.link(nested, alias)
    assert os.stat(nested).st_ino == os.stat(alias).st_ino

    candidate = tmp_path / "candidate.cmpct"
    opaque_control = tmp_path / "forced-opaque.cmpct"
    Builder(source, workers=1, reproducible=True).build(candidate)
    with monkeypatch.context() as mp:
        mp.setattr(builder_module, "make_vzip_recipe", lambda _path, _add: None)
        Builder(source, workers=1, reproducible=True).build(opaque_control)

    assert candidate.read_bytes() == opaque_control.read_bytes(), (
        "rejected speculative VZIP polluted the serialized physical plan"
    )

    dest = tmp_path / "extracted"
    with CMPCT(candidate) as ar:
        assert ar.verify()
        assert ar.read("00-common.bin") == FIRST
        assert ar.read("10-nested.zip") == zip_bytes
        assert ar.read("20-alias.zip") == zip_bytes
        assert ar.by["20-alias.zip"][1] == K_HARDLINK
        assert ar.by["20-alias.zip"][6][0] == "10-nested.zip"
        assert ar.by["10-nested.zip"][6][0] != S_VZIP
        names = [row[0] for row in ar.files]
        assert names.index("20-alias.zip") < names.index("10-nested.zip")
        ar.extractall(dest)

    assert (dest / "00-common.bin").read_bytes() == FIRST
    assert (dest / "10-nested.zip").read_bytes() == zip_bytes
    assert (dest / "20-alias.zip").read_bytes() == zip_bytes
    owned = os.stat(dest / "10-nested.zip")
    linked = os.stat(dest / "20-alias.zip")
    assert (owned.st_dev, owned.st_ino) == (linked.st_dev, linked.st_ino), (
        "hardlink alias lost physical inode identity despite exact logical bytes"
    )
