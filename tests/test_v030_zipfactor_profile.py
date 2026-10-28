from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_profile as ZF

_DATE = (2021, 2, 3, 4, 6, 8)


def _bundle(path: Path, salt: int, *, drift: bool = False) -> bytes:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for member in range(5):
            name = f"member-{member:02d}.txt" if not (drift and member == 4) else "drift.txt"
            info = zipfile.ZipInfo(name, _DATE); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            raw = "".join(
                f"row={row:04d} member={member} salt={salt} value={(row * 313 + salt * 17 + member) % 104729}\n"
                for row in range(180 + member * 11)
            ).encode()
            zf.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return path.read_bytes()


def _staged(root: Path, *, count: int = 6) -> dict[str, bytes]:
    root.mkdir(parents=True)
    manifest = b"canonical-filesystem-manifest-fixture-v1"
    manifest_path = root / FS.FILESYSTEM_MANIFEST; manifest_path.parent.mkdir(parents=True); manifest_path.write_bytes(manifest)
    expected = {FS.FILESYSTEM_MANIFEST: manifest}
    for index in range(count):
        rel = f"bundle-{index:02d}.zip"; expected[rel] = _bundle(root / rel, 500 + index)
    return expected


def test_zipfactor_profile_builds_and_selectively_restores_exact_members(tmp_path: Path) -> None:
    staged = tmp_path / "staged"; expected = _staged(staged)
    archive = tmp_path / "candidate.cmpct"

    stats = ZF.build(staged, archive, level=1, group_size=3)

    assert archive.read_bytes()[:8] == ZF.MAGIC
    assert stats["format_revision"] == 25
    assert stats["format_profile"] == ZF.PROFILE
    assert stats["max_decode_unit_bytes"] <= ZF.MAX_DECODE
    assert stats["max_member_read_amplification"] <= ZF.MAX_AMP
    for rel, raw in expected.items():
        restored, read_stats = ZF.read_member_with_stats(archive, rel)
        assert restored == raw
        assert read_stats["decoded_context_amplification"] <= ZF.MAX_AMP
    verified = ZF.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["verified_files"] == len(expected)


def test_zipfactor_profile_rejects_layout_drift_before_publication(tmp_path: Path) -> None:
    staged = tmp_path / "staged"; _staged(staged, count=3)
    _bundle(staged / "bundle-02.zip", 999, drift=True)
    with pytest.raises(ZF.ProfileNotEligible, match="layout drift"):
        ZF.build(staged, tmp_path / "candidate.cmpct")


def test_zipfactor_profile_detects_authenticated_payload_corruption(tmp_path: Path) -> None:
    staged = tmp_path / "staged"; _staged(staged)
    archive = tmp_path / "candidate.cmpct"; ZF.build(staged, archive, level=1, group_size=3)
    raw = bytearray(archive.read_bytes()); raw[-7] ^= 0x40; archive.write_bytes(raw)
    assert ZF.strong_verify(archive)["ok"] is False


def test_zipfactor_profile_rejects_non_zip_regular_member(tmp_path: Path) -> None:
    staged = tmp_path / "staged"; _staged(staged, count=3)
    (staged / "ordinary.bin").write_bytes(b"ordinary")
    with pytest.raises(ZF.ProfileNotEligible, match="only ZIP"):
        ZF.build(staged, tmp_path / "candidate.cmpct")
