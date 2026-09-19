from __future__ import annotations

import copy
import zipfile

from benchmarks import v030_zipfactor_signature_compare_abba as AB
from experiments import entropygraph_v030_zipfactor_fused as ZF


def _zip(path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("same/member.txt", b"A" * 256)


def _changed(value):
    if isinstance(value, bytes):
        return value + b"x"
    if isinstance(value, str):
        return value + "x"
    return int(value) + 1


def _assert_same_law(reference: dict, candidate: dict) -> None:
    assert AB._itemgetter_same_signature(reference, candidate) is ZF._same_framing_signature(reference, candidate)


def test_itemgetter_candidate_matches_shipping_signature_law_for_every_owned_field(tmp_path):
    source = tmp_path / "source.zip"
    _zip(source)
    reference = ZF.ZIP_PARSER.parse_zip(source.read_bytes())
    assert reference is not None
    _assert_same_law(reference, copy.deepcopy(reference))

    # Exhaust every field owned by the admission signature, not just a representative sample.
    for field in ZF._LOCAL_SIGNATURE_FIELDS:
        changed = copy.deepcopy(reference)
        changed["locals"][0][field] = _changed(changed["locals"][0][field])
        _assert_same_law(reference, changed)
        assert AB._itemgetter_same_signature(reference, changed) is False

    for field in ZF._CENTRAL_SIGNATURE_FIELDS:
        changed = copy.deepcopy(reference)
        changed["centrals"][0][field] = _changed(changed["centrals"][0][field])
        _assert_same_law(reference, changed)
        assert AB._itemgetter_same_signature(reference, changed) is False

    for field in ZF._EOCD_SIGNATURE_FIELDS:
        changed = copy.deepcopy(reference)
        changed["eocd"][field] = _changed(changed["eocd"][field])
        _assert_same_law(reference, changed)
        assert AB._itemgetter_same_signature(reference, changed) is False


def test_itemgetter_candidate_preserves_dynamic_field_exclusions_and_length_rejection(tmp_path):
    source = tmp_path / "source.zip"
    _zip(source)
    reference = ZF.ZIP_PARSER.parse_zip(source.read_bytes())
    assert reference is not None

    dynamic = copy.deepcopy(reference)
    for section, fields in (
        ("locals", ("crc", "csize", "usize", "payload", "offset")),
        ("centrals", ("crc", "csize", "usize", "local_offset")),
    ):
        for field in fields:
            dynamic[section][0][field] = _changed(dynamic[section][0][field])
    _assert_same_law(reference, dynamic)
    assert AB._itemgetter_same_signature(reference, dynamic) is True

    fewer_locals = copy.deepcopy(reference)
    fewer_locals["locals"] = []
    _assert_same_law(reference, fewer_locals)
    assert AB._itemgetter_same_signature(reference, fewer_locals) is False

    fewer_centrals = copy.deepcopy(reference)
    fewer_centrals["centrals"] = []
    _assert_same_law(reference, fewer_centrals)
    assert AB._itemgetter_same_signature(reference, fewer_centrals) is False
