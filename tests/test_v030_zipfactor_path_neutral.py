from __future__ import annotations

import shutil
import zipfile

import pytest

from experiments import entropygraph_v030_zipfactor_fused as ZF


def _zip(path, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("same/member.txt", payload)


def test_extensionless_structural_zip_members_are_admitted(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    first = source / "alpha.data"
    second = source / "beta"
    _zip(first, b"A" * 256)
    shutil.copyfile(first, second)

    _manifest, items, stats = ZF._scan(source)

    assert [name for name, _parsed in items] == ["alpha.data", "beta"]
    assert stats["regular_graph_members"] == 2
    assert stats["admission"] == "supported-zip-structure+shared-framing-signature-v1"
    assert stats["path_identity_used_for_admission"] is False


def test_misleading_zip_suffix_cannot_admit_non_zip_bytes(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _zip(source / "valid.bin", b"A" * 256)
    (source / "looks-valid.zip").write_bytes(b"not a zip archive")

    with pytest.raises(ZF.ProfileNotEligible, match="supported ZIP structure"):
        ZF._scan(source)
