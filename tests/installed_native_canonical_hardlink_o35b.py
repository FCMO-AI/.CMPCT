#!/usr/bin/env python3
"""O35b: authenticated mixed-separator hardlink owner from an ACTUAL installed wheel.

Distinct from O35a static destination control. This cannot prove Windows hardlink
inode equivalence, concurrent destination containment, or release promotion.
"""
from __future__ import annotations

import binascii
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

import msgpack
import cmpct
from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_FILE, K_HARDLINK,
    MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

PAYLOAD = b"O35b-authenticated-mixed-owner-\x00\xfe" * 3


def signed_archive(path: Path, targets: dict[str, str]) -> None:
    rows = [["sub/owner.bin", K_FILE, 0o644, 0, len(PAYLOAD), sha(PAYLOAD), [S_BLOB, 0]]]
    rows.extend(
        [alias, K_HARDLINK, 0o644, 0, len(PAYLOAD), sha(PAYLOAD), [target]]
        for alias, target in targets.items()
    )
    index = {
        "v": VERSION,
        "files": sorted(rows, key=lambda row: row[0]),
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
    }
    raw = msgpack.packb(index, use_bin_type=True)
    zipped = zc(raw, 3)
    blob = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xFFFFFFFF, sha(PAYLOAD),
    ) + PAYLOAD
    header = HDR.pack(MAGIC, VERSION, 0, len(zipped), len(raw), len(blob), sha(raw))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(zipped), len(raw), 0, sha(raw))
    path.write_bytes(header + zipped + blob + zipped + footer)


def must_reject(archive: Path, reason: str) -> None:
    try:
        preflight_archive(archive)
    except (OSError, ValueError):
        pass
    else:
        raise AssertionError(f"strict preflight accepted {reason} signed hardlink")
    try:
        with CMPCT(archive):
            pass
    except (OSError, ValueError):
        pass
    else:
        raise AssertionError(f"ordinary wheel Reader accepted {reason} signed hardlink")


def main() -> None:
    assert len(sys.argv) == 2, "usage: installed_native_canonical_hardlink_o35b.py SOURCE_HEAD"
    source_head = sys.argv[1]
    assert len(source_head) == 40 and all(x in "0123456789abcdef" for x in source_head)
    module = Path(cmpct.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    assert module.is_relative_to(prefix), (module, prefix)
    owner_hash = hashlib.sha256(PAYLOAD).hexdigest()
    targets = {
        "alias.bin": "branch\\first.bin",
        "branch/first.bin": "sub\\owner.bin",
        "branch/second.bin": "branch\\first.bin",
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-o35b-installed-") as td:
        root = Path(td)
        archive = root / "mixed-signed-r24.cmpct"
        signed_archive(archive, targets)
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        assert preflight_archive(archive)["files"] == 4
        destination = root / "destination"
        names = ["sub/owner.bin", *targets]
        with CMPCT(archive) as reader:
            assert len(reader.files) == len(names)
            assert reader.verify() == len(names)
            for alias in targets:
                assert reader._hardlink_owners[alias] == "sub/owner.bin"
            for name in names:
                assert reader.read(name) == PAYLOAD, name
                assert reader.read_range(name, 2, 7) == PAYLOAD[2:9], name
                assert bytes(reader.file_sha256(name)).hex() == owner_hash, name
            reader.extractall(destination, metadata=False)
        for name in names:
            assert (destination / name).read_bytes() == PAYLOAD, name
        posix_inode_check = os.name == "posix"
        if posix_inode_check:
            assert len({(destination / name).stat().st_ino for name in names}) == 1
        hostile = root / "unsafe-signed-r24.cmpct"
        signed_archive(hostile, {"alias.bin": "../escape.bin"})
        must_reject(hostile, "parent-escape")
        cycle = root / "cycle-signed-r24.cmpct"
        signed_archive(cycle, {"alias.bin": "branch\\first.bin", "branch/first.bin": "alias.bin"})
        must_reject(cycle, "canonical-cycle")
        assert not (root / "escape.bin").exists()
        assert not (root / "untrusted-publish").exists()
    print(json.dumps({
        "schema": "cmpct-v031-installed-canonical-hardlink-o35b-v1",
        "source_sha": source_head,
        "host_os": platform.system().lower(),
        "installed_module": str(module),
        "wheel_import_under_prefix": True,
        "package_version": importlib.metadata.version("cmpct"),
        "signed_archive_sha256": archive_hash,
        "content_sha256": owner_hash,
        "member_count": 4,
        "canonical_signed_mixed_chain_positive": True,
        "implicit_hardlink_only_parent_restored": True,
        "all_member_content_and_ranges_verified": True,
        "host_posix_inode_identity_confirmed": posix_inode_check,
        "unsafe_parent_target_rejected": True,
        "canonical_cycle_rejected": True,
        "scope": "real installed wheel exact r24 hardlink semantic class; not race-free confinement",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
