#!/usr/bin/env python3
"""J24P02 scoped Linux kernel oracle, not a CMPCT Reader/product patch.

Checks unnamed O_TMPFILE source identity at atomic *creation* via linkat,
with EEXIST controls. It CANNOT safely replace an existing output.
"""
from __future__ import annotations

import ctypes
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tempfile
import zipfile

AT_FDCWD = -100
AT_EMPTY_PATH = 0x1000
AT_SYMLINK_FOLLOW = 0x400
CASE_NAMES = ("absent", "regular_occupied", "symlink_occupied",
              "hardlink_occupied", "late_creation", "renamed_parent_boundary")
PAYLOAD = hashlib.sha256(b"CMPCT-J24P02-fixed-input-no-fixture-identity").digest() * 2
libc = ctypes.CDLL(None, use_errno=True)
libc.linkat.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
libc.linkat.restype = ctypes.c_int


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def complete_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        member = zipfile.ZipInfo("raw.bin", date_time=(2020, 1, 2, 3, 4, 6))
        member.compress_type = zipfile.ZIP_DEFLATED
        member.create_system = 3
        member.external_attr = 0o100644 << 16
        archive.writestr(member, PAYLOAD)
    return buffer.getvalue()


def authenticate(raw: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.namelist() == ["raw.bin"]
        assert archive.testzip() is None
        assert archive.read("raw.bin") == PAYLOAD


def unnamed_zip(directory: Path):
    # NOTE: O_EXCL with O_TMPFILE prevents linkat publication on Linux.
    fd = os.open(directory, os.O_TMPFILE | os.O_RDWR, 0o600)
    try:
        raw = complete_zip()
        with os.fdopen(os.dup(fd), "wb") as stream:
            stream.write(raw)
            stream.flush()
        os.fsync(fd)
        inode = os.fstat(fd)
        assert stat.S_ISREG(inode.st_mode) and inode.st_nlink == 0
        os.lseek(fd, 0, os.SEEK_SET)
        assert os.read(fd, len(raw) + 1) == raw
        authenticate(raw)
        return fd, raw, inode
    except BaseException:
        os.close(fd)
        raise


def linkat(oldfd, oldpath, newdirfd, newname, flags):
    ctypes.set_errno(0)
    if libc.linkat(oldfd, oldpath, newdirfd, newname, flags) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def publish(fd: int, directory_fd: int, leaf: str) -> str:
    name = os.fsencode(leaf)
    try:
        linkat(fd, b"", directory_fd, name, AT_EMPTY_PATH)
        return "AT_EMPTY_PATH"
    except OSError as e:
        if e.errno not in (errno.EPERM, errno.ENOENT, errno.EINVAL):
            raise
        # Documented alternative for unprivileged Linux without CAP_DAC_READ_SEARCH.
        linkat(AT_FDCWD, os.fsencode("/proc/self/fd/%d" % fd),
               directory_fd, name, AT_SYMLINK_FOLLOW)
        return "PROC_SELF_FD_FOLLOW"


def normal_case(name: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-j24p02-") as temporary:
        root = Path(temporary)
        folder = root / "output"
        folder.mkdir()
        target = folder / "finished.zip"
        victim = root / "unrelated.zip"
        foreign = complete_zip().replace(b"raw.bin", b"for.bin")
        victim.write_bytes(foreign)
        vstat = victim.stat()
        vsha = sha(victim.read_bytes())
        if name == "regular_occupied":
            target.write_bytes(b"sentinel-existing-data")
        elif name == "symlink_occupied":
            target.symlink_to(victim)
        elif name == "hardlink_occupied":
            os.link(victim, target)
        elif name not in ("absent", "late_creation"):
            raise AssertionError(name)

        fd, raw, initial = unnamed_zip(folder)
        dirfd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
        try:
            if name == "absent":
                assert not target.exists(), "staging was visible prematurely"
                route = publish(fd, dirfd, target.name)
                current = os.lstat(target)
                assert stat.S_ISREG(current.st_mode)
                assert (current.st_dev, current.st_ino) == (initial.st_dev, initial.st_ino)
                assert current.st_nlink == 1
                assert target.read_bytes() == raw
                authenticate(target.read_bytes())
                result = "EXACT_FD_TO_NAME_CREATE"
                error = None
            else:
                if name == "late_creation":
                    # Separate process, same-UID adversary inserting a valid ZIP
                    # exactly before the final kernel publication operation.
                    code = "import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(bytes.fromhex(sys.argv[2]))"
                    subprocess.run([sys.executable, "-c", code, str(target), foreign.hex()],
                                   check=True, timeout=12, capture_output=True)
                old = os.lstat(target)
                old_bytes = target.read_bytes()
                old_link = os.readlink(target) if target.is_symlink() else None
                try:
                    publish(fd, dirfd, target.name)
                except OSError as exc:
                    assert exc.errno == errno.EEXIST, (name, exc)
                    error = "EEXIST"
                else:
                    raise AssertionError("existing destination was clobbered!")
                current = os.lstat(target)
                assert (current.st_dev, current.st_ino) == (old.st_dev, old.st_ino)
                assert stat.S_IFMT(current.st_mode) == stat.S_IFMT(old.st_mode)
                assert target.read_bytes() == old_bytes
                assert (os.readlink(target) if target.is_symlink() else None) == old_link
                route = "EEXIST_REFUSAL"
                result = "ATOMIC_NOCLOBBER_REJECTION"

            assert sha(victim.read_bytes()) == vsha
            assert (victim.stat().st_dev, victim.stat().st_ino) == (vstat.st_dev, vstat.st_ino)
            assert initial.st_nlink == 0
            return {"case": name, "result": result, "route": route, "errno": error,
                    "source_inode": initial.st_ino, "source_unlinked_before": True,
                    "raw_zip_sha256": sha(raw), "published_sha256": sha(target.read_bytes()),
                    "foreign_victim_sha256": vsha}
        finally:
            os.close(dirfd)
            os.close(fd)


def renamed_parent_boundary() -> dict:
    # Deliberate negative: dirfd binds the parent *inode*, not a permanent path.
    with tempfile.TemporaryDirectory(prefix="cmpct-j24p02-parent-") as temporary:
        base = Path(temporary)
        original = base / "original"
        moved = base / "relocated"
        original.mkdir()
        fd, raw, inode = unnamed_zip(original)
        dirfd = os.open(original, os.O_RDONLY | os.O_DIRECTORY)
        try:
            parent = os.fstat(dirfd)
            os.rename(original, moved)
            assert not original.exists()
            route = publish(fd, dirfd, "finished.zip")
            target = moved / "finished.zip"
            assert target.read_bytes() == raw
            authenticate(target.read_bytes())
            assert not (original / "finished.zip").exists()
            assert (target.stat().st_dev, target.stat().st_ino) == (inode.st_dev, inode.st_ino)
            assert (moved.stat().st_dev, moved.stat().st_ino) == (parent.st_dev, parent.st_ino)
            return {"case": "renamed_parent_boundary", "route": route,
                    "result": "DIRFD_INODE_BOUND_PATHNAME_NOT_BOUND",
                    "raw_zip_sha256": sha(raw), "original_path_stale": True}
        finally:
            os.close(dirfd)
            os.close(fd)


def main() -> int:
    if platform.system() != "Linux" or not hasattr(os, "O_TMPFILE"):
        print("J24P02_DECISION=UNSUPPORTED", flush=True)
        return 2
    rows = []
    try:
        for name in CASE_NAMES:
            row = renamed_parent_boundary() if name == "renamed_parent_boundary" else normal_case(name)
            assert row["case"] == name
            rows.append(row)
            print("J24P02_CASE=" + json.dumps(row, sort_keys=True), flush=True)
        assert len(rows) == 6
        assert rows[0]["result"] == "EXACT_FD_TO_NAME_CREATE"
        assert all(row["result"] == "ATOMIC_NOCLOBBER_REJECTION" for row in rows[1:5])
        assert rows[5]["result"] == "DIRFD_INODE_BOUND_PATHNAME_NOT_BOUND"
    except BaseException as exc:
        import traceback
        traceback.print_exc()
        print("J24P02_DECISION=NOT_PROVEN_OR_FALSIFIED " + repr(exc), flush=True)
        return 1
    print("J24P02_DECISION=" + json.dumps({
        "result": "LINUX_CREATE_ONLY_DESCRIPTOR_PUBLICATION_SCOPED_PASS",
        "cases": len(rows), "new_target": 1, "occupied_refusals": 4, "parent_boundaries": 1,
        "uid": os.getuid(), "platform": platform.platform(),
        "scope": "Linux kernel primitive only; not CMPCT Reader or existing-output replacement"
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
