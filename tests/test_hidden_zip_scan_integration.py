from __future__ import annotations

import os
import random
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import S_BLOB, S_PACK, S_VZIP
import cmpct.v030_hidden_zip_builder as scan_seam


def _write_zip(path: Path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload.bin", payload)


def _rows(builder: Builder) -> dict[str, list]:
    return {row[0]: row for row in builder.files}


def _explicit_set(root: Path, count: int) -> bytes:
    # Deterministic high-entropy content keeps the exact shared Deflate stream comfortably above the
    # 2176-byte economic reuse floor; the test therefore exercises ownership rather than tiny-stream
    # rejection.
    shared = random.Random(0xC0DEC7).randbytes(32 * 1024)
    for i in range(count):
        payload = shared if i == 0 else random.Random(i + 100).randbytes(8 * 1024)
        _write_zip(root / f"explicit-{i}.zip", payload)
    return (root / "explicit-0.zip").read_bytes()


def test_scan_seven_explicit_plus_hidden_preserves_threshold_and_can_admit(tmp_path: Path) -> None:
    hidden_bytes = _explicit_set(tmp_path, 7)
    (tmp_path / "hidden.docx").write_bytes(hidden_bytes)
    b = Builder(tmp_path); b.scan(); rows = _rows(b)
    assert all(rows[f"explicit-{i}.zip"][6][0] == S_VZIP for i in range(7))
    assert rows["hidden.docx"][6][0] == S_VZIP
    assert sum(row[6][0] == S_PACK for row in rows.values() if row[6]) == 0


def test_scan_eight_explicit_plus_hidden_preserves_spack_and_denies_subsidy(tmp_path: Path) -> None:
    hidden_bytes = _explicit_set(tmp_path, 8)
    (tmp_path / "hidden.docx").write_bytes(hidden_bytes)
    b = Builder(tmp_path); b.scan(); rows = _rows(b)
    assert all(rows[f"explicit-{i}.zip"][6][0] == S_PACK for i in range(8))
    assert rows["hidden.docx"][6][0] == S_BLOB
    assert rows["hidden.docx"][4] == len(hidden_bytes)
    assert rows["hidden.docx"][5] is not None


def test_scan_cohort_overflow_disables_whole_optional_lane_before_second_record(tmp_path: Path, monkeypatch) -> None:
    first = tmp_path / "a.docx"; second = tmp_path / "b.docx"
    _write_zip(first, random.Random(1).randbytes(8 * 1024))
    _write_zip(second, random.Random(2).randbytes(8 * 1024))
    monkeypatch.setattr(scan_seam, "MAX_OBSERVATION_FILES", 1)

    def must_not_optimize(*_args, **_kwargs):
        raise AssertionError("overflowed hidden cohort must not enter proof/finalization")
    monkeypatch.setattr(scan_seam, "finalize_deferred_hidden_files", must_not_optimize)

    b = Builder(tmp_path); b.scan(); rows = _rows(b)
    assert rows["a.docx"][6][0] == S_BLOB
    assert rows["b.docx"][6][0] == S_BLOB


def test_non_pk_ordinary_blob_path_is_unchanged(tmp_path: Path) -> None:
    raw = b"ordinary bytes that are not a zip" * 128
    (tmp_path / "ordinary.bin").write_bytes(raw)
    b = Builder(tmp_path); b.scan(); row = _rows(b)["ordinary.bin"]
    assert row[6][0] == S_BLOB
    assert b.cands[bytes(row[6][1])].raw == raw


def test_hidden_candidate_reproducible_mtime_normalizes_after_finalization(tmp_path: Path) -> None:
    hidden_bytes = _explicit_set(tmp_path, 7)
    p = tmp_path / "hidden.docx"; p.write_bytes(hidden_bytes)
    os.utime(p, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
    epoch = 123_000_000_000
    b = Builder(tmp_path, reproducible=True, reproducible_epoch_ns=epoch); b.scan(); rows = _rows(b)
    assert rows["hidden.docx"][6][0] == S_VZIP
    assert all(row[3] == epoch for row in rows.values())
