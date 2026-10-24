#!/usr/bin/env python3
"""O32: prove POSIX static destination pivot refusal from the actual installed wheel.

Research court only: this does not prove race-free containment, whole-tree
atomicity, Windows reparse safety, or hardlink-alias containment.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

import cmpct
from cmpct.builder import Builder
from cmpct.reader import CMPCT


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require(len(sys.argv) == 2, "usage: installed_native_static_destination_smoke.py EXACT_HEAD")
    expected_head = sys.argv[1]
    require(len(expected_head) == 40 and all(ch in "0123456789abcdef" for ch in expected_head),
            "invalid exact source SHA")
    require(os.name == "posix" and platform.system() in {"Linux", "Darwin"},
            "the POSIX installed static destination court must not be run on Windows")
    module = Path(cmpct.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    require(module.is_relative_to(prefix), f"CMPCT import is not from isolated wheel: {module}")

    with tempfile.TemporaryDirectory(prefix="cmpct-o32-installed-pivot-") as tmp:
        root = Path(tmp)
        source = root / "source"
        (source / "z-last").mkdir(parents=True)
        ordinary = b"EARLY-MEMBER-O32"
        owner = b"HARDLINK-OWNER-O32"
        (source / "a-first.bin").write_bytes(ordinary)
        (source / "owner.bin").write_bytes(owner)
        os.link(source / "owner.bin", source / "alias.bin")
        (source / "member.lnk").symlink_to("owner.bin")
        (source / "z-last" / "member.bin").write_bytes(b"LATE-MEMBER-O32")
        archive = root / "authentic-r24.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        archive_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()

        outside = root / "outside"
        outside.mkdir()
        sentinel = outside / "member.bin"
        unchanged = b"EXTERNAL-O32-SENTINEL"
        sentinel.write_bytes(unchanged)
        sentinel_stat = sentinel.stat()
        sentinel_sha256 = hashlib.sha256(unchanged).hexdigest()
        destination = root / "destination"
        destination.mkdir()
        pivot = destination / "z-last"
        pivot.symlink_to(outside, target_is_directory=True)

        with CMPCT(archive) as reader:
            require(reader.read("a-first.bin") == ordinary, "signed ordinary read mismatch")
            require(reader.verify() >= 4, "strong verification did not cover archive")
            try:
                reader.extractall(destination, safe_symlinks=True, metadata=False)
            except OSError as exc:
                require("pre-existing destination symlink" in str(exc),
                        f"unexpected exception class/policy: {exc}")
            else:
                raise AssertionError("installed wheel accepted pre-existing destination pivot")

            for name in ("a-first.bin", "owner.bin", "alias.bin", "member.lnk"):
                require(not os.path.lexists(destination / name),
                        f"ordinary member published before reject: {name}")
            require(sentinel.read_bytes() == unchanged, "outside sentinel content changed")
            require(sentinel.stat().st_ino == sentinel_stat.st_ino,
                    "outside sentinel inode replaced")
            require(hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_sha256,
                    "outside sentinel digest changed")

            pivot.unlink()
            reader.extractall(destination, safe_symlinks=True, metadata=False)

        require((destination / "a-first.bin").read_bytes() == ordinary,
                "valid ordinary member not restored")
        require((destination / "z-last" / "member.bin").read_bytes() == b"LATE-MEMBER-O32",
                "valid nested member not restored")
        require((destination / "owner.bin").read_bytes() == owner
                and (destination / "alias.bin").read_bytes() == owner,
                "hardlink content mismatch")
        require((destination / "owner.bin").stat().st_ino ==
                (destination / "alias.bin").stat().st_ino,
                "hardlink physical identity mismatch")
        require((destination / "member.lnk").is_symlink()
                and os.readlink(destination / "member.lnk") == "owner.bin",
                "legitimate symlink not reconstructed")
        require(sentinel.read_bytes() == unchanged and
                sentinel.stat().st_ino == sentinel_stat.st_ino,
                "safe reconstruction mutated outside sentinel")

        print(json.dumps({
            "schema": "cmpct-v031-installed-wheel-static-destination-o32-v1",
            "source_sha": expected_head,
            "host_os": platform.system().lower(),
            "installed_module": str(module),
            "wheel_import_under_prefix": True,
            "package_version": importlib.metadata.version("cmpct"),
            "archive_sha256": archive_sha256,
            "outside_sentinel_sha256": sentinel_sha256,
            "negative_result": "prewrite_rejected",
            "positive_result": "exact_inode_reconstruction",
            "prewrite_no_ordinary_members": True,
            "external_inode_sha_unchanged": True,
            "scope": "real POSIX installed-wheel static guard; not TOCTOU-safe, not Windows",
        }, sort_keys=True))


if __name__ == "__main__":
    main()
