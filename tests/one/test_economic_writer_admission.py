from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import (
    build_general_law_archive,
    economically_admit_law,
    predicted_law_complete_delta_bytes,
)


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _write_relation(root: Path, relation: str, length: int) -> None:
    root.mkdir()
    source = _hash_stream(length, f"test-economic-{relation}-{length}".encode())
    if relation == "add8":
        target = bytes(((value + 37) & 0xFF) for value in source)
    elif relation == "xor":
        target = bytes((value ^ 0xA5) for value in source)
    else:
        raise KeyError(relation)
    (root / "00-source.bin").write_bytes(source)
    (root / "01-target.bin").write_bytes(target)


def _target_op(wire: bytes) -> str:
    opened = open_authenticated_archive(wire)
    entry = opened.base.entries["01-target.bin"]
    root = opened.program.roots[entry["root"]]
    return opened.program.nodes[root.ref.node].op


def test_frozen_model_break_even_is_representation_cost_not_lookup_table() -> None:
    assert predicted_law_complete_delta_bytes("add8", 10) == 1
    assert predicted_law_complete_delta_bytes("add8", 11) == 0
    assert predicted_law_complete_delta_bytes("xor", 12) == -1
    assert predicted_law_complete_delta_bytes("fill", 1) == 0
    assert predicted_law_complete_delta_bytes("exact_reuse", 0) == -3
    assert not economically_admit_law("add8", 10)
    assert economically_admit_law("add8", 11)
    assert economically_admit_law("xor", 11)
    assert economically_admit_law("fill", 1)


def test_marginal_model_rejects_unknown_relation_and_negative_length() -> None:
    with pytest.raises(Exception):
        predicted_law_complete_delta_bytes("legacy_codec", 32)
    with pytest.raises(Exception):
        predicted_law_complete_delta_bytes("add8", -1)


def test_tiny_add8_rejection_becomes_surprise_and_avoids_exact_proof(tmp_path: Path) -> None:
    root = tmp_path / "tiny-add8"
    _write_relation(root, "add8", 8)
    current, current_stats = build_general_law_archive(root)
    economic, economic_stats = build_general_law_archive(root, economic_admission=True)
    assert _target_op(current) == "add8"
    assert _target_op(economic) == "surprise"
    assert len(economic) < len(current)
    assert economic_stats.discovery_exact_proof_bytes < current_stats.discovery_exact_proof_bytes
    assert open_authenticated_archive(economic).read_file("01-target.bin") == (root / "01-target.bin").read_bytes()


def test_break_even_add8_is_preserved_as_same_generic_law(tmp_path: Path) -> None:
    root = tmp_path / "break-even-add8"
    _write_relation(root, "add8", 11)
    current, current_stats = build_general_law_archive(root)
    economic, economic_stats = build_general_law_archive(root, economic_admission=True)
    assert _target_op(current) == "add8"
    assert _target_op(economic) == "add8"
    assert current == economic
    assert current_stats == economic_stats


def test_profitable_xor_is_preserved_wire_identically(tmp_path: Path) -> None:
    root = tmp_path / "profitable-xor"
    _write_relation(root, "xor", 32)
    current, current_stats = build_general_law_archive(root)
    economic, economic_stats = build_general_law_archive(root, economic_admission=True)
    assert _target_op(current) == "xor"
    assert _target_op(economic) == "xor"
    assert current == economic
    assert current_stats == economic_stats


def test_default_writer_policy_remains_unchanged(tmp_path: Path) -> None:
    root = tmp_path / "default-policy"
    _write_relation(root, "add8", 8)
    implicit, implicit_stats = build_general_law_archive(root)
    explicit, explicit_stats = build_general_law_archive(root, economic_admission=False)
    assert implicit == explicit
    assert implicit_stats == explicit_stats
    assert _target_op(implicit) == "add8"
