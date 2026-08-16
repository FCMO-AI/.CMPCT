#!/usr/bin/env python3
"""Cross-check the native read/preflight/extract CLI against the Python revision-24 oracle."""

from __future__ import annotations

import json
import shutil
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
                "link_target": row[6][0] if row[1] == 3 else None,
            }
            for row in archive.files
        ]
        assert native_entries == expected, (native_entries, expected)
        assert info_payload["entries"] == len(expected)

        stat = run("stat", str(ARCHIVE), "payload.bin")
        assert stat.returncode == 0, stat.stderr.decode()
        assert json.loads(stat.stdout) == next(
            row for row in expected if row["path"] == "payload.bin"
        )

        preflight = run("preflight", str(ARCHIVE))
        assert preflight.returncode == 0, preflight.stderr.decode()
        preflight_payload = json.loads(preflight.stdout)
        assert preflight_payload == {
            "entries": len(expected),
            "preflight": "ok",
            "revision": 24,
        }

        whole = run("read", str(ARCHIVE), "payload.bin")
        assert whole.returncode == 0, whole.stderr.decode()
        assert whole.stdout == archive.read("payload.bin")

        offset = 333_333
        length = 8_192
        ranged = run("range", str(ARCHIVE), "raw.bin", str(offset), str(length))
        assert ranged.returncode == 0, ranged.stderr.decode()
        assert ranged.stdout == archive.read_range("raw.bin", offset, length)

        # Native extraction is deliberately checked with the same ordinary builder archive used for
        # C-ABI parity. This keeps the CLI test focused on command wiring while the dedicated ABI gate
        # covers hardlinks/symlinks and large sequential streams in more depth.
        destination = Path("/tmp/cmpct-native-cli-extract")
        shutil.rmtree(destination, ignore_errors=True)
        extracted = run("extract", str(ARCHIVE), str(destination))
        assert extracted.returncode == 0, extracted.stderr.decode()
        extracted_payload = json.loads(extracted.stdout)
        assert extracted_payload["extract"] == "ok"
        assert extracted_payload["revision"] == 24
        for row in archive.files:
            if row[1] != 0:
                continue
            assert (destination / row[0]).read_bytes() == archive.read(row[0])

    missing_stat = run("stat", str(ARCHIVE), "missing.bin")
    assert missing_stat.returncode != 0
    assert missing_stat.stdout == b""

    missing = run("range", str(ARCHIVE), "missing.bin", "0", "1")
    assert missing.returncode != 0
    assert missing.stdout == b""

    directory_read = run("read", str(ARCHIVE), "dir")
    assert directory_read.returncode != 0
    assert directory_read.stdout == b""

    oversized = run("range", str(ARCHIVE), "raw.bin", "0", str(64 * 1024 * 1024 + 1))
    assert oversized.returncode != 0
    assert oversized.stdout == b""


if __name__ == "__main__":
    main()
