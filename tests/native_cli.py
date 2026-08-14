#!/usr/bin/env python3
"""Cross-check the small native read CLI against the Python revision-24 oracle."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cmpct.reader import CMPCT


ARCHIVE = Path("/tmp/native.cmpct")
BINARY = Path("native/cmpct-core/target/release/cmpct-native")


def run(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(BINARY), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    info = run("info", str(ARCHIVE))
    assert info.returncode == 0, info.stderr.decode()
    info_payload = json.loads(info.stdout)
    assert info_payload["revision"] == 24

    listed = run("list", str(ARCHIVE))
    assert listed.returncode == 0, listed.stderr.decode()
    native_entries = json.loads(listed.stdout)

    with CMPCT(ARCHIVE) as archive:
        expected = [
            {
                "path": row[0],
                "kind": row[1],
                "mode": row[2],
                "mtime_ns": row[3],
                "size": row[4],
            }
            for row in archive.files
        ]
        assert native_entries == expected, (native_entries, expected)
        assert info_payload["entries"] == len(expected)

        offset = 333_333
        length = 8_192
        ranged = run("range", str(ARCHIVE), "raw.bin", str(offset), str(length))
        assert ranged.returncode == 0, ranged.stderr.decode()
        assert ranged.stdout == archive.read_range("raw.bin", offset, length)

    missing = run("range", str(ARCHIVE), "missing.bin", "0", "1")
    assert missing.returncode != 0
    assert missing.stdout == b""

    oversized = run("range", str(ARCHIVE), "raw.bin", "0", str(64 * 1024 * 1024 + 1))
    assert oversized.returncode != 0
    assert oversized.stdout == b""


if __name__ == "__main__":
    main()
