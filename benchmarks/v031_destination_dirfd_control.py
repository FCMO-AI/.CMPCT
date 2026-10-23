"""Independent POSIX directory-capability microcontrol for CMPCT destination safety.

Only proves isolated syscall semantics on the hosting POSIX filesystem; this is
not a production extractor, hostile-race conformance suite, or portability proof.
"""
from __future__ import annotations
import errno
import json
import os
from pathlib import Path
import tempfile

FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
WRITE = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW


def run():
    if not all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_DIRECTORY")):
        raise RuntimeError("requires POSIX O_DIRECTORY and O_NOFOLLOW")
    result = []
    with tempfile.TemporaryDirectory(prefix="cmpct-dirfd-control-") as tmp:
        p = Path(tmp)
        dest = p / "dest"
        outside = p / "outside"
        dest.mkdir()
        outside.mkdir()
        victim = outside / "victim.bin"
        victim.write_bytes(b"ORIGINAL")
        root_fd = os.open(dest, FLAGS)
        try:
            # A symlink masquerading as an already-existing parent cannot
            # become a directory capability via openat(O_NOFOLLOW|O_DIRECTORY).
            (dest / "nested").symlink_to(outside, target_is_directory=True)
            parent_errno = None
            try:
                child = os.open("nested", FLAGS, dir_fd=root_fd)
            except OSError as exc:
                parent_errno = exc.errno
            else:
                os.close(child)
            assert parent_errno in (errno.ELOOP, errno.ENOTDIR), parent_errno
            assert victim.read_bytes() == b"ORIGINAL"
            result.append(dict(case="ancestor_nofollow", status="REJECTED",
                               errno=parent_errno, outside_unchanged=True))
            (dest / "nested").unlink()

            # Opening a preexisting leaf symlink with O_NOFOLLOW must fail.
            (dest / "leaf.bin").symlink_to(victim)
            leaf_errno = None
            try:
                fd = os.open("leaf.bin", WRITE, 0o600, dir_fd=root_fd)
            except OSError as exc:
                leaf_errno = exc.errno
            else:
                os.close(fd)
            assert leaf_errno in (errno.ELOOP, errno.ENOTDIR), leaf_errno
            assert victim.read_bytes() == b"ORIGINAL"

            # Atomic publication via anchored dir_fd replaces the symlink
            # itself rather than truncating its outside target.
            tmp_name = ".cmpct-stage-test"
            fd = os.open(tmp_name, WRITE | os.O_EXCL, 0o600, dir_fd=root_fd)
            os.write(fd, b"SOURCE")
            os.close(fd)
            os.replace(tmp_name, "leaf.bin", src_dir_fd=root_fd,
                       dst_dir_fd=root_fd)
            assert (dest / "leaf.bin").read_bytes() == b"SOURCE"
            assert not (dest / "leaf.bin").is_symlink()
            assert victim.read_bytes() == b"ORIGINAL"
            result.append(dict(case="leaf_nofollow_atomic", status="SAFE_REPLACE",
                               errno=leaf_errno, outside_unchanged=True))

            # A pinned directory handle keeps writing into its original inode
            # after a deliberate one-shot symlink path substitution.
            os.mkdir("stable", dir_fd=root_fd)
            stable_fd = os.open("stable", FLAGS, dir_fd=root_fd)
            try:
                os.rename(dest / "stable", dest / "stable-old")
                (dest / "stable").symlink_to(outside, target_is_directory=True)
                fd = os.open(".cmpct-stage-test", WRITE | os.O_EXCL, 0o600,
                             dir_fd=stable_fd)
                os.write(fd, b"PINNED")
                os.close(fd)
                os.replace(".cmpct-stage-test", "member.bin",
                           src_dir_fd=stable_fd, dst_dir_fd=stable_fd)
                assert (dest / "stable-old" / "member.bin").read_bytes() == b"PINNED"
                assert not (outside / "member.bin").exists()
                assert victim.read_bytes() == b"ORIGINAL"
                result.append(dict(case="parent_path_substitution",
                                   status="ORIGINAL_INODE_PINNED",
                                   outside_unchanged=True))
            finally:
                os.close(stable_fd)
        finally:
            os.close(root_fd)
    return dict(schema="cmpct-dirfd-posix-microcontrol-v1",
                outcome="STATIC_AND_ONESHOT_PIVOTS_CONTAINED_IN_MICROCONTROL",
                cases=result,
                scope="POSIX Linux microcontrol only; no CMPCT product code or "
                      "platform/native/hostile-concurrent adversary proof.")


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
