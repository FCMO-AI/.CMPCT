"""O54: actual installed O50 Builder deferred VZIP split-source scientific falsifier.

This is an adversarial test, NOT a new Builder implementation. The only hook is the
time between make_vzip_recipe's original ap.read_bytes() and its independent
zipfile.ZipFile(ap) opening of the very same regular source inode.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
import cmpct.builder as builder_mod
import cmpct.codec as codec_mod


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _zip_bytes(symbol: bytes) -> bytes:
    # ZIP_STORED removes compressor nondeterminism and makes the two ZIPs equal
    # length while preserving a byte-level difference under the same filename.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as writer:
        entry = zipfile.ZipInfo("member.txt", date_time=(2020, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_STORED
        writer.writestr(entry, symbol * 4096)
    result = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(result)) as r:
        assert r.read("member.txt") == symbol * 4096
    return result


A = _zip_bytes(b"A")
B = _zip_bytes(b"B")
assert len(A) == len(B) and A != B and _sha(A) != _sha(B)


def _create_source(tmp_path: Path, data: bytes):
    root = tmp_path / "tree"
    root.mkdir()
    source = root / "nested.zip"
    source.write_bytes(data)
    return root, source


def _build(root: Path, archive: Path):
    builder = Builder(root, workers=1, reproducible=True)
    info = builder.build(archive)
    kinds = [r[6][0] for r in builder.files if r[0] == "nested.zip" and r[6]]
    assert kinds == [builder_mod.S_VZIP], ("no-real-vzip", kinds)
    return info


def _read_and_verify(archive: Path):
    verdict = {"read_ok": False, "verify_ok": False}
    try:
        with CMPCT(archive) as reader:
            try:
                raw = reader.read("nested.zip")
                verdict["read_sha"] = _sha(raw)
                verdict["read_bytes"] = len(raw)
                verdict["read_ok"] = True
            except Exception as exc:
                verdict["read_error"] = type(exc).__name__ + ": " + str(exc)
            try:
                verdict["verify_n"] = reader.verify()
                verdict["verify_ok"] = True
            except Exception as exc:
                verdict["verify_error"] = type(exc).__name__ + ": " + str(exc)
    except Exception as exc:
        verdict["reader_error"] = type(exc).__name__ + ": " + str(exc)
    return verdict


@pytest.mark.parametrize("input_data", [A, B], ids=["original-A", "independent-B"])
def test_stable_installed_vzip_round_trip(tmp_path, input_data):
    root, source = _create_source(tmp_path, input_data)
    archive = tmp_path / "stable.cmpct"
    _build(root, archive)
    verdict = _read_and_verify(archive)
    assert verdict["read_ok"], verdict
    assert verdict["read_sha"] == _sha(input_data), verdict
    assert verdict["verify_ok"], verdict
    assert source.read_bytes() == input_data


def test_same_inode_split_source_vzip_custody(tmp_path, monkeypatch):
    root, source = _create_source(tmp_path, A)
    archive = tmp_path / "split.cmpct"
    pre = os.stat(source)
    pivot = {"count": 0, "before_sha": _sha(source.read_bytes())}
    real_zipfile = zipfile.ZipFile

    def open_real_after_pivot(file, *args, **kwargs):
        try:
            target = Path(file)
        except TypeError:
            target = None
        if target is not None and target == source and pivot["count"] == 0:
            # This call occurs *after* the authentic codec read `original=A`
            # and *before* its independent original ZipFile parse. The write
            # truncates/replaces the bytes of the same REGULAR INODE; there is
            # no symlink, FIFO, rename or outside-root path involved.
            assert source.read_bytes() == A
            source.write_bytes(B)
            pivot["count"] += 1
            pivot["after_sha"] = _sha(source.read_bytes())
            post = os.stat(source)
            pivot["inode_stable"] = (pre.st_dev, pre.st_ino) == (post.st_dev, post.st_ino)
            pivot["size_stable"] = pre.st_size == post.st_size
        return real_zipfile(file, *args, **kwargs)

    build_error = None
    with monkeypatch.context() as mp:
        mp.setattr(codec_mod.zipfile, "ZipFile", open_real_after_pivot)
        try:
            _build(root, archive)
        except Exception as exc:
            build_error = type(exc).__name__ + ": " + str(exc)

    verdict = _read_and_verify(archive) if archive.exists() and build_error is None else {}
    if build_error is not None:
        decision = "BUILDER_REJECTED"
    elif not verdict.get("read_ok") or not verdict.get("verify_ok"):
        decision = "EMITTED_UNVERIFIABLE_R24"
    elif verdict.get("read_sha") in (_sha(A), _sha(B)):
        decision = "EXACT_VERIFIED"
    else:
        decision = "OTHER_VERIFIED_CONTENT"

    details = {
        "source_pre_sha": _sha(A), "source_post_sha": _sha(B),
        "source_length": len(A), "original_inode": pre.st_ino,
        "mutator": pivot, "build_error": build_error,
        "archive_exists": archive.exists(),
        "archive_size": archive.stat().st_size if archive.exists() else None,
        "archive_sha": _sha(archive.read_bytes()) if archive.exists() else None,
        "reconstruction": verdict, "decision": decision,
        "runtime_os": os.name,
    }
    Path("o54-result.json").write_text(json.dumps(details, indent=2, sort_keys=True), encoding="utf-8")
    print("O54_RESULT=" + json.dumps(details, sort_keys=True))
    assert pivot["count"] == 1, ("NO_GENUINE_PIVOT", details)
    assert pivot["inode_stable"], ("INODE_CHANGED", details)
    assert pivot["size_stable"], ("SIZE_CHANGED", details)
    assert source.read_bytes() == B, ("SOURCE_DID_NOT_PIVOT", details)
    # Scientific prediction is prospective. Failure is an honest falsification,
    # not permission to weaken the source or comparator.
    assert decision == "EMITTED_UNVERIFIABLE_R24", details
