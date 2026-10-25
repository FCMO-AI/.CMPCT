"""O81: source/output alias claims against real installed revision-24 Builders.

The original source is obtained from its immutable Git commit, not reconstructed.
This is a bounded failure-mode court, not a release or performance benchmark.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.core import Builder, CMPCT

BASE = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
ORIGINAL_BLOB = "663ef0922992b1fbb8f19e6eea88d55c10a56044"


def _historical_builder(tmp_path):
    assert subprocess.check_output(
        ["git", "rev-parse", f"{BASE}:src/cmpct/builder.py"], text=True
    ).strip() == ORIGINAL_BLOB
    source = subprocess.check_output(
        ["git", "show", f"{BASE}:src/cmpct/builder.py"]
    )
    assert hashlib.sha1(
        b"blob " + str(len(source)).encode() + b"\x00" + source
    ).hexdigest() == ORIGINAL_BLOB
    p = tmp_path / "historical_builder.py"
    p.write_bytes(source)
    name = "cmpct._o81_original_builder"
    spec = importlib.util.spec_from_file_location(name, p)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.Builder


def _source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    raw = hashlib.shake_256(b"cmpct-o81-source-ownership").digest(8192)
    (root / "payload.bin").write_bytes(raw)
    return root, raw


def _hardlink(src, dst):
    try:
        os.link(src, dst)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"host does not grant hardlink creation: {exc}")


def test_historical_successful_build_overwrites_hardlinked_source(tmp_path):
    original = _historical_builder(tmp_path)
    root, raw = _source(tmp_path)
    out = tmp_path / "external-archive.cmpct"
    _hardlink(root / "payload.bin", out)
    assert os.stat(out).st_ino == os.stat(root / "payload.bin").st_ino
    original(root, workers=1).build(out)
    assert (root / "payload.bin").read_bytes() == out.read_bytes()
    assert (root / "payload.bin").read_bytes() != raw
    with CMPCT(out) as ar:
        ar.verify()
        assert ar.read("payload.bin") == raw


def test_candidate_refuses_external_hardlink_and_preserves_source(tmp_path):
    root, raw = _source(tmp_path)
    out = tmp_path / "external-archive.cmpct"
    _hardlink(root / "payload.bin", out)
    with pytest.raises(ValueError, match="hardlink to source"):
        Builder(root, workers=1).build(out)
    assert (root / "payload.bin").read_bytes() == raw
    assert out.read_bytes() == raw
    assert os.stat(out).st_ino == os.stat(root / "payload.bin").st_ino


def test_historical_rebuild_ingests_previous_output(tmp_path):
    original = _historical_builder(tmp_path)
    root, raw = _source(tmp_path)
    out = root / "snapshot.cmpct"
    original(root, workers=1).build(out)
    first = out.read_bytes()
    original(root, workers=1).build(out)
    with CMPCT(out) as ar:
        ar.verify()
        assert ar.read("payload.bin") == raw
        assert ar.read("snapshot.cmpct") == first


def test_candidate_rejects_in_tree_output_before_mutation(tmp_path):
    root, raw = _source(tmp_path)
    out = root / "snapshot.cmpct"
    with pytest.raises(ValueError, match="outside the source root"):
        Builder(root, workers=1).build(out)
    assert not out.exists()
    assert (root / "payload.bin").read_bytes() == raw


def test_candidate_rejects_output_symlink_into_source(tmp_path):
    root, raw = _source(tmp_path)
    out = tmp_path / "external-link.cmpct"
    try:
        out.symlink_to(root / "payload.bin")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"host symlink privileges unavailable: {exc}")
    with pytest.raises(ValueError, match="outside the source root"):
        Builder(root, workers=1).build(out)
    assert out.is_symlink()
    assert (root / "payload.bin").read_bytes() == raw


def test_same_source_external_destination_parity_and_strong_reader(tmp_path):
    original = _historical_builder(tmp_path)
    root, raw = _source(tmp_path)
    out_original = tmp_path / "baseline.cmpct"
    out_candidate = tmp_path / "candidate.cmpct"
    original(root, workers=1).build(out_original)
    Builder(root, workers=1).build(out_candidate)
    assert out_original.read_bytes() == out_candidate.read_bytes()
    assert (root / "payload.bin").read_bytes() == raw
    with CMPCT(out_candidate) as ar:
        ar.verify()
        assert ar.read("payload.bin") == raw


def test_outside_root_prefix_sibling_is_not_misclassified(tmp_path):
    root, raw = _source(tmp_path)
    sibling = tmp_path / "source-other"
    sibling.mkdir()
    out = sibling / "safe.cmpct"
    Builder(root, workers=1).build(out)
    with CMPCT(out) as ar:
        ar.verify()
        assert ar.read("payload.bin") == raw


def test_source_hardlinks_without_output_alias_remain_supported(tmp_path):
    root, raw = _source(tmp_path)
    _hardlink(root / "payload.bin", root / "copy.bin")
    out = tmp_path / "safe.cmpct"
    Builder(root, workers=1).build(out)
    with CMPCT(out) as ar:
        ar.verify()
        assert ar.read("payload.bin") == raw
        assert ar.read("copy.bin") == raw
