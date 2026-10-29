#!/usr/bin/env python3
"""J24G35: synthetic private-directory rebind vs fd-relative stage ownership.

OS primitive research; NOT an installed CMPCT product test. Based on an
already observed 2026-10-29 local Linux pilot. The hosted macOS/Ubuntu court
tests a different source/host and retains all negative evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def attacker_rename_and_rebind(stage: Path, outside: Path, actor_uid: int | None) -> None:
    # The second process can rename the 0700 *directory entry* without
    # traversing its contents. Parent-directory write permission suffices.
    code = """import os, sys
stage, outside, check = sys.argv[1:]
if check == 'separate':
    try: os.listdir(stage)
    except PermissionError: pass
    else: raise AssertionError('the attacker was able to enter the 0700 stage')
os.rename(stage, stage + '-renamed')
os.symlink(outside, stage)
"""
    def switch_uid() -> None:
        os.setgroups([])
        os.setgid(actor_uid)
        os.setuid(actor_uid)

    if actor_uid is not None and os.geteuid() != 0:
        raise RuntimeError("distinct-uid case requires root")
    result = subprocess.run(
        [sys.executable, "-c", code, str(stage), str(outside),
         "separate" if actor_uid is not None else "same"],
        preexec_fn=switch_uid if actor_uid is not None else None,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError("attacker setup failed: " + result.stderr)


def one_case(root: Path, name: str, actor_uid: int | None) -> dict:
    base = root / name
    base.mkdir(mode=0o755)
    parent = base / "shared"
    parent.mkdir()
    parent.chmod(0o777)
    outside = base / "outside"
    outside.mkdir()
    outside.chmod(0o777)
    sentinel = b"INDEPENDENT OUTSIDE SENTINEL\n"
    (outside / "unchanged").write_bytes(sentinel)

    # mkdtemp returns a mode-0700 directory; its parent is writable by the
    # attacker. This is the exact boundary a private-directory-only repair
    # would rely on.
    stage = Path(tempfile.mkdtemp(prefix=".cmpct-stage-", dir=parent))
    assert stat.S_IMODE(stage.stat().st_mode) == 0o700
    source_dir_fd = os.open(stage, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        original = os.fstat(source_dir_fd)
        attacker_rename_and_rebind(stage, outside, actor_uid)
        assert stage.is_symlink()
        assert (stage.with_name(stage.name + "-renamed")).stat().st_ino == original.st_ino

        expected = b"AUTHENTIC INODE CONTENT\n" * 7
        fake = b"ATTACKER NAMESPACE CONTENT"
        # Deliberately demonstrate the weaker design, but exclusively
        # against a synthetic outside file in this temporary test directory.
        unsafe_path = stage / "payload.cmpct"
        unsafe_path.write_bytes(fake)
        assert (outside / "payload.cmpct").read_bytes() == fake
        os.replace(unsafe_path, parent / "unsafe-output.cmpct")
        assert (parent / "unsafe-output.cmpct").read_bytes() == fake

        # The stronger control writes/read-checks using the *same opened
        # source inode* and publishes from its pinned directory FD.
        output_fd = os.open(
            "payload.cmpct", os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=source_dir_fd
        )
        try:
            with os.fdopen(os.dup(output_fd), "wb") as stream:
                stream.write(expected)
                stream.flush()
                os.fsync(stream.fileno())
            inode = os.fstat(output_fd).st_ino
            assert inode == os.stat("payload.cmpct", dir_fd=source_dir_fd,
                                    follow_symlinks=False).st_ino
            os.lseek(output_fd, 0, os.SEEK_SET)
            assert os.read(output_fd, len(expected)) == expected
            os.replace("payload.cmpct", "safe-output.cmpct",
                       src_dir_fd=source_dir_fd, dst_dir_fd=parent_fd)
        finally:
            os.close(output_fd)
        actual = (parent / "safe-output.cmpct").read_bytes()
        assert actual == expected
        assert (outside / "unchanged").read_bytes() == sentinel
        assert not (outside / "payload.cmpct").exists()
        assert (parent / "unsafe-output.cmpct").read_bytes() != expected
        return {
            "scenario": name, "actor_uid": actor_uid,
            "stage_mode": oct(stat.S_IMODE(original.st_mode)),
            "stage_directory_renamed": True,
            "stage_alias_rebound": stage.is_symlink(),
            "weak_path_writer_reached_outside": True,
            "weak_path_publish_used_outside": True,
            "source_dir_fd_retains_original_inode": os.fstat(source_dir_fd).st_ino == original.st_ino,
            "anchored_writer_reached_outside": False,
            "anchored_source_inode": inode,
            "anchored_output_sha256": sha(actual),
            "expected_sha256": sha(expected),
            "outside_sentinel_intact": True,
        }
    finally:
        os.close(source_dir_fd)
        os.close(parent_fd)


def main() -> int:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        print(json.dumps({"decision": "UNSUPPORTED_NOT_SUCCESS", "platform": sys.platform}))
        return 2
    with tempfile.TemporaryDirectory(prefix="j24g35-") as temporary:
        root = Path(temporary)
        root.chmod(0o755)
        cases = [one_case(root, "same_uid", None)]
        # The additional Linux root run explicitly proves the parent-entry
        # attack even when the actor cannot search a 0700 defender directory.
        if os.geteuid() == 0:
            cases.append(one_case(root, "different_uid", 65534))
        assert all(
            c["weak_path_writer_reached_outside"]
            and c["source_dir_fd_retains_original_inode"]
            and not c["anchored_writer_reached_outside"]
            and c["anchored_output_sha256"] == c["expected_sha256"]
            and c["outside_sentinel_intact"]
            for c in cases
        )
        print(json.dumps({
            "schema": "J24G35-posix-stage-custody-v1",
            "decision": "PRIVATE_DIR_ONLY_FALSIFIED__FD_ANCHOR_SURVIVES_THIS_REBIND",
            "evidence_class": "OS_PRIMITIVE_NOT_PRODUCT",
            "platform": sys.platform, "effective_uid": os.geteuid(),
            "cases": cases,
            "unmeasured": [
                "installed CMPCT Builder/Reader/pathless composition",
                "Windows rooted-handle publication",
                "same-UID attacker permitted to mutate private-directory contents",
                "adversarial rename after publication source selection",
                "frozen archive benchmark and release"
            ],
        }, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
