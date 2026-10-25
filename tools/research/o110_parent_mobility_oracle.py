"""O110 POSIX directory-ancestry mobility lower-rung counterexample.
Exploratory local observation, not an installed CMPCT test or a new product claim.
Runs exclusively inside TemporaryDirectory; Linux openat2 check is architecture gated.
"""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile

class OpenHow(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_uint64), ("mode", ctypes.c_uint64), ("resolve", ctypes.c_uint64)]

def linux_openat2(dirfd, rel):
    # Linux x86-64/aarch64 syscall 437; RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS.
    h = OpenHow(os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600, 0x08 | 0x04)
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(ctypes.c_long(437), ctypes.c_int(dirfd),
                      ctypes.c_char_p(rel.encode()), ctypes.byref(h),
                      ctypes.c_size_t(ctypes.sizeof(h)))
    if fd < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return fd

def main():
    observation = {
        "scope": "exploratory POSIX kernel primitive; NOT CMPCT installed-product evidence",
        "system": platform.system(),
        "machine": platform.machine()
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-o110-") as temp:
        root = Path(temp)
        source = root / "source"
        output = root / "outside"
        source.mkdir()
        output.mkdir()
        content = b"P" * 4096
        (source / "payload").write_bytes(content)
        alias = root / "outlink"
        alias.symlink_to(output, target_is_directory=True)
        assert not (output == source or source in output.parents)
        before = os.stat(output)
        dirfd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            # Adversary has rename rights over both parents; moves the SAME inode.
            moved = source / "moved"
            os.rename(output, moved)
            alias.unlink()
            alias.symlink_to(moved, target_is_directory=True)
            after = os.fstat(dirfd)
            assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
            assert moved.parent == source
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
            fd = os.open("openat.cmpct", flags, 0o600, dir_fd=dirfd)
            os.write(fd, b"openat")
            os.close(fd)
            assert (moved / "openat.cmpct").read_bytes() == b"openat"
            observation["dirfd_identity_preserved_but_ancestry_changed"] = True
            if platform.system() == "Linux" and platform.machine() in ("x86_64", "aarch64"):
                try:
                    fd = linux_openat2(dirfd, "openat2.cmpct")
                    os.write(fd, b"openat2")
                    os.close(fd)
                    assert (moved / "openat2.cmpct").read_bytes() == b"openat2"
                    try:
                        escaped = linux_openat2(dirfd, "../escape")
                    except OSError as exc:
                        assert exc.errno in (errno.EXDEV, errno.ELOOP, errno.EPERM)
                    else:
                        os.close(escaped)
                        raise AssertionError("RESOLVE_BENEATH did not reject parent escape")
                    observation["openat2_beneath_does_not_fix_external_ancestry"] = True
                    observation["openat2_rejects_relative_parent_escape"] = True
                except OSError as exc:
                    observation["openat2_unavailable"] = str(exc)
            assert (source / "payload").read_bytes() == content
            observation["source_payload_sha256"] = hashlib.sha256(content).hexdigest()
            observation["output_objects_now_within_source"] = sorted(p.name for p in moved.iterdir())
        finally:
            os.close(dirfd)
    print(json.dumps(observation, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
