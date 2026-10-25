"""O102 source-exact O69 Reader timestamp restoration, truthful negative-science court.

The Windows case intentionally PASSES only if the verified r24 archive yields correct
logical bytes but a wrong physical mtime with metadata=True. That is a negative
product finding, not a product pass. Never weaken an inherited correctness gate.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from cmpct.core import Builder, CMPCT

STAMP_NS = 1_580_643_296_000_000_000  # fixed UTC in 2020, far from CI's current clock
TOLERANCE_NS = 3_000_000_000
MIN_BAD_GAP_NS = 365 * 24 * 3600 * 1_000_000_000
PAYLOAD = b"o102 source-authenticated payload\x00\xff" * 101


def _close(a: int, b: int) -> bool:
    return abs(a - b) <= TOLERANCE_NS


def test_host_physically_supports_explicit_file_and_directory_mtime(tmp_path: Path):
    directory = tmp_path / "parent"
    directory.mkdir()
    leaf = directory / "member.bin"
    leaf.write_bytes(PAYLOAD)
    os.utime(leaf, ns=(STAMP_NS, STAMP_NS))
    os.utime(directory, ns=(STAMP_NS, STAMP_NS))
    assert _close(leaf.stat().st_mtime_ns, STAMP_NS), "host cannot represent source file timestamp"
    assert _close(directory.stat().st_mtime_ns, STAMP_NS), "host cannot represent directory timestamp"


def test_installed_r24_reader_reports_success_but_win32_loses_mtime(tmp_path: Path):
    src = tmp_path / "source"
    sub = src / "sub"
    sub.mkdir(parents=True)
    member = sub / "payload.bin"
    member.write_bytes(PAYLOAD)
    # Normalize after all child writes; child creation changes directory mtime.
    os.utime(member, ns=(STAMP_NS, STAMP_NS))
    os.utime(sub, ns=(STAMP_NS, STAMP_NS))
    assert _close(member.stat().st_mtime_ns, STAMP_NS)
    assert _close(sub.stat().st_mtime_ns, STAMP_NS)

    archive = tmp_path / "real-r24.cmpct"
    Builder(src, workers=1).build(archive)
    assert archive.read_bytes().startswith(b"CMPCT24\\0".replace(b"\\0", b"\x00"))
    with CMPCT(archive) as reader:
        rows = {row[0]: row for row in reader.files}
        assert "sub" in rows and "sub/payload.bin" in rows, rows.keys()
        assert _close(int(rows["sub"][3]), STAMP_NS), rows["sub"]
        assert _close(int(rows["sub/payload.bin"][3]), STAMP_NS), rows["sub/payload.bin"]
        assert reader.verify() == 1
        assert reader.read("sub/payload.bin") == PAYLOAD

        dest = tmp_path / "extracted"
        # The exact public default metadata=True behavior; no workaround metadata=False.
        reader.extractall(dest, metadata=True)
        extracted = dest / "sub" / "payload.bin"
        extracted_dir = dest / "sub"
        assert extracted.read_bytes() == PAYLOAD
        file_ns = extracted.stat().st_mtime_ns
        dir_ns = extracted_dir.stat().st_mtime_ns

    result = {
        "platform": sys.platform,
        "source_sha256": hashlib.sha256(PAYLOAD).hexdigest(),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "file_recorded_ns": int(rows["sub/payload.bin"][3]),
        "dir_recorded_ns": int(rows["sub"][3]),
        "file_extracted_ns": int(file_ns),
        "dir_extracted_ns": int(dir_ns),
        "file_delta_s": abs(int(file_ns) - STAMP_NS) / 1e9,
        "dir_delta_s": abs(int(dir_ns) - STAMP_NS) / 1e9,
        "reader_verify": "pass",
        "byte_reconstruction": "pass",
    }
    artifact = os.environ.get("O102_RECEIPT_DIR")
    if artifact:
        Path(artifact).mkdir(parents=True, exist_ok=True)
        (Path(artifact) / "source-physical-mtime.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("O102_REAL_FILESYSTEM_RESULT=" + json.dumps(result, sort_keys=True), flush=True)

    if sys.platform == "win32":
        # This is the prospective adverse verdict. Even though Reader returns
        # successfully, its no-follow utime fallback has lost both timestamp fields.
        assert abs(file_ns - STAMP_NS) > MIN_BAD_GAP_NS, result
        assert abs(dir_ns - STAMP_NS) > MIN_BAD_GAP_NS, result
    else:
        # Positive same-archive control where Python supports no-follow utime.
        assert _close(file_ns, STAMP_NS), result
        assert _close(dir_ns, STAMP_NS), result

    # Independently demonstrate the Windows host *can* represent the recorded mtime.
    # This explicit path-following operation is only a laboratory control on a
    # disposable known-regular file, NOT a recommended Reader fallback.
    os.utime(extracted, ns=(STAMP_NS, STAMP_NS))
    os.utime(extracted_dir, ns=(STAMP_NS, STAMP_NS))
    assert _close(extracted.stat().st_mtime_ns, STAMP_NS)
    assert _close(extracted_dir.stat().st_mtime_ns, STAMP_NS)
