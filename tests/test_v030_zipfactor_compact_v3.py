from __future__ import annotations

from pathlib import Path
import zipfile

from experiments import entropygraph_v030_zipfactor_compact_v3 as ZF3

_DATE = (2020, 1, 1, 0, 0, 0)


def _write_bundle(path: Path, *, salt: int, drift: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for member in range(4):
            name = f"member-{member:02d}.txt"
            if drift and member == 3:
                name = "drifted-name.txt"
            info = zipfile.ZipInfo(name, _DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            rows = [
                f"row={row:04d} member={member} salt={salt} value={(row * 131 + member * 17 + salt) % 65521:05d}\n"
                for row in range(120 + member * 7)
            ]
            zf.writestr(info, "".join(rows).encode(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def _family(root: Path, *, count: int = 7) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for bundle in range(count):
        _write_bundle(root / f"bundle-{bundle:02d}.zip", salt=700 + bundle)


def test_binary_control_profile_round_trips_exact_zip_family(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _family(source)
    archive = tmp_path / "candidate.cmpct"

    stats = ZF3.build(source, archive, level=6, group_size=4)
    verified = ZF3.verify_and_identities(archive)

    assert verified["ok"] is True
    assert verified["format_revision"] == 25
    assert verified["format_profile"] == ZF3.PROFILE
    assert verified["verified_user_files"] == 7
    assert float(verified["max_member_read_amplification"]) <= 8.0
    assert int(verified["max_decode_unit_bytes"]) <= 8 * 1024 * 1024
    assert stats["control_bytes"] < 512
    for path in sorted(source.glob("*.zip")):
        rel = path.name
        size, digest = verified["identities"][rel]
        assert size == path.stat().st_size
        import hashlib
        assert digest == hashlib.sha256(path.read_bytes()).digest()


def test_binary_control_profile_corruption_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _family(source)
    archive = tmp_path / "candidate.cmpct"
    ZF3.build(source, archive, group_size=4)
    raw = bytearray(archive.read_bytes())
    raw[-1] ^= 0x5A
    archive.write_bytes(raw)

    verified = ZF3.strong_verify(archive)

    assert verified["ok"] is False


def test_binary_control_profile_rejects_framing_drift(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for bundle in range(4):
        _write_bundle(source / f"bundle-{bundle:02d}.zip", salt=900 + bundle, drift=bundle == 3)

    archive = tmp_path / "candidate.cmpct"
    try:
        ZF3.build(source, archive)
    except Exception as exc:
        assert "framing layout drift" in str(exc)
    else:
        raise AssertionError("framing drift must fail closed")


def test_binary_control_profile_rejects_non_zip_regular_file(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_bundle(source / "bundle-00.zip", salt=1000)
    _write_bundle(source / "bundle-01.zip", salt=1001)
    (source / "ordinary.bin").write_bytes(b"not a zip")

    try:
        ZF3.build(source, tmp_path / "candidate.cmpct")
    except Exception as exc:
        assert "must all be ZIPs" in str(exc)
    else:
        raise AssertionError("mixed regular-file trees must fail closed")
