from __future__ import annotations

from pathlib import Path
import zipfile

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_profile as ZF
from experiments import entropygraph_v030_zipfactor_session as ZFS

_DATE = (2022, 3, 4, 5, 6, 8)


def _bundle(path: Path, salt: int) -> bytes:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for member in range(4):
            info = zipfile.ZipInfo(f"member-{member:02d}.txt", _DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            raw = "".join(
                f"row={row:04d} member={member} salt={salt} value={(row * 911 + salt + member) % 65521}\n"
                for row in range(140 + member * 9)
            ).encode()
            zf.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return path.read_bytes()


def test_one_pass_zipfactor_session_returns_exact_identities(tmp_path: Path) -> None:
    staged = tmp_path / "staged"
    staged.mkdir()
    manifest = b"session-manifest-fixture"
    manifest_path = staged / FS.FILESYSTEM_MANIFEST
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(manifest)
    expected = {FS.FILESYSTEM_MANIFEST: manifest}
    for index in range(7):
        rel = f"bundle-{index:02d}.zip"
        expected[rel] = _bundle(staged / rel, 700 + index)

    archive = tmp_path / "candidate.cmpct"
    ZF.build(staged, archive, level=1, group_size=7)
    result = ZFS.verify_and_identities(archive)

    assert result["ok"] is True
    assert result["verified_user_files"] == 7
    assert result["verified_content_members"] == 8
    assert result["max_member_read_amplification"] <= ZF.MAX_AMP
    assert result["max_decode_unit_bytes"] <= ZF.MAX_DECODE
    assert result["manifest_raw"] == manifest
    for rel, raw in expected.items():
        size, digest = result["identities"][rel]
        assert size == len(raw)
        import hashlib
        assert digest == hashlib.sha256(raw).digest()


def test_one_pass_zipfactor_session_fails_closed_on_corruption(tmp_path: Path) -> None:
    staged = tmp_path / "staged"
    staged.mkdir()
    manifest_path = staged / FS.FILESYSTEM_MANIFEST
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(b"manifest")
    for index in range(3):
        _bundle(staged / f"bundle-{index:02d}.zip", 900 + index)
    archive = tmp_path / "candidate.cmpct"
    ZF.build(staged, archive, level=1, group_size=3)
    raw = bytearray(archive.read_bytes())
    raw[-3] ^= 0x01
    archive.write_bytes(raw)
    assert ZFS.strong_verify(archive)["ok"] is False
