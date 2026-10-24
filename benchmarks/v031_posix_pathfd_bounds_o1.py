#!/usr/bin/env python3
"""Detached Linux/POSIX pathname oracle; no CMPCT product or format changes.

Shows why a name-preserving byte manifest alone does not guarantee reconstruction:
near-PATH_MAX raw relative names can be created by dirfd descent, while a
root-prefixed absolute pathname fails, even when all components are legal.
"""
import errno
import json
import os
import tempfile


def run():
    if os.name != "posix" or not hasattr(os, "supports_dir_fd") or os.mkdir not in os.supports_dir_fd:
        return {"status": "SKIPPED", "reason": "requires dir_fd mkdir/open support"}
    parts = [bytes([0xff - (i % 12)]) * 255 for i in range(16)]
    relative = b"/".join(parts)
    assert len(relative) == 4095 and all(b"/" not in p and b"\0" not in p and len(p) == 255 for p in parts)
    with tempfile.TemporaryDirectory() as temp:
        root = os.fsencode(temp)
        opened = [os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))]
        try:
            for part in parts:
                os.mkdir(part, 0o700, dir_fd=opened[-1])
                opened.append(os.open(part, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0), dir_fd=opened[-1]))
            assert os.fstat(opened[-1]).st_ino
            absolute_status = "UNEXPECTED_SUCCESS"
            try:
                os.stat(root + b"/" + relative)
            except OSError as error:
                absolute_status = "FAIL_ERRNO_" + str(error.errno)
                if error.errno != errno.ENAMETOOLONG:
                    raise
            assert absolute_status == "FAIL_ERRNO_" + str(errno.ENAMETOOLONG), absolute_status
            fd = os.open(b"item", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=opened[-1])
            os.write(fd, b"exact-byte-content")
            os.close(fd)
            assert os.stat(b"item", dir_fd=opened[-1]).st_size == 18
            return {"status": "PASS", "raw_relative_bytes":len(relative),
                    "absolute_prefixed_bytes":len(root)+1+len(relative),
                    "component_max_bytes":255, "components":len(parts),
                    "dirfd_stepwise_create":"PASS", "absolute_stat":absolute_status,
                    "decision":"Absolute joined path materializers cannot fully support legitimate near-limit POSIX paths; safe descriptor-root walk plus explicit resource/rename/symlink policy is required.",
                    "scope":"detached POSIX mechanism only; no CMPCT read/write/format evidence"}
        finally:
            for fd in opened[::-1]:
                os.close(fd)


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
