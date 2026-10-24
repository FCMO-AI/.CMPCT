"""Prospective APFS normalization-insensitive namespace court.

Same test source runs before/after a destination-only fix. All file fixtures are
directory-only, so no compression engine or archive bytes are altered.
"""
from __future__ import annotations

import os
import sys
import unicodedata
from pathlib import Path

import pytest

from cmpct.codec import K_DIR
from cmpct.reader import CMPCT


NFC = "caf\u00e9"
NFD = "cafe\u0301"


def _reader(*names: str) -> CMPCT:
    # Exercise authentic Reader.extractall without importing any Builder.
    # No payload references are needed for directory materialization.
    reader = object.__new__(CMPCT)
    reader.files = [[name, K_DIR, 0o755, 0, 0, b"", None] for name in names]
    return reader


def test_lexical_spellings_are_byte_distinct_but_canonically_equivalent() -> None:
    assert NFC != NFD
    assert NFC.encode("utf-8") != NFD.encode("utf-8")
    assert unicodedata.normalize("NFD", NFC) == unicodedata.normalize("NFD", NFD)


def test_real_host_composition_alias_probe(tmp_path: Path) -> None:
    # This is a filesystem probe, not an assumption derived from platform name.
    (tmp_path / NFC).mkdir()
    alias = tmp_path / NFD
    observed = alias.exists() and os.path.samefile(tmp_path / NFC, alias)
    print("HOST_NORMALIZATION_ALIAS", sys.platform, observed)
    if sys.platform == "darwin":
        assert observed, "macOS runner is not a normalization-insensitive host; classify as infrastructure"
    else:
        # Non-Mac filesystems need not be alias-insensitive. This is evidence, not
        # a requirement to mutate the global portable CMPCT grammar.
        assert (tmp_path / NFC).is_dir()


@pytest.mark.skipif(sys.platform != "darwin", reason="requires actual macOS APFS/HFS+ path semantics")
@pytest.mark.parametrize("names", [
    (NFC, NFD),
    (f"root/{NFC}/a", f"root/{NFD}/b"),
    ("Alpha", "alpha"),
])
def test_mac_ambiguous_tree_rejected_before_any_member_creation(
    tmp_path: Path, names: tuple[str, str],
) -> None:
    dest = tmp_path / "out"
    with pytest.raises(IOError, match="(?:ambiguous|duplicate).*macOS|macOS.*(?:ambiguous|duplicate)"):
        _reader(*names).extractall(dest, metadata=False)
    assert dest.is_dir()
    assert list(dest.iterdir()) == []


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS destination")
@pytest.mark.parametrize("name", [NFC, NFD, "regular/subdirectory"])
def test_mac_unambiguous_positive_control(tmp_path: Path, name: str) -> None:
    dest = tmp_path / "out"
    _reader(name).extractall(dest, metadata=False)
    assert (dest / name).is_dir()


@pytest.mark.skipif(sys.platform == "darwin", reason="Mac volumes may conflate Unicode forms")
def test_nonmac_two_spellings_remain_distinct(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    _reader(NFC, NFD).extractall(dest, metadata=False)
    assert (dest / NFC).is_dir()
    assert (dest / NFD).is_dir()
    assert os.stat(dest / NFC).st_ino != os.stat(dest / NFD).st_ino
