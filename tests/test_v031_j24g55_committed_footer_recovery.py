"""J24G55: physical committed-footer recovery invariants under the shared replay.

This is a new candidate verification court. It does not change or relabel
historical malformed-index, crash/recovery or frozen release fixtures.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from cmpct.validation import preflight_archive


def _verify(path: Path, names: set[str]) -> None:
    assert preflight_archive(path)["files"] == len(names)
    with CMPCT(path) as reader:
        assert set(reader.by) == names
        assert reader.verify() == len(names)


@pytest.mark.parametrize("corruption", ["footer_sha", "footer_truncated", "uncommitted_tail"])
def test_signed_journal_recovers_only_committed_generations(tmp_path: Path, corruption: str):
    tree = tmp_path / "tree"
    tree.mkdir()
    originals = {"a.bin": b"A" * 117, "b.bin": b"B" * 223, "c.bin": b"C" * 319}
    for name, payload in originals.items():
        (tree / name).write_bytes(payload)
    archive = tmp_path / "archive.cmpct"
    Builder(tree, workers=1, reproducible=False).build(archive)
    _verify(archive, set(originals))
    before = archive.read_bytes()
    append_delete(archive, "b.bin")
    after = archive.read_bytes()
    assert after.startswith(before) and len(after) > len(before)
    _verify(archive, {"a.bin", "c.bin"})
    altered = bytearray(after)
    expected = set(originals)
    if corruption == "footer_sha":
        altered[-1] ^= 1
    elif corruption == "footer_truncated":
        altered = altered[:-1]
    else:
        altered.extend(b"\x00UNCOMMITTED\xffCMPCT-TRAIL\x00")
        expected = {"a.bin", "c.bin"}
    adversarial = tmp_path / f"{corruption}.cmpct"
    adversarial.write_bytes(altered)
    _verify(adversarial, expected)
    with CMPCT(adversarial) as reader:
        for name in expected:
            assert reader.read(name) == originals[name]
