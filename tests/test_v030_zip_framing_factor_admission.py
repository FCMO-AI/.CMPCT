from __future__ import annotations

from pathlib import Path
import zipfile

from benchmarks import v030_zip_framing_factor_oracle as ZFF

_DATE = (2020, 1, 1, 0, 0, 0)


def _write_bundle(path: Path, *, salt: int, drift_name: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for member in range(4):
            name = f"member-{member:02d}.txt"
            if drift_name and member == 3:
                name = "different-name.txt"
            info = zipfile.ZipInfo(name, _DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            rows = [
                f"row={i:04d} member={member} salt={salt} value={(i * 131 + member * 17 + salt) % 65521:05d}\n"
                for i in range(120 + member * 7)
            ]
            zf.writestr(info, "".join(rows).encode(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def _unseen_family(root: Path, *, count: int = 5) -> None:
    for bundle in range(count):
        _write_bundle(root / f"bundle-{bundle:02d}.zip", salt=100 + bundle)


def test_zip_framing_factor_admits_unseen_structurally_identical_family(tmp_path: Path) -> None:
    _unseen_family(tmp_path)

    items, _parse_s, reject = ZFF._parse_sources(tmp_path)

    assert reject is None
    assert items is not None
    assert len(items) == 5
    assert all(len(item["locals"]) == 4 for _rel, item in items)


def test_zip_framing_factor_round_trips_unseen_family_with_bounded_locality(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _unseen_family(source, count=6)
    items, parse_s, reject = ZFF._parse_sources(source)
    assert reject is None
    assert items is not None

    candidate = tmp_path / "candidate.zff"
    result = ZFF._build_candidate(items, group_size=3, level=3, archive=candidate, parse_s=parse_s)

    assert result["all_zip_bytes_exact"] is True
    assert result["tree_verified"] is True
    assert result["locality_green"] is True
    assert float(result["max_member_read_amplification"]) <= ZFF.MAX_AMP
    assert int(result["max_decode_unit_bytes"]) <= ZFF.MAX_DECODE


def test_zip_framing_factor_rejects_framing_name_drift(tmp_path: Path) -> None:
    for bundle in range(4):
        _write_bundle(
            tmp_path / f"bundle-{bundle:02d}.zip",
            salt=200 + bundle,
            drift_name=bundle == 3,
        )

    items, _parse_s, reject = ZFF._parse_sources(tmp_path)

    assert items is None
    assert reject is not None
    assert reject.startswith("framing-layout-drift:")


def test_zip_framing_factor_rejects_non_zip_tree(tmp_path: Path) -> None:
    _write_bundle(tmp_path / "bundle.zip", salt=300)
    (tmp_path / "ordinary.bin").write_bytes(b"not a zip family")

    items, _parse_s, reject = ZFF._parse_sources(tmp_path)

    assert items is None
    assert reject == "not-all-zip"
