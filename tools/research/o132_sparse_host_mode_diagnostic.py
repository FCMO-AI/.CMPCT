#!/usr/bin/env python3
"""O132: identify a platform sparse admission gap without modifying parent tests.

This instrument reports real filesystem allocation and SEEK_DATA/Hole outcomes,
then separately observes exact parent Builder.scan and final revision-24 mode.
It does not treat an original macOS red as a passed product test.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_SPARSE, S_CDC, S_BLOB, _sparse_data_extents

SIZE = 16 * 1024 * 1024
EDGE = 4096
REL = "z-last.bin"
MODES = {"S_SPARSE": S_SPARSE, "S_CDC": S_CDC, "S_BLOB": S_BLOB}


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_fixture(path: Path, method: str) -> None:
    with path.open("wb") as f:
        if method == "seek":
            f.write(b"A" * EDGE)
            f.seek(SIZE - EDGE)
            f.write(b"B" * EDGE)
        elif method == "truncate":
            os.ftruncate(f.fileno(), SIZE)
            assert os.pwrite(f.fileno(), b"A" * EDGE, 0) == EDGE
            assert os.pwrite(f.fileno(), b"B" * EDGE, SIZE - EDGE) == EDGE
        elif method == "dense":
            f.write(b"A" * EDGE)
            piece = b"\x00" * (1024 * 1024)
            for _ in range((SIZE - 2 * EDGE) // len(piece)):
                f.write(piece)
            f.write(b"\x00" * ((SIZE - 2 * EDGE) % len(piece)))
            f.write(b"B" * EDGE)
        else:
            raise AssertionError(method)
    assert path.stat().st_size == SIZE


def seek_probe(path: Path) -> dict:
    stats = path.stat()
    data = {
        "size": stats.st_size,
        "st_blocks": getattr(stats, "st_blocks", None),
        "allocated_proxy_bytes": getattr(stats, "st_blocks", 0) * 512,
        "size_gate": stats.st_size >= 1024 * 1024,
        "supports_seek_data": hasattr(os, "SEEK_DATA"),
        "supports_seek_hole": hasattr(os, "SEEK_HOLE"),
    }
    data["allocation_gate"] = (
        bool(getattr(stats, "st_blocks", 0))
        and getattr(stats, "st_blocks", 0) * 512 < stats.st_size * .75
    )
    fd = os.open(path, os.O_RDONLY)
    try:
        for name in ("SEEK_DATA", "SEEK_HOLE"):
            if not hasattr(os, name):
                data[name] = "UNAVAILABLE"
                continue
            out = []
            for pos in (0, EDGE, SIZE // 2, SIZE - EDGE):
                try:
                    out.append({"from": pos, "to": os.lseek(fd, pos, getattr(os, name))})
                except OSError as exc:
                    out.append({"from": pos, "errno": exc.errno, "error": exc.strerror})
            data[name] = out
    finally:
        os.close(fd)
    return data


def storage_name(storage: int) -> str:
    for name, value in MODES.items():
        if storage == value:
            return name
    return "OTHER_" + repr(storage)


def one(root: Path, method: str) -> dict:
    src = root / method / "source"
    src.mkdir(parents=True)
    path = src / REL
    write_fixture(path, method)
    sha = file_sha(path)
    physical = seek_probe(path)
    sparse = _sparse_data_extents(path, SIZE)
    physical["sparse_returned_none"] = sparse is None
    physical["sparse_extents"] = (
        None if sparse is None else
        [{"offset": off, "length": len(chunk),
          "sha256": hashlib.sha256(chunk).hexdigest()} for off, chunk in sparse]
    )
    physical["sparse_extent_bytes"] = (
        None if sparse is None else sum(len(chunk) for _, chunk in sparse)
    )
    scan = Builder(src, workers=1, reproducible=True)
    scan.scan()
    row = next(row for row in scan.files if row[0] == REL)
    scan_mode = storage_name(row[6][0])
    archive = root / (method + ".cmpct")
    outcome = Builder(src, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        final_mode = storage_name(reader.by[REL][6][0])
        verified = reader.verify()
        assert verified == 1, (method, verified)
        dest = root / (method + "-extract")
        reader.extractall(dest, metadata=False)
    actual_sha = file_sha(dest / REL)
    assert actual_sha == sha, (method, actual_sha, sha)
    result = {
        "method": method,
        "source_sha256": sha,
        "source_size": SIZE,
        "physical": physical,
        "scan_storage": scan_mode,
        "final_storage": final_mode,
        "archive_size": archive.stat().st_size,
        "archive_sha256": file_sha(archive),
        "builder_report_bytes": outcome["bytes"],
        "verified_members": verified,
        "extracted_sha256": actual_sha,
        "extract_exact": True,
    }
    print("O132_OBSERVATION " + json.dumps(result, sort_keys=True), flush=True)
    return result


def main() -> None:
    import cmpct.builder
    import cmpct.reader
    import cmpct.codec
    import os as os_module
    out = Path(sys.argv[1])
    observations = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o132-") as tmp:
        root = Path(tmp)
        for method in ("seek", "truncate", "dense"):
            observations.append(one(root, method))
    if len({x["source_sha256"] for x in observations}) != 1:
        raise AssertionError("three original inputs have different logical bytes")
    assert all(x["extract_exact"] for x in observations)
    assert all(x["source_size"] == SIZE for x in observations)
    result = {
        "schema": "cmpct-o132-macos-sparse-host-diagnostic-v1",
        "platform": platform.platform(),
        "python": sys.version,
        "product_modules": {
            "builder": str(Path(cmpct.builder.__file__).resolve()),
            "reader": str(Path(cmpct.reader.__file__).resolve()),
            "codec": str(Path(cmpct.codec.__file__).resolve()),
        },
        "observations": observations,
        "all_same_logical_bytes": True,
        "exact_reconstruction": True,
        "scientific_claim": "host-specific sparse classification measured; not a product fix",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("O132_EXACT_RECONSTRUCTION_AND_CUSTODY_PASS", flush=True)


if __name__ == "__main__":
    main()
