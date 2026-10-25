"""O63: actual r24 one-capture ZIP x transaction-rollback composition.

Preserves independent #287 fixed-Huffman failure and #415 one-buffer source-
coherency laws. A failed speculative VZIP must equal opaque admission in physical
archive bytes; a successful recipe must retain existing stable O60 behavior.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
import zlib
from pathlib import Path

import pytest

import cmpct.builder as builder_module
from cmpct.builder import Builder
from cmpct.codec import S_BLOB, S_VZIP, _compressed_payload, deflate_level_for
from cmpct.reader import CMPCT


FIRST = b"valid initial STORED member, never a commit\n" * 311
SECOND = b"late fixed-Huffman valid DEFLATE, cannot be regenerated\n" * 700


def make_zip(path: Path, monkeypatch, *, fixed_last: bool) -> bytes:
    historical_compressor = zipfile._get_compressor

    def fixed_strategy(compression, level=None):
        if compression == zipfile.ZIP_DEFLATED:
            return zlib.compressobj(
                6, zlib.DEFLATED, -15, zlib.DEF_MEM_LEVEL, zlib.Z_FIXED
            )
        return historical_compressor(compression, level)

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("first.txt", FIRST, compress_type=zipfile.ZIP_STORED)
        if fixed_last:
            with monkeypatch.context() as mp:
                mp.setattr(zipfile, "_get_compressor", fixed_strategy)
                z.writestr("second.txt", SECOND, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        else:
            z.writestr("second.txt", SECOND, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    with zipfile.ZipFile(path) as z:
        assert z.read("first.txt") == FIRST
        assert z.read("second.txt") == SECOND
        stream = _compressed_payload(path, z.infolist()[-1])
        assert (deflate_level_for(SECOND, stream) is None) is fixed_last
    return path.read_bytes()


def state(b: Builder):
    return {
        h: (c.raw, frozenset(c.hints),
            tuple(sorted((sh, bs, count)
                         for sh, (bs, count) in c.deflates.items())))
        for h, c in b.cands.items()
    }


def build(root: Path, out: Path):
    b = Builder(root, workers=1, reproducible=True)
    b.build(out)
    return b


@pytest.mark.parametrize("extension", ["zip", "whl"])
def test_late_valid_fixed_huffman_fallback_equals_forced_opaque_archive(
    tmp_path, monkeypatch, extension
):
    root = tmp_path / "input"
    root.mkdir()
    nested = root / ("payload." + extension)
    raw = make_zip(nested, monkeypatch, fixed_last=True)

    candidate_path = tmp_path / "candidate.cmpct"
    control_path = tmp_path / "opaque.cmpct"
    candidate = build(root, candidate_path)

    with monkeypatch.context() as mp:
        mp.setattr(builder_module, "make_vzip_recipe", lambda *_a, **_kw: None)
        control = build(root, control_path)

    assert candidate.recipes == control.recipes == []
    assert state(candidate) == state(control)
    assert candidate.files == control.files
    assert candidate_path.read_bytes() == control_path.read_bytes()
    with CMPCT(candidate_path) as reader:
        assert reader.read(nested.name) == raw
        assert reader.verify() >= 1


def test_aborted_probe_restores_shared_hash_hints_and_deflate_variants(tmp_path, monkeypatch):
    root = tmp_path / "input"
    root.mkdir()
    (root / "common.bin").write_bytes(FIRST)
    nested = root / "nested.zip"
    make_zip(nested, monkeypatch, fixed_last=True)

    candidate = Builder(root, workers=1, reproducible=True)
    candidate.scan()
    with monkeypatch.context() as mp:
        mp.setattr(builder_module, "make_vzip_recipe", lambda *_a, **_kw: None)
        control = Builder(root, workers=1, reproducible=True)
        control.scan()

    assert state(candidate) == state(control)
    assert candidate.files == control.files


@pytest.mark.parametrize("extension", ["zip", "whl"])
def test_successful_virtual_recipe_preserves_existing_o60_archive_bytes(
    tmp_path, monkeypatch, extension
):
    root = tmp_path / "input"
    root.mkdir()
    path = root / ("ok." + extension)
    raw = make_zip(path, monkeypatch, fixed_last=False)

    candidate_path = tmp_path / "candidate.cmpct"
    b = build(root, candidate_path)
    assert b.files[0][6][0] == S_VZIP and len(b.recipes) == 1
    with CMPCT(candidate_path) as reader:
        assert reader.read(path.name) == raw
        assert reader.verify() >= 1

    # Stable-result byte identity is also exercised by the original O60
    # full-historical product court, executed unchanged in this workflow.


def test_late_exception_restores_existing_candidates_in_place(tmp_path, monkeypatch):
    root = tmp_path / "input"
    root.mkdir()
    (root / "common.bin").write_bytes(FIRST)
    (root / "nested.zip").write_bytes(b"opaque bytes; mock must fail after mutations")

    b = Builder(root, workers=1, reproducible=True)
    before = hashlib.sha256(FIRST).digest()

    def fail(_path, add_content, *, original=None):
        assert original is not None
        add_content(FIRST, ".txt", b"compressed candidate")
        add_content(b"unreferenced", ".junk")
        raise RuntimeError("deliberate late parse failure")

    with monkeypatch.context() as mp:
        mp.setattr(builder_module, "make_vzip_recipe", fail)
        with pytest.raises(RuntimeError, match="deliberate"):
            b.scan()

    assert state(b) == {
        before: (FIRST, frozenset({".bin"}), ())
    }
    assert isinstance(b.cands, dict)


def test_failed_probe_keeps_single_captured_source_read(tmp_path, monkeypatch):
    root = tmp_path / "input"
    root.mkdir()
    source = root / "nested.zip"
    raw = make_zip(source, monkeypatch, fixed_last=True)
    real_read = Path.read_bytes
    observations = []

    def spy(path):
        if path == source:
            observations.append(path)
        return real_read(path)

    with monkeypatch.context() as mp:
        mp.setattr(Path, "read_bytes", spy)
        b = Builder(root, workers=1, reproducible=True)
        b.scan()

    assert len(observations) == 1, "fallback must not reopen source"
    assert b.files[0][6][0] == S_BLOB
    assert b.cands[hashlib.sha256(raw).digest()].raw == raw
