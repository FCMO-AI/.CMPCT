from __future__ import annotations

"""Revision-24 explicit VZIP fallback transactional candidate ownership (#206).

The oracle uses a valid standard ZIP whose last member is raw-DEFLATE Z_FIXED:
it inflates exactly but cannot be recreated by CMPCT's standard-level search.
Do not replace the fixed-stream adversary with an arbitrary corrupt ZIP.
"""

import hashlib
import zipfile
import zlib
from pathlib import Path

import pytest

import cmpct.builder as builder_module
from cmpct.builder import Builder
from cmpct.codec import K_FILE, S_BLOB, S_PACK, S_VZIP, _compressed_payload, deflate_level_for, make_vzip_recipe
from cmpct.reader import CMPCT


FIRST = b"shared-content-from-valid-earlier-member\n" * 311
SECOND = (b"Stage VZIP candidate with repeated tokens and punctuation.\n" * 700)


def _make_zip(path: Path, monkeypatch, *, fixed_last: bool) -> bytes:
    get_compressor = zipfile._get_compressor

    def fixed(compression: int, level=None):
        if compression == zipfile.ZIP_DEFLATED:
            return zlib.compressobj(6, zlib.DEFLATED, -15, zlib.DEF_MEM_LEVEL, zlib.Z_FIXED)
        return get_compressor(compression, level)

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("first.txt", FIRST, compress_type=zipfile.ZIP_STORED)
        if fixed_last:
            with monkeypatch.context() as p:
                p.setattr(zipfile, "_get_compressor", fixed)
                zf.writestr("second.txt", SECOND, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        else:
            zf.writestr("second.txt", SECOND, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    source = path.read_bytes()
    with zipfile.ZipFile(path) as zf:
        assert zf.read("first.txt") == FIRST
        assert zf.read("second.txt") == SECOND
        members = zf.infolist()
        assert len(members) == 2
        stream = _compressed_payload(path, members[-1])
        assert bool(deflate_level_for(SECOND, stream) is None) == fixed_last
    return source


def _snapshot(builder: Builder):
    return {
        h: (c.raw, frozenset(c.hints), tuple(sorted((sh, stream, n) for sh, (stream, n) in c.deflates.items())))
        for h, c in builder.cands.items()
    }


def _forced_opaque(builder: Builder, root: Path, monkeypatch) -> None:
    # Reference control, not a competing VZIP algorithm.
    with monkeypatch.context() as p:
        p.setattr(builder_module, "make_vzip_recipe", lambda _path, _callback: None)
        builder.scan()


def test_late_nonreproducible_deflate_discards_all_earlier_candidates(tmp_path: Path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    payload = _make_zip(source / "nested.zip", monkeypatch, fixed_last=True)
    b = Builder(source, workers=1, reproducible=True)
    b.scan()

    # A rejected recipe must be indistinguishable from never probing the ZIP.
    assert b.recipes == []
    assert len(b.files) == 1
    assert b.files[0][1] == K_FILE and b.files[0][6][0] == S_BLOB
    assert _snapshot(b) == {hashlib.sha256(payload).digest(): (payload, frozenset({".zip"}), ())}


def test_late_fallback_is_complete_archive_byte_identical_to_opaque_control(tmp_path: Path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    original = _make_zip(source / "nested.zip", monkeypatch, fixed_last=True)
    candidate = tmp_path / "candidate.cmpct"
    opaque = tmp_path / "opaque.cmpct"
    Builder(source, workers=1, reproducible=True).build(candidate)
    with monkeypatch.context() as p:
        p.setattr(builder_module, "make_vzip_recipe", lambda _path, _callback: None)
        Builder(source, workers=1, reproducible=True).build(opaque)

    # The control has identical file content and explicit opaque semantics.
    assert candidate.read_bytes() == opaque.read_bytes()
    with CMPCT(candidate) as ar:
        assert ar.read("nested.zip") == original
        assert ar.verify()


def test_late_fallback_does_not_mutate_preexisting_member_alias(tmp_path: Path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    (source / "common.bin").write_bytes(FIRST)
    _make_zip(source / "nested.zip", monkeypatch, fixed_last=True)

    baseline = Builder(source, workers=1, reproducible=True)
    _forced_opaque(baseline, source, monkeypatch)
    candidate = Builder(source, workers=1, reproducible=True)
    candidate.scan()
    assert _snapshot(candidate) == _snapshot(baseline)
    assert candidate.files == baseline.files
    assert candidate.recipes == baseline.recipes


def test_late_probe_exception_rolls_back_before_reraising(tmp_path: Path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    (source / "common.bin").write_bytes(FIRST)
    (source / "nested.zip").write_bytes(b"opaque control, replacement mock raises")
    def fail_after_two_adds(_path, add):
        add(FIRST, ".other", b"sample deflate")
        add(b"unreferenced-new-blob", ".junk")
        raise RuntimeError("late recipe error")

    b = Builder(source, workers=1, reproducible=True)
    with monkeypatch.context() as p:
        p.setattr(builder_module, "make_vzip_recipe", fail_after_two_adds)
        with pytest.raises(RuntimeError, match="late recipe"):
            b.scan()
    # The already-scanned ordinary file remains; the ZIP has not reached its
    # opaque fallback because the original parse error must propagate.
    original_hash = hashlib.sha256(FIRST).digest()
    assert _snapshot(b) == {original_hash: (FIRST, frozenset({".bin"}), ())}
    assert isinstance(b.cands, dict)


def test_successful_vzip_preserves_original_candidate_and_recipe_semantics(tmp_path: Path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    nested = source / "nested.zip"
    original = _make_zip(nested, monkeypatch, fixed_last=False)

    historical = Builder(source, workers=1, reproducible=True)
    recipe = make_vzip_recipe(nested, historical.add_content)
    assert recipe is not None
    candidate = Builder(source, workers=1, reproducible=True)
    candidate.scan()
    assert candidate.recipes == [recipe]
    assert candidate.files[0][6] == [S_VZIP, 0]
    assert _snapshot(candidate) == _snapshot(historical)

    out = tmp_path / "success.cmpct"
    Builder(source, workers=1, reproducible=True).build(out)
    with CMPCT(out) as ar:
        assert ar.read("nested.zip") == original
        assert ar.verify()


def test_eight_explicit_containers_preserve_pack_admission(tmp_path: Path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    for i in range(8):
        _make_zip(source / f"nested{i}.zip", monkeypatch, fixed_last=i % 2 == 0)
    b = Builder(source, workers=1, reproducible=True)
    b.scan()
    assert not b.recipes
    assert len(b.files) == 8
    assert all(row[6][0] == S_PACK for row in b.files)
