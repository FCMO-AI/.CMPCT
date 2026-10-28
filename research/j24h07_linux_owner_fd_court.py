"""J24H07 installed first-party CMPCT Linux bound-owner hardlink test.

Prospectively registered before product patch in
 docs/v031-research/2026-10-28-j24h07-linux-owner-fd-prereg.md.
All real Builder/Writer/Reader bytes and genuine kernel linkat; only the
injection timing is controlled by this process. No cross-platform release credit.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import tempfile
from unittest import mock

from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.core import Builder, CMPCT
from cmpct.transactions import append_rename
from cmpct.validation import preflight_archive

CONTENT = (b"J24H06 authenticated owner byte stream\x00\xff" * 127)
EXTERNAL = (b"J24H06 untrusted external canary DIFFERENT\x00" * 123)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def describe(path: Path) -> dict:
    if not path.exists() and not path.is_symlink():
        return {"exists": False}
    l = os.lstat(path)
    d = {
        "exists": True, "symlink": stat.S_ISLNK(l.st_mode),
        "regular_nofollow": stat.S_ISREG(l.st_mode),
        "mode": stat.S_IFMT(l.st_mode),
        "lstat_dev": l.st_dev, "lstat_ino": l.st_ino,
    }
    try:
        s = os.stat(path)
        d.update({"stat_dev": s.st_dev, "stat_ino": s.st_ino,
                  "sha256": sha(path.read_bytes()), "bytes": s.st_size})
    except (OSError, ValueError) as exc:
        d["stat_error"] = type(exc).__name__ + ": " + str(exc)
    return d


def execute(root: Path) -> dict:
    src = root / "src"
    src.mkdir()
    owner = src / "b-owner"
    alias = src / "z-alias"
    owner.write_bytes(CONTENT)
    os.link(owner, alias)
    assert os.path.samefile(owner, alias)
    original = root / "base.cmpct"
    Builder(src, workers=1, reproducible=False).build(original)
    renamed = root / "forward.cmpct"
    renamed.write_bytes(original.read_bytes())
    append_rename(renamed, "z-alias", "a-alias")
    signed_sha = sha(renamed.read_bytes())
    assert renamed.read_bytes().startswith(b"CMPCT24\x00")
    assert preflight_archive(renamed)["files"] == 2

    external = root / "external-sentinel.bin"
    external.write_bytes(EXTERNAL)
    external_initial_sha = sha(external.read_bytes())

    with CMPCT(renamed) as reader:
        assert sorted(reader.by) == ["a-alias", "b-owner"]
        assert reader.by["a-alias"][1] == K_HARDLINK
        assert reader.by["a-alias"][6] == ["b-owner"]
        assert reader.by["b-owner"][1] == K_FILE
        assert reader.verify() == 2
        assert reader.read("a-alias") == CONTENT
        assert reader.read_range("b-owner", 3, 40) == CONTENT[3:43]

        control = root / "control"
        reader.extractall(control, metadata=True)
        cowner, calias = control / "b-owner", control / "a-alias"
        assert not cowner.is_symlink() and not calias.is_symlink()
        assert cowner.read_bytes() == calias.read_bytes() == CONTENT
        assert os.path.samefile(cowner, calias)
        assert not os.path.samefile(cowner, external)

        dest = root / "injected"
        expected_owner = os.path.abspath(dest / "b-owner")
        expected_alias = os.path.abspath(dest / "a-alias")
        displaced = dest / "b-owner.original-displaced"
        from cmpct.reader import _linux_link_owner_fd
        real_link = _linux_link_owner_fd
        seen = []

        def swap_at_link(source_fd, alias_full):
            # This is the first and only kernel linkat for this signed owner.
            assert os.path.abspath(alias_full) == expected_alias, (alias_full, expected_alias)
            assert not seen, 'unexpected second hardlink operation'
            assert (dest / 'b-owner').read_bytes() == CONTENT
            assert not (dest / 'b-owner').is_symlink()
            before=os.fstat(source_fd)
            assert stat.S_ISREG(before.st_mode), 'source descriptor not a regular inode'
            assert os.stat(expected_owner).st_ino == before.st_ino
            (dest / 'b-owner').rename(displaced)
            (dest / 'b-owner').symlink_to(external)
            seen.append({'owner_swapped':True,'source_fd_inode':before.st_ino,
                         'replacement':'symlink to external'})
            # Invoke the genuine Linux syscall via production helper, not a mocked success.
            return real_link(source_fd, alias_full)

        thrown = None
        with mock.patch("cmpct.reader._linux_link_owner_fd", side_effect=swap_at_link):
            try:
                reader.extractall(dest, metadata=True)
            except (OSError, IOError, RuntimeError, ValueError) as exc:
                thrown = type(exc).__name__ + ": " + str(exc)

    assert len(seen) == 1, "race instrumentation did not reach its target"
    a = describe(dest / "a-alias")
    b = describe(dest / "b-owner")
    d = describe(displaced)
    e = describe(external)
    control_owner = describe(cowner)
    control_alias = describe(calias)
    assert d["sha256"] == sha(CONTENT), "instrument lost authentic bytes"
    assert sha(external.read_bytes()) == external_initial_sha, "external sentinel was modified"
    assert sha(renamed.read_bytes()) == signed_sha, "signed archive changed during test"

    accepted = thrown is None
    alias_owned=(a.get('sha256')==sha(CONTENT) and not a.get('symlink',True)
                 and a.get('stat_ino')==d.get('stat_ino')
                 and a.get('stat_dev')==d.get('stat_dev'))
    # A changed public owner name means returning success is not safe even if
    # the alias's source inode was bound correctly. The candidate must fail closed.
    mismatch = accepted or not alias_owned or not b.get('symlink',False)
    result = ('BOUND_SOURCE_AND_FAIL_CLOSED' if not accepted and alias_owned and b.get('symlink')
              else 'UNEXPECTED_UNSAFE_OUTCOME')
    record = {
        "hypothesis": "J24H07-LINUX-FD-OWNER",
        "platform": platform.platform(),
        "archive_sha256": signed_sha,
        "archive_bytes": renamed.stat().st_size,
        "signed_payload_sha256": sha(CONTENT),
        "external_initial_sha256": external_initial_sha,
        "external_final_sha256": sha(external.read_bytes()),
        "control": {"owner": control_owner, "alias": control_alias,
                    "same_inode": os.path.samefile(cowner, calias),
                    "verified_members": 2, "metadata": True},
        "injection": {"calls": seen, "original_owner_displaced": d,
                      "swapped_owner": b, "alias": a, "external": e,
                      "extract_exception": thrown,
                      "metadata": True},
        "result": result,
        "accepted_without_postextract_validation": accepted,
        "silent_mismatch": bool(mismatch),
        "bound_alias_to_original_inode": bool(alias_owned),
        "scientific_scope": "Deterministic inter-call race, not exploitation frequency or release acceptance",
    }
    assert result=='BOUND_SOURCE_AND_FAIL_CLOSED', json.dumps(record,sort_keys=True)
    assert 'rebound' in (thrown or ''), thrown
    # This proves only source-fd alias binding and observed fail-close in this
    # deterministic intercall source-name swap, not hostile-tree atomicity.
    return record


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="cmpct-j24h07-") as td:
        result = execute(Path(td))
    artifact_dir = os.getenv("J24H07_ARTIFACTS")
    if artifact_dir:
        p = Path(artifact_dir)
        p.mkdir(parents=True, exist_ok=True)
        (p / "court.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("J24H07_PRODUCT_COURT=" + json.dumps(result, sort_keys=True), flush=True)
