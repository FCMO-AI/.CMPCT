"""Adversarial ownership test: a failed CMPCT open must not leak its acquired resources.

Uses module-level handle spies instead of /proc/fd to be portable and to avoid
accidental passing when CPython's reference counting collects an exception frame.
Keep all exceptions alive until *after* the close assertions.
"""
from __future__ import annotations

import base64
import builtins
import hashlib
import json
import mmap
from pathlib import Path

import pytest

import cmpct.reader as reader


def _watch_files(monkeypatch):
    seen = []
    original = builtins.open

    def observe(*args, **kwargs):
        f = original(*args, **kwargs)
        seen.append(f)
        return f

    monkeypatch.setattr(reader, "open", observe, raising=False)
    return seen


def _fixed_valid_archive(tmp_path):
    fixture = json.loads(
        (Path(__file__).parent / "conformance" / "v24-direct-codecs.json").read_text()
    )["vectors"][0]
    blob = base64.b64decode(fixture["archive_base64"], validate=True)
    assert hashlib.sha256(blob).hexdigest() == fixture["archive_sha256"]
    archive = tmp_path / "frozen.cmpct"
    archive.write_bytes(blob)
    return archive, fixture["name"]


def test_failed_header_closes_owned_file_without_gc(tmp_path, monkeypatch):
    p = tmp_path / "corrupted.cmpct"
    p.write_bytes(b"\0" * reader.HDR.size)
    files = _watch_files(monkeypatch)
    with pytest.raises((IOError, ValueError)) as exc:
        reader.CMPCT(p)
    assert exc.value is not None  # keep exception + traceback alive
    assert len(files) == 1
    assert files[0].closed, "failed open leaked file while exception was retained"


def test_failed_mmap_closes_owned_file_without_gc(tmp_path, monkeypatch):
    p = tmp_path / "mapper.cmpct"
    p.write_bytes(b"X")
    files = _watch_files(monkeypatch)

    def fake_index(_self):
        return {"files": [], "blobs": [], "recipes": []}, 0

    def failed_map(*args, **kwargs):
        raise OSError("injected mapper failure")

    monkeypatch.setattr(reader.CMPCT, "_load_index", fake_index)
    monkeypatch.setattr(reader.mmap, "mmap", failed_map)
    with pytest.raises(OSError, match="injected mapper failure") as exc:
        reader.CMPCT(p)
    assert exc.value is not None
    assert len(files) == 1
    assert files[0].closed, "mmap failure leaked archive descriptor"


def test_canonical_collision_closes_owned_file_and_map(tmp_path, monkeypatch):
    p = tmp_path / "alias.cmpct"
    p.write_bytes(b"X")
    files = _watch_files(monkeypatch)
    maps = []
    original_map = mmap.mmap

    def watch_map(*args, **kwargs):
        mm = original_map(*args, **kwargs)
        maps.append(mm)
        return mm

    def fake_index(_self):
        return {"files": [["tree/leaf"], ["tree\\leaf"]], "blobs": [], "recipes": []}, 0

    monkeypatch.setattr(reader.CMPCT, "_load_index", fake_index)
    monkeypatch.setattr(reader.mmap, "mmap", watch_map)
    with pytest.raises(IOError, match="duplicate canonical logical path") as exc:
        reader.CMPCT(p)
    assert exc.value is not None
    assert len(files) == 1 and len(maps) == 1
    assert files[0].closed, "canonical collision leaked file"
    assert maps[0].closed, "canonical collision leaked mmap"


def test_independent_valid_r24_archive_opens_normally(tmp_path, monkeypatch):
    p, name = _fixed_valid_archive(tmp_path)
    files = _watch_files(monkeypatch)
    with reader.CMPCT(p) as archive:
        assert archive.read(name) == bytes(range(64))
        assert len(files) == 1
        assert not files[0].closed
    assert files[0].closed
