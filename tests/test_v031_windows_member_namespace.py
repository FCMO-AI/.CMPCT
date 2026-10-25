"""Win32 extraction namespace contract: do not reinterpret valid archive names as drives,
alternate data streams, devices, or case aliases of other members.

This is a destination-filesystem admission rule, not a change to r24 wire grammar:
POSIX archives may legitimately contain names that Win32 cannot represent safely.
"""
from __future__ import annotations

import ntpath
import os
from pathlib import Path

import pytest

from cmpct.codec import K_DIR, K_HARDLINK, K_SYMLINK, S_BLOB
from cmpct.path_policy import canonical_logical_path, canonical_windows_extraction_key
from cmpct.reader import CMPCT


@pytest.mark.parametrize("path", [
    "D:outside", "D:/outside", "folder/file:stream", "folder/<name>",
    "folder/a?b", "folder/a|b", "folder/a\x01b",
    "NUL", "NUL.txt", "CONIN$", "a/COM1.txt", "a/LPT\u00b2.bin",
    "trailing.", "dir/name ", "dir/COM\u00b3",
])
def test_windows_namespace_rejects_nonordinary_or_aliased_names(path: str) -> None:
    _, parts = canonical_logical_path(path)
    with pytest.raises(ValueError, match="Windows"):
        canonical_windows_extraction_key(parts)


@pytest.mark.parametrize("path", [
    "alpha/beta.txt", "alpha\\beta.txt", ".git/config", "a/proper name.txt",
    "data-01/file_02", "a/hello.world",
])
def test_windows_namespace_accepts_regular_members(path: str) -> None:
    _, parts = canonical_logical_path(path)
    assert canonical_windows_extraction_key(parts)


def test_windows_namespace_detects_case_aliases_without_changing_posix_grammar() -> None:
    upper = canonical_windows_extraction_key(canonical_logical_path("Alpha/Report.TXT")[1])
    lower = canonical_windows_extraction_key(canonical_logical_path("alpha/report.txt")[1])
    assert upper == lower
    # The wire-name grammar must stay capable of expressing legitimate POSIX names.
    assert canonical_logical_path("folder/a:b")[0] == "folder/a:b"


def test_drive_relative_escape_is_a_real_win32_path_join_hazard() -> None:
    # Independent stdlib control: the apparent child name resets ntpath's drive authority.
    result = ntpath.join(r"C:\safe\root", "D:outside")
    assert ntpath.splitdrive(result)[0].upper() == "D:"
    assert result != ntpath.join(r"C:\safe\root", "ordinary")
    with pytest.raises(ValueError, match="Windows"):
        canonical_windows_extraction_key(("D:outside",))


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows filesystem semantics")
@pytest.mark.parametrize("name", ["D:outside", "abc:stream", "NUL.txt", "bad."])
def test_real_windows_extractor_rejects_before_any_member_write(tmp_path: Path, name: str) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [[name, K_DIR, 0o755, 0, 0, b"", None]]
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="unsafe Windows"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows filesystem semantics")
def test_real_windows_extractor_rejects_case_collisions_before_writes(tmp_path: Path) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [
        ["Alpha", K_DIR, 0o755, 0, 0, b"", None],
        ["alpha", K_DIR, 0o755, 0, 0, b"", None],
    ]
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="duplicate Windows"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows filesystem semantics")
def test_real_windows_symlink_target_rejects_drive_relative_escape(tmp_path: Path) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [["link", K_SYMLINK, 0o777, 0, 9, b"", [S_BLOB, 0]]]
    ar.read = lambda name: b"D:outside"
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="unsafe Windows"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows filesystem semantics")
def test_real_windows_regular_directory_roundtrip_remains_available(tmp_path: Path) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [["ordinary/child", K_DIR, 0o755, 0, 0, b"", None]]
    destination = tmp_path / "out"
    ar.extractall(destination, metadata=False)
    assert (destination / "ordinary" / "child").is_dir()


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows filesystem semantics")
def test_real_windows_implicit_parent_case_alias_is_rejected_prewrite(tmp_path: Path) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [
        ["Dir/a", K_DIR, 0o755, 0, 0, b"", None],
        ["dir/b", K_DIR, 0o755, 0, 0, b"", None],
    ]
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="ambiguous Windows parent case alias"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows filesystem semantics")
def test_real_windows_hardlink_owner_cannot_change_drive_authority(tmp_path: Path) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [["alias", K_HARDLINK, 0o644, 0, 0, b"", ["D:outside"]]]
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="unsafe Windows hardlink target"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX namespace can represent Win32-reserved names")
def test_real_posix_extractor_keeps_legal_windows_incompatible_names(tmp_path: Path) -> None:
    ar = object.__new__(CMPCT)
    names = ["a:stream", "NUL.txt", "Case", "case", "trailing."]
    ar.files = [[name, K_DIR, 0o755, 0, 0, b"", None] for name in names]
    destination = tmp_path / "out"
    ar.extractall(destination, metadata=False)
    assert sorted(p.name for p in destination.iterdir()) == sorted(names)


@pytest.mark.parametrize("target", [r"\outside", "/outside", r"\Windows\Temp"])
def test_win32_root_relative_symlink_target_is_not_relative_to_destination(target: str) -> None:
    # This independent standard-library discriminator catches a common false
    # assumption: PureWindowsPath.is_absolute() is false for root-relative paths,
    # although a symlink to them escapes its containing extraction directory.
    root = r"C:\safe\root"
    joined = ntpath.normcase(ntpath.normpath(ntpath.join(root, target)))
    assert not joined.startswith(ntpath.normcase(ntpath.normpath(root)) + "\\")
    # Python 3.13 may return False from ntpath.isabs for a single leading
    # separator. Confinement is the invariant, not one stdlib predicate.


@pytest.mark.skipif(os.name != "nt", reason="requires real Windows symlink creation policy")
@pytest.mark.parametrize("target", [r"\outside", "/outside"])
def test_real_win32_root_relative_symlink_target_rejected(tmp_path: Path, target: str) -> None:
    ar = object.__new__(CMPCT)
    ar.files = [["link", K_SYMLINK, 0o777, 0, len(target.encode()), b"", [S_BLOB, 0]]]
    ar.read = lambda name: target.encode()
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="unsafe Windows"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []
