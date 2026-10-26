"""O167 positive authentic r24 Win32 no-follow metadata restoration court.

O102 (#457) is the frozen *negative* baseline and remains unmodified. A
green O167 test requires true physical file/directory timestamp restoration,
not merely Reader.extractall returning or payload SHA verification.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest
from cmpct.core import Builder, CMPCT
from cmpct._win32_times import restore_win32_leaf_mtime

STAMP_NS = 1_580_643_296_000_000_000
DIFFERENT_NS = 1_548_934_400_000_000_000
TOLERANCE_NS = 3_000_000_000
PAYLOAD = b"o167 authentic r24 timestamp payload\x00\xff" * 101


def close_ns(actual: int, expected: int) -> bool:
    return abs(int(actual) - int(expected)) <= TOLERANCE_NS


def _receipt(name: str, fields: dict) -> None:
    path = os.environ.get("O167_RECEIPT_DIR")
    if path:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        (p / (name + ".json")).write_text(json.dumps(fields, sort_keys=True, indent=2) + "\n")


def test_host_source_timestamp_control(tmp_path: Path) -> None:
    sub = tmp_path / "control"
    sub.mkdir()
    leaf = sub / "file.bin"
    leaf.write_bytes(PAYLOAD)
    os.utime(leaf, ns=(STAMP_NS, STAMP_NS))
    os.utime(sub, ns=(STAMP_NS, STAMP_NS))
    assert close_ns(leaf.stat().st_mtime_ns, STAMP_NS)
    assert close_ns(sub.stat().st_mtime_ns, STAMP_NS)


def test_authentic_r24_extract_restores_physical_timestamps(tmp_path: Path) -> None:
    src = tmp_path / "source"
    sub = src / "sub"
    sub.mkdir(parents=True)
    member = sub / "payload.bin"
    member.write_bytes(PAYLOAD)
    os.utime(member, ns=(STAMP_NS, STAMP_NS))
    os.utime(sub, ns=(STAMP_NS, STAMP_NS))

    archive = tmp_path / "authentic-r24.cmpct"
    Builder(src, workers=1).build(archive)
    assert archive.read_bytes().startswith(b"CMPCT24\x00")
    with CMPCT(archive) as reader:
        rows = {r[0]: r for r in reader.files}
        assert "sub" in rows and "sub/payload.bin" in rows
        assert close_ns(rows["sub"][3], STAMP_NS)
        assert close_ns(rows["sub/payload.bin"][3], STAMP_NS)
        assert reader.verify() == 1
        assert reader.read("sub/payload.bin") == PAYLOAD
        dest = tmp_path / "out"
        reader.extractall(dest, metadata=True)
        restored = dest / "sub" / "payload.bin"
        assert restored.read_bytes() == PAYLOAD
        file_ns = restored.stat().st_mtime_ns
        dir_ns = (dest / "sub").stat().st_mtime_ns

    receipt = {
        "platform": sys.platform,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "payload_sha256": hashlib.sha256(PAYLOAD).hexdigest(),
        "file_record_ns": rows["sub/payload.bin"][3],
        "dir_record_ns": rows["sub"][3],
        "file_restored_ns": file_ns,
        "dir_restored_ns": dir_ns,
        "file_error_ns": abs(file_ns - STAMP_NS),
        "dir_error_ns": abs(dir_ns - STAMP_NS),
        "read_verified": True,
    }
    _receipt("physical", receipt)
    assert close_ns(file_ns, STAMP_NS), receipt
    assert close_ns(dir_ns, STAMP_NS), receipt


def test_win32_handle_helper_regular_and_directory(tmp_path: Path) -> None:
    if sys.platform != "win32":
        with pytest.raises(NotImplementedError):
            restore_win32_leaf_mtime(tmp_path, STAMP_NS, directory=True)
        return
    directory = tmp_path / "directory"
    directory.mkdir()
    leaf = directory / "file.bin"
    leaf.write_bytes(PAYLOAD)
    restore_win32_leaf_mtime(leaf, STAMP_NS, directory=False)
    restore_win32_leaf_mtime(directory, STAMP_NS, directory=True)
    assert close_ns(leaf.stat().st_mtime_ns, STAMP_NS)
    assert close_ns(directory.stat().st_mtime_ns, STAMP_NS)
    with pytest.raises(OSError, match="changed file type"):
        restore_win32_leaf_mtime(leaf, STAMP_NS, directory=True)
    with pytest.raises(OSError, match="changed file type"):
        restore_win32_leaf_mtime(directory, STAMP_NS, directory=False)
    _receipt("helper", {"platform": sys.platform, "regular": "pass", "directory": "pass", "type_change": "refused"})


def test_win32_reparse_leaf_does_not_modify_target(tmp_path: Path) -> None:
    if sys.platform != "win32":
        pytest.skip("Win32-specific reparse-point custody")
    target = tmp_path / "external-target.bin"
    target.write_bytes(PAYLOAD)
    os.utime(target, ns=(STAMP_NS, STAMP_NS))
    link = tmp_path / "symlink.bin"
    kind = "symlink"
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        # Some hosted Windows users lack the privilege to create symlinks.
        # A directory junction is also a final-component reparse point; it
        # supplies an independently real kernel witness without weakening the
        # requirement to reject such leaves.
        import subprocess
        kind = "junction"
        target_dir = tmp_path / "external-directory"
        target_dir.mkdir()
        os.utime(target_dir, ns=(STAMP_NS, STAMP_NS))
        link = tmp_path / "directory-junction"
        proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target_dir)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, ("junction unavailable", proc.stdout, proc.stderr)
        before_ns = target_dir.stat().st_mtime_ns
        with pytest.raises(OSError):
            restore_win32_leaf_mtime(link, DIFFERENT_NS, directory=True)
        assert target_dir.stat().st_mtime_ns == before_ns
    else:
        before_ns = target.stat().st_mtime_ns
        with pytest.raises(OSError):
            restore_win32_leaf_mtime(link, DIFFERENT_NS, directory=False)
        assert link.is_symlink()
        assert target.read_bytes() == PAYLOAD
        assert target.stat().st_mtime_ns == before_ns
    _receipt("reparse", {"platform": sys.platform, "reparse_kind": kind,
                         "external_target_mtime_unchanged": True, "reparse_refused": True})
