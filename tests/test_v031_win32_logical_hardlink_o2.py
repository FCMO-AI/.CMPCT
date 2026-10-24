"""Prospective O2 Win32 missing-exact-logical-hardlink-owner regression.

Case-fold resolution in Windows must not turn a missing authenticated logical
source into an accepted hardlink. Exact-owner positive stays available.
"""
from __future__ import annotations
import os
from pathlib import Path
import pytest
from cmpct.codec import K_FILE, K_HARDLINK, S_BLOB
from cmpct.reader import CMPCT


def _archive(owner: str, alias_source: str) -> CMPCT:
    r = object.__new__(CMPCT)
    r.files = [
        [owner, K_FILE, 0o644, 0, 7, b"", [S_BLOB, 0]],
        ["alias", K_HARDLINK, 0o644, 0, 7, b"", [alias_source]],
    ]
    r.read = lambda name: b"payload"
    return r


@pytest.mark.skipif(os.name != "nt", reason="requires real Win32 case-insensitive filesystem")
def test_win32_missing_exact_logical_owner_refused_before_writes(tmp_path: Path) -> None:
    # Confirm the host's physical alias property independently; otherwise the
    # runner is not a valid Win32 test environment for this specific mechanism.
    probe = tmp_path / "physical_probe"
    probe.mkdir()
    (probe / "Alpha").write_bytes(b"payload")
    assert os.path.samefile(probe / "Alpha", probe / "alpha"), "runner lacks expected case-alias semantics"
    dest = tmp_path / "out"
    with pytest.raises(IOError, match="(?:missing logical Windows hardlink owner|unsafe Windows hardlink)"):
        _archive("Alpha", "alpha").extractall(dest, metadata=False)
    assert dest.is_dir() and not list(dest.iterdir()), "reject entire archive before any member creation"


@pytest.mark.skipif(os.name != "nt", reason="requires genuine Windows filesystem")
def test_win32_exact_logical_owner_hardlink_still_allowed(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    _archive("Alpha", "Alpha").extractall(dest, metadata=False)
    assert (dest / "Alpha").read_bytes() == (dest / "alias").read_bytes() == b"payload"
    assert os.path.samefile(dest / "Alpha", dest / "alias")
