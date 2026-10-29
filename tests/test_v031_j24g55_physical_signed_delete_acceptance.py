"""J24G55: acceptance of J24G54a's unchanged physical signed-journal inputs.

The original J24G54a negative-reproduction court stays immutable in PR #786.
This is a separate fixed-candidate acceptance test, not historical evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from cmpct.validation import ValidationError, preflight_archive, _load_effective_index, ParserLimits

KEY = "com.fcmo.cmpct.j24g54" if sys.platform == "darwin" else "user.cmpct_j24g54"
A = "a-owner.bin"
B = "b-delete.bin"
Z = "z-survivor.bin"
VALUE = {"a": b"j24g54-a\x00\xff", "z": b"j24g54-z\x00\xfe"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _set(path: Path, value: bytes) -> None:
    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/xattr", "-wx", KEY, value.hex(), str(path)],
                       check=True, capture_output=True, text=True)
    else:
        os.setxattr(path, KEY, value, follow_symlinks=False)


def _get(path: Path) -> bytes:
    if sys.platform == "darwin":
        result = subprocess.run(["/usr/bin/xattr", "-px", KEY, str(path)],
                                check=True, capture_output=True, text=True)
        return bytes.fromhex("".join(result.stdout.split()))
    return os.getxattr(path, KEY, follow_symlinks=False)


def _named_xattrs(reader: CMPCT) -> dict[str, dict[str, bytes]]:
    result = {}
    for ordinal, entries in reader.fsmeta.get("xattrs", []):
        assert 0 <= ordinal < len(reader.files)
        result[reader.files[ordinal][0]] = {str(name): bytes(value) for name, value in entries}
    return result


@pytest.mark.skipif(sys.platform not in ("darwin", "linux"), reason="native xattr court")
@pytest.mark.parametrize(
    "case,marked,expected_falsifier",
    [
        ("both_survivors", ("a", "z"), True),
        ("late_survivor", ("z",), True),
        ("early_survivor", ("a",), False),
        ("no_xattrs", (), False),
    ],
)
def test_firstparty_committed_delete_preflight_matches_reader(
    tmp_path: Path, case: str, marked: tuple[str, ...], expected_falsifier: bool,
) -> None:
    source = tmp_path / "tree"
    source.mkdir()
    payloads = {A: b"original-A\x00" * 32, B: b"remove-B" * 50, Z: b"survivor-Z\xff" * 42}
    for name, payload in payloads.items():
        (source / name).write_bytes(payload)
    for flag in marked:
        name = A if flag == "a" else Z
        _set(source / name, VALUE[flag])
        assert _get(source / name) == VALUE[flag]

    archive = tmp_path / "journal.cmpct"
    Builder(source, workers=1, reproducible=False).build(archive)
    raw_before = archive.read_bytes()
    base_validation = preflight_archive(archive)
    assert base_validation["files"] == 3
    with CMPCT(archive) as reader:
        assert reader.verify() == 3
        original_attrs = _named_xattrs(reader)
        assert set(original_attrs) == {A if flag == "a" else Z for flag in marked}
        for flag in marked:
            name = A if flag == "a" else Z
            assert original_attrs[name][KEY] == VALUE[flag]
        assert [row[0] for row in reader.files] == [A, B, Z]

    append_delete(archive, B)
    raw_after = archive.read_bytes()
    assert raw_after.startswith(raw_before), "journal must append, not rewrite base"
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        assert [row[0] for row in reader.files] == [A, Z]
        assert reader.read(A) == payloads[A]
        assert reader.read(Z) == payloads[Z]
        corrected_attrs = _named_xattrs(reader)
        assert set(corrected_attrs) == set(original_attrs)
        for name in original_attrs:
            assert corrected_attrs[name] == original_attrs[name]
        restored = tmp_path / "restored"
        reader.extractall(restored, metadata=True, require_xattrs=bool(marked))
    assert not (restored / B).exists()
    for name in (A, Z):
        assert (restored / name).read_bytes() == payloads[name]
    for flag in marked:
        name = A if flag == "a" else Z
        assert _get(restored / name) == VALUE[flag]

    error = None
    try:
        final_validation = preflight_archive(archive)
    except ValidationError as exc:
        error = f"{type(exc).__name__}: {exc}"
        final_validation = None
    # Historical negative predicate remains preserved independently.
    assert error is None, f"valid signed journal wrongly rejected: {error}"
    assert final_validation["files"] == 2
    with archive.open("rb") as stream:
        effective, _, footer, depth = _load_effective_index(
            stream, os.fstat(stream.fileno()).st_size, ParserLimits())
    assert footer and depth == 1
    mapped = {}
    for ordinal, pairs in effective.get("fsmeta", {}).get("xattrs", []):
        assert 0 <= ordinal < len(effective["files"])
        mapped[effective["files"][ordinal][0]] = {
            str(name): bytes(value) for name, value in pairs}
    assert mapped == corrected_attrs == original_attrs
    assert bool(expected_falsifier) == (Z in original_attrs)

    output_dir = os.environ.get("J24G55_EVIDENCE_DIR")
    if output_dir:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{case}-before.cmpct").write_bytes(raw_before)
        (directory / f"{case}-after.cmpct").write_bytes(raw_after)
        receipt = {
            "case": case, "host": sys.platform,
            "before_sha256": _sha(raw_before), "after_sha256": _sha(raw_after),
            "marked_names": sorted(original_attrs), "survivor_names": [A, Z],
            "reader_verify": 2, "native_xattr_readback": True,
            "preflight_before": base_validation, "preflight_after": final_validation,
            "preflight_remapped_owners": sorted(mapped),
            "reader_remapped_owners": sorted(corrected_attrs),
            "preflight_exception": error, "expected_falsifier": expected_falsifier,
            "source": "installed real Builder and transaction Writer; unmodified branch product",
        }
        (directory / f"{case}-receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("J24G55_ACCEPT", case, "reader_valid=2", "preflight_exception=", error)
