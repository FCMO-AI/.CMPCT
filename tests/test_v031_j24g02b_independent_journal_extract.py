"""Physical extraction witness for independently frozen r24 signed journal generations.

J24G02b is prospective under its separate preregistration. This test *consumes*
the J24G01 fixture; it never reconstructs or re-signs an archive with CMPCT's
Writer or Builder. Exact disk paths and SHA-256 are the external oracle.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from cmpct.reader import CMPCT


FIXTURE = Path(__file__).parent / "conformance" / "v24-committed-journal.json"
CASES = (
    ("base", "base"),
    ("committed", "latest"),
    ("corrupt_successor", "latest"),
    ("incomplete_successor", "latest"),
)


def _fixed_archive(variant: str) -> tuple[bytes, dict[str, dict[str, str]]]:
    oracle = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert oracle["schema"] == "cmpct-v24-independent-committed-journal-v1"
    encoded = oracle["segments"]
    pieces = {
        key: base64.b64decode(data, validate=True) for key, data in encoded.items()
    }
    base = pieces["base"]
    committed = base + pieces["committed_delta"]
    archives = {
        "base": base,
        "committed": committed,
        "corrupt_successor": committed + pieces["invalid_successor"],
        "incomplete_successor": committed + pieces["incomplete_successor"],
    }
    archive = archives[variant]
    receipt = oracle["archives"][variant]
    assert len(archive) == receipt["bytes"]
    assert hashlib.sha256(archive).hexdigest() == receipt["sha256"]
    generation = "base" if variant == "base" else "latest"
    return archive, oracle["expected"][generation]


@pytest.mark.parametrize(("variant", "expected_generation"), CASES)
def test_independent_signed_journal_extractall_exact_physical_tree(
    tmp_path: Path, variant: str, expected_generation: str
) -> None:
    """No uncommitted successor may appear in real materialized filesystem output."""
    fixed, expected = _fixed_archive(variant)
    assert expected_generation == ("base" if variant == "base" else "latest")
    path = tmp_path / f"{variant}.cmpct"
    path.write_bytes(fixed)
    output = tmp_path / "output"
    with CMPCT(path) as reader:
        assert sorted(reader.by) == sorted(expected)
        reader.extractall(output, metadata=False, max_bytes=1024 * 1024)

    # Count every filesystem entry, not just regular files: an unexpected
    # empty directory or link is also an incorrect committed logical tree.
    actual = sorted(p.relative_to(output).as_posix() for p in output.rglob("*"))
    assert actual == sorted(expected)
    for name, receipt in expected.items():
        target = output / name
        assert target.is_file() and not target.is_symlink()
        payload = target.read_bytes()
        assert payload == bytes.fromhex(receipt["hex"])
        assert hashlib.sha256(payload).hexdigest() == receipt["sha256"]

    # The deleted file may not reappear because a later uncommitted footer exists.
    if expected_generation == "latest":
        assert not (output / "keep.txt").exists()
