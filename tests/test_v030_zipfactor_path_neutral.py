from __future__ import annotations

import copy
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

    # Ratchet the semantic rejection reason without coupling the test to incidental wording: admission is based on
    # parseable ZIP structure, never the filename suffix.
    with pytest.raises(ZF.ProfileNotEligible, match=r"supported .*structur"):
        ZF._scan(source)


def test_direct_signature_comparator_matches_mature_signature_law(tmp_path):
    source = tmp_path / "source.zip"
    _zip(source, b"A" * 256)
    reference = ZF.ZIP_PARSER.parse_zip(source.read_bytes())
    assert reference is not None

    # The mature signature intentionally excludes per-file dynamics. The allocation-free comparator must do exactly
    # the same: changing CRC/sizes/payload/local physical offset is legal framing reuse, not structural drift.
    dynamic = copy.deepcopy(reference)
    dynamic["locals"][0]["crc"] ^= 1
    dynamic["locals"][0]["csize"] += 1
    dynamic["locals"][0]["usize"] += 1
    dynamic["locals"][0]["payload"] += b"x"
    dynamic["locals"][0]["offset"] += 1
    dynamic["centrals"][0]["crc"] ^= 1
    dynamic["centrals"][0]["csize"] += 1
    dynamic["centrals"][0]["usize"] += 1
    dynamic["centrals"][0]["local_offset"] += 1
    assert ZF.BASE._signature(reference) == ZF.BASE._signature(dynamic)
    assert ZF._same_framing_signature(reference, dynamic) is True

    # Every field actually owned by BASE._signature remains an exact, collision-free admission condition.
    for section, field in (
        ("locals", "method"),
        ("locals", "name"),
        ("centrals", "made"),
        ("centrals", "comment"),
    ):
        changed = copy.deepcopy(reference)
        row = changed[section][0]
        value = row[field]
        row[field] = value + b"x" if isinstance(value, bytes) else int(value) + 1
        assert ZF.BASE._signature(reference) != ZF.BASE._signature(changed)
        assert ZF._same_framing_signature(reference, changed) is False

    changed_eocd = copy.deepcopy(reference)
    changed_eocd["eocd"]["comment"] += b"x"
    assert ZF.BASE._signature(reference) != ZF.BASE._signature(changed_eocd)
    assert ZF._same_framing_signature(reference, changed_eocd) is False
