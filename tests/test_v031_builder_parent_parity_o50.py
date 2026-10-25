"""O50 source-exact O47-parent vs O47+O48 composition on identical real source.

The baseline is executed from the actual parent commit using the same installed
runtime/codec.  This tests full archive bytes rather than inferring parity from
the visually small Builder source diff.  Only supported input types participate.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import types
import zipfile

import pytest

from cmpct.builder import Builder as ComposedBuilder
from cmpct.codec import K_HARDLINK
from cmpct.reader import CMPCT

_PARENT_SHA = "29d9688ae6bff6d1eccc27f019893866abe5b5c3"
_PARENT_BUILDER_BLOB = "6f60dfe63742ff4b777f959a15d6fb828ae29610"


def _exact_parent_builder():
    root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True).strip())
    # O59: generic Tests intentionally uses a shallow checkout, unlike the O50
    # hosted court. Prefer the actual immutable parent commit when it exists;
    # fall back ONLY if the commit object itself is missing. An existing commit
    # with a missing historical source path must still fail, not be concealed.
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{_PARENT_SHA}^{{commit}}"],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False).returncode == 0
    if exists:
        src = subprocess.check_output(
            ["git", "show", f"{_PARENT_SHA}:src/cmpct/builder.py"], cwd=root)
        custody = "git-parent"
    else:
        # The fixture is the unedited historical source file, not a new Builder
        # implementation. Its blob identity is verified below on every use.
        # A Git checkout may apply CRLF conversion on Windows. Read the
        # immutable indexed blob, not transformed working-tree text, so the
        # source is byte-identical across supported platforms.
        fixture_ref = "HEAD:tests/fixtures/o50_o47_parent_builder.py"
        frozen_blob = subprocess.check_output(
            ["git", "rev-parse", fixture_ref], cwd=root, text=True).strip()
        assert frozen_blob == _PARENT_BUILDER_BLOB, (
            "frozen fixture index custody", frozen_blob, _PARENT_BUILDER_BLOB
        )
        src = subprocess.check_output(
            ["git", "cat-file", "blob", frozen_blob], cwd=root)
        custody = "frozen-exact-blob"
    blob = hashlib.sha1(
        b"blob " + str(len(src)).encode("ascii") + b"\0" + src
    ).hexdigest()
    assert blob == _PARENT_BUILDER_BLOB, (custody, blob, _PARENT_BUILDER_BLOB)
    print("O50_PARENT_SOURCE_CUSTODY", custody, blob)
    # A distinct module namespace avoids monkeypatching the installed production
    # Builder. Relative imports still use the real, installed cmpct.codec/Reader.
    mod = types.ModuleType("cmpct._o50_parent_builder")
    mod.__package__ = "cmpct"
    mod.__file__ = str(root / "src/cmpct/builder.py")
    # CPython's dataclass resolution of postponed annotations consults
    # sys.modules[cls.__module__]; an unregistered isolated namespace is invalid.
    sys.modules[mod.__name__] = mod
    exec(compile(src, f"git:{_PARENT_SHA}:src/cmpct/builder.py", "exec"), mod.__dict__)
    return mod.Builder


def _make_source(root: Path, shape: str) -> Path:
    source = root / f"source-{shape}"
    source.mkdir()
    (source / "nested").mkdir()
    if shape == "tiny":
        for i in range(31):
            # Vary extension and payload; aggregation must be source-equivalent.
            p = source / "nested" / (f"{i:03d}.txt" if i % 2 else f"{i:03d}.bin")
            p.write_bytes(bytes((i * 17 + j * 13) & 255 for j in range(20 + 11*i)))
        (source / "empty.txt").write_bytes(b"")
    elif shape == "mixed":
        payload = bytes((i * 23 + (i >> 8) * 17) & 255 for i in range(64 * 1024))
        (source / "owner.bin").write_bytes(payload)
        os.link(source / "owner.bin", source / "alias.bin")
        (source / "independent.bin").write_bytes(payload)
        with zipfile.ZipFile(source / "nested" / "container.zip", "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("alpha.txt", "delta" * 100)
            z.writestr("other.bin", bytes(range(256)))
        with open(source / "sparse.dat", "wb") as fh:
            fh.seek(2 * 1024 * 1024)
            fh.write(b"tailmarker")
        if os.name != "nt":
            os.symlink("owner.bin", source / "symbolic")
    else:
        raise AssertionError(shape)
    return source


@pytest.mark.parametrize("shape", ["tiny", "mixed"])
def test_composed_builder_preserves_exact_parent_bytes_on_supported_sources(tmp_path: Path, shape: str):
    source = _make_source(tmp_path, shape)
    ParentBuilder = _exact_parent_builder()
    output_47 = tmp_path / f"parent-{shape}.cmpct"
    output_50 = tmp_path / f"composed-{shape}.cmpct"
    params = {"workers": 1, "reproducible": True, "reproducible_epoch_ns": 0}
    ParentBuilder(source, **params).build(output_47)
    ComposedBuilder(source, **params).build(output_50)
    original = output_47.read_bytes()
    composed = output_50.read_bytes()
    assert original == composed, {
        "shape": shape,
        "baseline_len": len(original),
        "candidate_len": len(composed),
        "baseline_sha": hashlib.sha256(original).hexdigest(),
        "candidate_sha": hashlib.sha256(composed).hexdigest(),
    }
    for archive in (output_47, output_50):
        with CMPCT(archive) as reader:
            assert reader.verify() >= 1
            files = reader.index["files"]
            if shape == "mixed":
                assert sum(row[1] == K_HARDLINK for row in files) == 1, files
    print("O50_PARENT_BYTE_IDENTITY", shape, len(original),
          hashlib.sha256(original).hexdigest())


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="original O47 versus O50 FIFO admission is POSIX only")
def test_exact_parent_silently_omits_fifo_but_composite_refuses(tmp_path: Path):
    """Same-source A/B: baseline passes with a missing entry, candidate fails closed.

    This negative control deliberately runs the historical source code unchanged,
    rather than simulating its behavior with a mocked predicate.
    """
    source = _make_source(tmp_path, "mixed")
    fifo = source / "zz-unsupported.fifo"
    os.mkfifo(fifo, mode=0o600)
    ParentBuilder = _exact_parent_builder()
    legacy = tmp_path / "legacy-partial.cmpct"
    ParentBuilder(source, workers=1, reproducible=True, reproducible_epoch_ns=0).build(legacy)
    with CMPCT(legacy) as reader:
        assert reader.verify() >= 1
        assert all(row[0] != fifo.name for row in reader.index["files"])
        assert sum(row[1] == K_HARDLINK for row in reader.index["files"]) == 1
    sentinel = b"PREVIOUS-SIGNED-GENERATION-MUST-NOT-BE-DESTROYED"
    candidate = tmp_path / "candidate-existing.cmpct"
    candidate.write_bytes(sentinel)
    with pytest.raises(OSError, match="unsupported filesystem entry"):
        ComposedBuilder(source, workers=1, reproducible=True,
                        reproducible_epoch_ns=0).build(candidate)
    assert candidate.read_bytes() == sentinel
