from __future__ import annotations

import gzip
import os
from pathlib import Path
import stat

import pytest

from experiments import entropygraph_v030_logs_inverse_profile_v3 as PROFILE


def _source(root: Path) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True)
    os.chmod(logs, 0o750)
    plain = (b"event=alpha status=ok\n" * 4096) + (b"event=beta status=warn\n" * 2048)
    owner = logs / "a.log"
    owner.write_bytes(plain)
    os.chmod(owner, 0o640)
    (logs / "a.log.gz").write_bytes(gzip.compress(plain, compresslevel=6, mtime=0))
    (logs / "unmatched.log").write_bytes(b"unmatched\n" * 8192)
    os.link(owner, logs / "b-hard.log")
    try:
        os.symlink("a.log", logs / "latest")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this platform")


def test_logs_v3_roundtrips_canonical_filesystem_semantics(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _source(source)
    archive = tmp_path / "candidate.cmpct"

    stats = PROFILE.build(source, archive)
    assert stats["profile_writer_revision"] == 3
    assert stats["canonical_filesystem_manifest"] is True
    assert stats["filesystem_manifest_bytes"] > 0

    verified = PROFILE.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["canonical_filesystem_manifest"] is True
    assert verified["max_member_read_amplification"] <= 8.0
    assert verified["max_decode_unit_bytes"] <= 8 * 1024 * 1024

    restored = tmp_path / "restored"
    PROFILE.extract(archive, restored)
    assert (restored / "logs/a.log").read_bytes() == (source / "logs/a.log").read_bytes()
    assert (restored / "logs/a.log.gz").read_bytes() == (source / "logs/a.log.gz").read_bytes()
    assert (restored / "logs/unmatched.log").read_bytes() == (source / "logs/unmatched.log").read_bytes()
    assert (restored / "logs/latest").is_symlink()
    assert os.readlink(restored / "logs/latest") == "a.log"
    assert os.stat(restored / "logs/a.log").st_ino == os.stat(restored / "logs/b-hard.log").st_ino
    assert stat.S_IMODE(os.stat(restored / "logs").st_mode) == 0o750
    assert stat.S_IMODE(os.stat(restored / "logs/a.log").st_mode) == 0o640


def test_logs_v3_roundtrips_signed_pre_epoch_mtime(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _source(source)
    owner = source / "logs/a.log"
    pre_epoch_ns = -1_000_000_000
    try:
        os.utime(owner, ns=(pre_epoch_ns, pre_epoch_ns))
    except OSError:
        pytest.skip("filesystem does not support pre-epoch nanosecond timestamps")
    if owner.stat().st_mtime_ns >= 0:
        pytest.skip("filesystem clamps pre-epoch timestamps")

    archive = tmp_path / "pre-epoch.cmpct"
    PROFILE.build(source, archive)
    verified = PROFILE.strong_verify(archive)
    assert verified["ok"] is True

    restored = tmp_path / "restored"
    PROFILE.extract(archive, restored)
    assert (restored / "logs/a.log").stat().st_mtime_ns == owner.stat().st_mtime_ns


def test_logs_v3_rejects_unsafe_symlink_on_restore(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    logs = source / "logs"
    logs.mkdir()
    (logs / "a.log").write_bytes(b"safe\n" * 4096)
    try:
        os.symlink("../../escape", logs / "unsafe")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this platform")

    archive = tmp_path / "candidate.cmpct"
    PROFILE.build(source, archive)
    with pytest.raises(RuntimeError, match="unsafe r25 symlink target"):
        PROFILE.extract(archive, tmp_path / "restored")
