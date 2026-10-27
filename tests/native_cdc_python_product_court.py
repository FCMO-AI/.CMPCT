#!/usr/bin/env python3
"""J24N04b: forced optional native CDC through installed Python Builder/Reader.

Linux/ELF scoped; C source blobs pinned to Git, not a mock of the extension.
Worker arms are fresh Python interpreters to avoid ctypes/CDLL lifetime leakage.
Historical original source is compared to corrected source on the same bytes.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PARENT = "b0be37721a7defbb570b2b3920a7924abb37379b"
PARENT_BLOB = "216189c6a15f1579d596bc4df5128ae63f794168"
CANDIDATE_BLOB = "05c840bb27a07c148be7a1ad8f2387397f4b70bc"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command(*args: str, input_data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(args, input=input_data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, cwd=ROOT, check=False, timeout=240)
    if proc.returncode:
        raise RuntimeError(f"Command {args!r} rc={proc.returncode}; "
                           f"stdout={proc.stdout[-3000:]!r}; stderr={proc.stderr[-3000:]!r}")
    return proc


def source_blob(data: bytes) -> str:
    return command("git", "hash-object", "--stdin", input_data=data).stdout.decode().strip()


def run_worker(mode: str, expected_so_sha: str) -> None:
    import cmpct.codec as codec
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.codec import S_CDC

    if mode == "fallback":
        assert codec._cdc is None, "fallback subprocess unexpectedly loaded optional native CDC"
    else:
        assert codec._cdc is not None, "forced subprocess did not load optional native CDC"
        so_path = Path(codec._cdc._name)
        assert so_path.name == "libcmpct_cdc.so" and sha(so_path.read_bytes()) == expected_so_sha, (
            "wrong installed optional CDC .so loaded", so_path)

    witness = bytes.fromhex("00de1a53f01163") + bytes(range(1, 65))
    payload = random.Random(240127).randbytes(3 * 1024 * 1024)

    def cut(data: bytes, minimum: int, average: int, maximum: int) -> list[int]:
        assert len(data) > maximum, "must actually exercise ctypes dispatch"
        parts = codec.cdc_chunks(data, minimum, average, maximum)
        assert b"".join(parts) == data, "Python cdc_chunks lost logical bytes"
        sizes = [len(x) for x in parts]
        assert all(s > 0 for s in sizes)
        if mode != "fallback":
            cap = max(4, len(data) // max(1, minimum) + 4)
            output = (ctypes.c_uint64 * cap)()
            input_buf = ctypes.create_string_buffer(data)
            count = int(codec._cdc.cmpct_cdc_cut(
                input_buf, len(data), minimum, average, maximum, output, cap))
            assert count > 0 and count <= cap, (mode, len(data), count)
            direct = [int(output[i]) for i in range(count)]
            assert direct and direct[-1] == len(data), (mode, direct[-5:])
            prev = 0
            direct_sizes = []
            for end in direct:
                assert prev < end <= len(data) and end - prev <= maximum
                direct_sizes.append(end - prev)
                prev = end
            assert direct_sizes == sizes, (mode, "Python wrapper differs from native C cuts")
        return sizes

    small_sizes = cut(witness, 1, 1, 7)
    ordinary_sizes = cut(payload, codec.CDC_MIN, codec.CDC_AVG, codec.CDC_MAX)

    with tempfile.TemporaryDirectory(prefix="j24n04b-archive-") as temporary:
        temp = Path(temporary)
        source = temp / "tree"
        source.mkdir()
        (source / "payload.bin").write_bytes(payload)
        archive = temp / "product.cmpct"
        outcome = Builder(source, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            row = reader.by["payload.bin"]
            assert row[6][0] == S_CDC, "genuine Builder must choose S_CDC storage"
            raw = reader.read("payload.bin")
            assert raw == payload, "Reader full reconstruction mismatch"
            assert reader.read_range("payload.bin", 1024 * 1024 - 9, 31) == payload[1024*1024-9:1024*1024+22]
            assert reader.verify() == 1, "whole-archive verification wrong"
            signed_geometry = [int(length) for length, _ in row[6][1]]
            assert signed_geometry == ordinary_sizes, "Builder did not consume same native Python chunks"
        receipt = {
            "schema": "j24n04b-forced-native-installed-python-v1",
            "source_mode": mode,
            "native_loaded": codec._cdc is not None,
            "optional_library_sha256": expected_so_sha if mode != "fallback" else None,
            "package_codec": str(Path(codec.__file__).resolve()),
            "witness_n_gt_max": len(witness) > 7,
            "witness_chunk_lengths": small_sizes,
            "ordinary_chunk_lengths": ordinary_sizes,
            "ordinary_chunk_count": len(ordinary_sizes),
            "ordinary_geometry_sha256": sha(json.dumps(ordinary_sizes).encode()),
            "input_sha256": sha(payload),
            "logical_length": len(payload),
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": sha(archive.read_bytes()),
            "signed_storage_mode": row[6][0],
            "logical_sha256": sha(raw),
            "verified": 1,
            "builder_report_bytes": outcome["bytes"],
        }
        assert receipt["builder_report_bytes"] == receipt["archive_bytes"]
        print("J24N04B_JSON " + json.dumps(receipt, sort_keys=True), flush=True)


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        run_worker(sys.argv[2], sys.argv[3])
        return
    if len(sys.argv) != 1:
        raise SystemExit("usage: native_cdc_python_product_court.py [--worker mode sha]")
    assert os.name == "posix" and sys.platform.startswith("linux"), "ELF integration court is Linux scoped"
    assert command("git", "rev-parse", "HEAD:native/cmpct_cdc.c").stdout.decode().strip() == CANDIDATE_BLOB

    # This file must be absent before/after; all temporary injected native code is
    # built only in Actions' disposable checkout, never committed to CMPCT.
    target = ROOT / "src" / "cmpct" / "libcmpct_cdc.so"
    assert not target.exists(), f"unexpected optional native library at {target}"
    parent_source = command("git", "show", f"{PARENT}:native/cmpct_cdc.c").stdout
    candidate_source = (ROOT / "native" / "cmpct_cdc.c").read_bytes()
    assert source_blob(parent_source) == PARENT_BLOB
    assert source_blob(candidate_source) == CANDIDATE_BLOB
    receipts = {}
    with tempfile.TemporaryDirectory(prefix="j24n04b-compiled-") as temporary:
        build_root = Path(temporary)
        for mode, source in (("parent", parent_source), ("candidate", candidate_source)):
            cfile = build_root / f"{mode}.c"
            library = build_root / f"{mode}.so"
            cfile.write_bytes(source)
            command("cc", "-std=c11", "-O2", "-fPIC", "-shared", "-Wall", "-Wextra",
                    "-Werror", str(cfile), "-o", str(library))
            expected = sha(library.read_bytes())
            try:
                shutil.copyfile(library, target)
                assert sha(target.read_bytes()) == expected
                proc = command(sys.executable, str(Path(__file__).resolve()), "--worker", mode, expected)
                lines = proc.stdout.decode().splitlines()
                labeled = [line.removeprefix("J24N04B_JSON ") for line in lines
                           if line.startswith("J24N04B_JSON ")]
                assert len(labeled) == 1, (mode, proc.stdout[-3000:], proc.stderr[-3000:])
                receipts[mode] = json.loads(labeled[0])
            finally:
                target.unlink(missing_ok=True)
        proc = command(sys.executable, str(Path(__file__).resolve()), "--worker", "fallback", "none")
        labeled = [line.removeprefix("J24N04B_JSON ") for line in proc.stdout.decode().splitlines()
                   if line.startswith("J24N04B_JSON ")]
        assert len(labeled) == 1, proc.stdout[-3000:]
        receipts["fallback"] = json.loads(labeled[0])
    assert not target.exists(), "temporary optional native library leaked"
    base = receipts["parent"]
    new = receipts["candidate"]
    fall = receipts["fallback"]
    assert base["native_loaded"] and new["native_loaded"] and not fall["native_loaded"]
    equal_fields = (
        "input_sha256", "logical_length", "witness_chunk_lengths",
        "ordinary_chunk_lengths", "ordinary_geometry_sha256",
        "archive_bytes", "archive_sha256", "logical_sha256", "verified",
        "signed_storage_mode"
    )
    for field in equal_fields:
        assert base[field] == new[field], (field, base[field], new[field])
    for mode in ("candidate", "parent", "fallback"):
        r = receipts[mode]
        assert r["input_sha256"] == r["logical_sha256"]
        assert r["verified"] == 1 and r["signed_storage_mode"] == 5
    assert base["optional_library_sha256"] != new["optional_library_sha256"]
    assert fall["witness_n_gt_max"]
    output = {
        "schema": "j24n04b-source-locked-python-path-v1",
        "parent_source_blob": PARENT_BLOB,
        "candidate_source_blob": CANDIDATE_BLOB,
        "parent_commit": PARENT,
        "results": receipts,
        "decision": "SOURCE_AUTHENTIC_INSTALLED_OPTIONAL_PATH_PARITY",
        "limitations": "Linux x64 optional helper only; default install remains fallback; no production performance claim",
    }
    out = ROOT / "evidence" / "j24n04b-installed-python.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("J24N04B_PRODUCT_INTEGRATION_PASS " +
          json.dumps({"native_archive_sha256":base["archive_sha256"],
                      "archive_bytes":base["archive_bytes"],
                      "segments":base["ordinary_chunk_count"],
                      "fallback_segments":fall["ordinary_chunk_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
