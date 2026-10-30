"""J24G56 prospective negative court: signed unsupported journal opcode semantics.

Research-only child of #789. Passing tests demonstrate a candidate defect;
they are NOT product acceptance tests or a release gate. The signed payload
remains physically authentic so parser divergence cannot be dismissed as CRC.
"""
from __future__ import annotations

import json
import os
import shutil
import struct
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import ValidationError, preflight_archive

_FTR = struct.Struct("<8sBBBBQQQ32s")


def _receipt(path: Path, label: str, reader_state: dict, validator_state: str):
    out = os.environ.get("J24G56_EVIDENCE_DIR")
    if not out:
        return
    root = Path(out)
    root.mkdir(parents=True, exist_ok=True)
    saved = root / f"{label}.cmpct"
    shutil.copyfile(path, saved)
    from hashlib import sha256
    receipt = {
        "label": label,
        "archive": saved.name,
        "sha256": sha256(saved.read_bytes()).hexdigest(),
        "reader": reader_state,
        "preflight": validator_state,
    }
    (root / f"{label}.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))


def _original(tmp_path: Path):
    tree = tmp_path / "tree"
    tree.mkdir()
    payloads = {"a.bin": b"A" * 117, "z.bin": b"Z" * 231}
    for name, payload in payloads.items():
        (tree / name).write_bytes(payload)
    archive = tmp_path / "original.cmpct"
    Builder(tree, workers=1, reproducible=True).build(archive)
    assert preflight_archive(archive)["files"] == 2
    with CMPCT(archive) as ar:
        assert ar.verify() == 2
        return archive, ar.latest_footer_pos, payloads


@pytest.mark.parametrize(
    ("label", "ops", "names", "preflight_must_accept"),
    [
        ("known_delete", [["del", "a.bin"]], {"z.bin"}, True),
        ("unknown_only", [["future_op", "z.bin"]], {"a.bin", "z.bin"}, False),
        ("unknown_then_delete", [["future_op", "z.bin"], ["del", "a.bin"]], {"z.bin"}, False),
        ("delete_then_unknown", [["del", "a.bin"], ["future_op", "z.bin"]], {"z.bin"}, False),
    ],
)
def test_physically_signed_unknown_op_reader_preflight_diverge(
    tmp_path: Path, label: str, ops: list, names: set[str], preflight_must_accept: bool
):
    archive, original_footer, payloads = _original(tmp_path)
    footer, _ = _append_generation(
        archive,
        {"blobs": [], "ops": ops},
        original_footer,
    )
    physical = archive.read_bytes()
    magic, kind, codec, flags, reserved, cs, us, prev, digest = _FTR.unpack_from(physical, footer)
    assert magic == b"CMPTF24\\0".replace(b"\\0", b"\x00")
    assert (kind, flags, reserved, prev) == (1, 0, 0, original_footer)
    assert codec in (0, 1)
    assert cs > 0 and us > 0 and footer + _FTR.size == len(physical)
    with CMPCT(archive) as reader:
        assert reader.latest_footer_pos == footer, "Reader recovered old footer, not observed mismatch"
        assert set(reader.by) == names
        assert reader.verify() == len(names)
        for name in names:
            assert reader.read(name) == payloads[name]
        state = {
            "selected_footer": reader.latest_footer_pos,
            "delta_depth": reader.delta_depth,
            "paths": sorted(reader.by),
            "verify_members": len(names),
        }
    if preflight_must_accept:
        got = preflight_archive(archive)
        assert got["latest_footer"] == footer
        assert got["files"] == len(names)
        validator = "accepts_new_footer"
    else:
        with pytest.raises(ValidationError, match="unsupported transaction operation"):
            preflight_archive(archive)
        validator = "rejects_supported_physical_footer_unsupported_operation"
    _receipt(archive, label, state, validator)


def test_corrupt_latest_footer_recovers_old_generation(tmp_path: Path):
    archive, original_footer, payloads = _original(tmp_path)
    _append_generation(archive, {"blobs": [], "ops": [["future_op", "z.bin"]]}, original_footer)
    bytes_ = bytearray(archive.read_bytes())
    bytes_[-1] ^= 0x01
    archive.write_bytes(bytes_)
    with CMPCT(archive) as reader:
        assert reader.latest_footer_pos == original_footer
        assert set(reader.by) == set(payloads)
        assert reader.verify() == 2
        state = {"selected_footer": original_footer, "paths": sorted(reader.by), "verify_members": 2}
    got = preflight_archive(archive)
    assert got["latest_footer"] == original_footer
    _receipt(archive, "corrupt_footer", state, "recovers_prior_footer")
