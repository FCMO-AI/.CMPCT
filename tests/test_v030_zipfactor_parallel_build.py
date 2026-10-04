from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_parallel_build as PAR


def _write_family(root: Path, count: int = 8) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        path = root / f"bundle-{i:02d}.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            # Identical archive structure, changing payloads: the intended framing-factor admission shape.
            zf.writestr("alpha.txt", ("alpha-%02d-" % i) * 80)
            zf.writestr("beta.txt", ("beta-%02d-" % i) * 120)


def test_parallel_builder_is_exactly_byte_identical(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _write_family(src)
    serial = tmp_path / "serial.cmpct"
    parallel = tmp_path / "parallel.cmpct"

    serial_stats = V3.build(src, serial, level=3, group_size=4)
    parallel_stats = PAR.build(src, parallel, level=3, group_size=4, workers=4)

    assert serial.read_bytes() == parallel.read_bytes()
    assert serial_stats["archive_bytes"] == parallel_stats["archive_bytes"]
    assert parallel_stats["scheduling_only"] is True
    assert 1 < parallel_stats["compression_workers"] <= 4
    assert parallel_stats["compression_jobs"] >= 4

    serial_verify = V3.verify_and_identities(serial)
    parallel_verify = V3.verify_and_identities(parallel)
    assert serial_verify["ok"] is True
    assert parallel_verify["ok"] is True
    assert serial_verify["identities"] == parallel_verify["identities"]
    assert parallel_verify["max_member_read_amplification"] <= 8.0
    assert parallel_verify["max_decode_unit_bytes"] <= 8 * 1024 * 1024


def test_parallel_builder_fails_closed_on_worker_overflow(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _write_family(src, count=4)
    with pytest.raises(V3.ProfileNotEligible, match="worker count"):
        PAR.build(src, tmp_path / "bad.cmpct", workers=5)
