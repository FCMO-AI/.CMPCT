from __future__ import annotations

from pathlib import Path
import os
import zipfile

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact as ZFC
from experiments import entropygraph_v030_zipfactor_eocd_parser as EOCD
from experiments import entropygraph_v030_zipfactor_fused as ZFF
from experiments import entropygraph_v030_zipfactor_profile as BASE

_DATE = (2023, 4, 5, 6, 8, 10)


def _bundle(path: Path, salt: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for member in range(3):
            info = zipfile.ZipInfo(f"member-{member}.txt", _DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            raw = "".join(
                f"row={row:04d} member={member} salt={salt} value={(row * 31337 + salt + member) % 65521}\n"
                for row in range(100 + member * 5)
            ).encode()
            zf.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def test_fused_zipfactor_scan_emits_exact_generic_filesystem_manifest(tmp_path: Path) -> None:
    root = tmp_path / "source"
    (root / "nested").mkdir(parents=True)
    for index in range(5):
        _bundle(root / "nested" / f"bundle-{index:02d}.zip", 1000 + index)

    generic_raw, _regular_sources, generic_stats = FS.capture_filesystem_manifest(
        root,
        max_path_bytes=ZFC.MAX_PATH,
        max_profile_files=ZFC.MAX_FILES,
        max_profile_logical_bytes=ZFF.MAX_LOGICAL_BYTES,
        max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
    )
    fused_raw, items, fused_stats = ZFF._scan(root)

    assert fused_raw == generic_raw
    assert fused_stats["manifest_sha256"] == generic_stats["manifest_sha256"]
    assert fused_stats["regular_graph_members"] == generic_stats["regular_graph_members"] == len(items) == 5
    assert fused_stats["logical_regular_bytes"] == generic_stats["logical_regular_bytes"]


def test_fused_zipfactor_default_eocd_parser_matches_mature_semantic_owner(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    for index in range(5):
        _bundle(root / f"bundle-{index:02d}.zip", 1500 + index)

    original_mature = BASE._parse_zip
    default_result = ZFF._scan(root)
    mature_result = ZFF._scan(root, parse_zip=BASE._parse_zip)

    assert ZFF.ZIP_PARSER.parse_zip is EOCD.parse_zip
    assert BASE._parse_zip is original_mature
    assert default_result == mature_result


def test_fused_zipfactor_build_verifies_with_compact_reader(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    for index in range(7):
        _bundle(root / f"bundle-{index:02d}.zip", 2000 + index)
    archive = tmp_path / "candidate.cmpct"

    stats = ZFF.build(root, archive, level=6, group_size=7)
    verified = ZFC.verify_and_identities(archive)

    assert stats["fused_source_scan"] is True
    assert stats["format_profile"] == ZFC.PROFILE
    assert verified["ok"] is True
    assert verified["verified_user_files"] == 7
    assert verified["max_member_read_amplification"] <= ZFC.MAX_AMP
    assert verified["max_decode_unit_bytes"] <= ZFC.MAX_DECODE


def test_fused_zipfactor_manifest_parity_preserves_symlink_and_directory_metadata(tmp_path: Path) -> None:
    root = tmp_path / "source"
    (root / "payload").mkdir(parents=True)
    for index in range(3):
        _bundle(root / "payload" / f"bundle-{index:02d}.zip", 3000 + index)
    try:
        os.symlink("payload/bundle-00.zip", root / "alias.zip")
    except (OSError, NotImplementedError):
        return

    generic_raw, _sources, _stats = FS.capture_filesystem_manifest(
        root,
        max_path_bytes=ZFC.MAX_PATH,
        max_profile_files=ZFC.MAX_FILES,
        max_profile_logical_bytes=ZFF.MAX_LOGICAL_BYTES,
        max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
    )
    fused_raw, items, _fused_stats = ZFF._scan(root)

    assert fused_raw == generic_raw
    assert len(items) == 3


def test_fused_zipfactor_rejects_non_zip_graph_owned_regular_file(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    _bundle(root / "bundle.zip", 4000)
    (root / "ordinary.bin").write_bytes(b"not a ZIP family")

    import pytest
    with pytest.raises(ZFF.ProfileNotEligible, match="must all be ZIPs"):
        ZFF._scan(root)
