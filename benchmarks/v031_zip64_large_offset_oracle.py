#!/usr/bin/env python3
"""O0 ZIP64 wire oracle: true >4 GiB STORED member, late Deflate, bounded RAM.

No CMPCT engine is modified; see 2026-10-23 preregistration.
"""
import binascii
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zipfile
import zlib

SIZE = (1 << 32) + 4096
U32 = 0xFFFFFFFF
PAYLOAD = b"CMPCT ZIP64 late-member reconstruction\\n" * 23
ZIP64_TAG = 1
FLAGS = 0x800
DIR_ATTR = (0o040755 << 16) | 0x10
FILE_ATTR = 0o100644 << 16


def zeros_crc(n):
    slab = b"\0" * (8 << 20)
    result = 0
    q, rem = divmod(n, len(slab))
    for _ in range(q):
        result = zlib.crc32(slab, result)
    return zlib.crc32(slab[:rem], result) & U32


def write_local(f, name, method, data, usize, crc, giant=False):
    offset = f.tell()
    nb = name.encode("utf-8")
    csize = usize if giant else len(data)
    extra = struct.pack("<HHQQ", ZIP64_TAG, 16, usize, csize) if giant else b""
    f.write(struct.pack("<IHHHHHIIIHH", 0x04034B50, 45 if giant else 20,
                        FLAGS, method, 0, 0, crc, U32 if giant else csize,
                        U32 if giant else usize, len(nb), len(extra)))
    f.write(nb)
    f.write(extra)
    if giant:
        assert method == 0 and data == b""
        f.seek(csize, os.SEEK_CUR)  # physically sparse; no giant memory buffer
    else:
        f.write(data)
    return (name, method, csize, usize, crc, offset, giant)


def write_central(f, row, corrupt_offset=False):
    name, method, cs, us, crc, off, giant = row
    name_bytes = name.encode("utf-8")
    need_offset = off > U32
    assert giant == (cs > U32 or us > U32)
    payload = (struct.pack("<QQ", us, cs) if giant else b"")
    if need_offset:
        payload += struct.pack("<Q", 0 if corrupt_offset and name == "late/member" else off)
    extra = struct.pack("<HH", ZIP64_TAG, len(payload)) + payload if payload else b""
    ver = 45 if extra else 20
    f.write(struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50,
                        (3 << 8) | ver, ver, FLAGS, method, 0, 0, crc,
                        U32 if giant else cs, U32 if giant else us,
                        len(name_bytes), len(extra), 0, 0, 0,
                        DIR_ATTR if name.endswith("/") else FILE_ATTR,
                        U32 if need_offset else off))
    f.write(name_bytes)
    f.write(extra)


def produce(path, overflow_count, tamper_offset, crc):
    co = zlib.compressobj(6, zlib.DEFLATED, -15)
    compressed = co.compress(PAYLOAD) + co.flush()
    rows = []
    start = time.perf_counter()
    with path.open("wb") as f:
        rows.append(write_local(f, "huge/zeros", 0, b"", SIZE, crc, giant=True))
        assert f.tell() > U32
        if overflow_count:
            for i in range(65534):
                rows.append(write_local(f, "dir%05d/" % i, 0, b"", 0, 0))
        rows.append(write_local(f, "late/member", 8, compressed, len(PAYLOAD),
                                binascii.crc32(PAYLOAD) & U32))
        end_member = rows[-1][5]
        start_cd = f.tell()
        for row in rows:
            write_central(f, row, corrupt_offset=tamper_offset)
        cd_size = f.tell() - start_cd
        zip64_end = f.tell()
        n = len(rows)
        f.write(struct.pack("<IQHHIIQQQQ", 0x06064B50, 44, 45, 45,
                            0, 0, n, n, cd_size, start_cd))
        f.write(struct.pack("<IIQI", 0x07064B50, 0, zip64_end, 1))
        f.write(struct.pack("<IHHHHIIH", 0x06054B50, 0, 0,
                            min(n, 65535), min(n, 65535), cd_size, U32, 0))
    st = path.stat()
    return {"entries": len(rows), "logical_zip_bytes": st.st_size,
            "allocated_zip_bytes": st.st_blocks * 512, "small_header_offset": end_member,
            "central_directory_offset": start_cd, "central_directory_bytes": cd_size,
            "create_wall_s": round(time.perf_counter() - start, 6)}


def check(path, m, crc):
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        assert len(items) == m["entries"]
        assert items[0].file_size == SIZE
        assert items[0].compress_size == SIZE
        assert items[0].CRC == crc
        tail = items[-1]
        assert tail.header_offset == m["small_header_offset"]
        assert tail.filename == "late/member"
        assert z.read(tail) == PAYLOAD  # verifies Deflate, CRC, exact contents
    u = shutil.which("unzip")
    if u:
        p = subprocess.run([u, "-p", str(path), "late/member"], capture_output=True, timeout=20)
        assert p.returncode == 0 and p.stdout == PAYLOAD, p.stderr[-500:]
    return {"cpython_zipfile": "PASS", "info_zip": "PASS" if u else "UNAVAILABLE",
            "member_sha256": hashlib.sha256(PAYLOAD).hexdigest()}


def main():
    start = time.perf_counter()
    crc = zeros_crc(SIZE)
    out = {"date": "2026-10-23", "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "runtime": sys.version, "host": platform.platform(), "giant_logical_bytes": SIZE,
           "giant_crc32": hex(crc), "cases": {}}
    with tempfile.TemporaryDirectory(prefix="cmpct-zip64-offset-") as d:
        d = Path(d)
        for overflow in (False, True):
            key = "count_plus_offset" if overflow else "offset_only"
            path = d / (key + ".zip")
            m = produce(path, overflow, False, crc)
            # Guard against accidentally allocating a giant *physical* test file.
            assert m["allocated_zip_bytes"] < 32 * (1 << 20), m
            m.update(check(path, m, crc))
            out["cases"][key] = m
            path.unlink()
        path = d / "tampered.zip"
        m = produce(path, False, True, crc)
        try:
            with zipfile.ZipFile(path) as z:
                z.read("late/member")
        except (zipfile.BadZipFile, OSError, EOFError, ValueError, struct.error) as e:
            out["tamper"] = {"result": "REJECTED", "error_class": type(e).__name__}
        else:
            raise AssertionError("corrupt ZIP64 offset unexpectedly read as valid")
    out["elapsed_wall_s"] = round(time.perf_counter() - start, 6)
    out["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out["decision"] = "ZIP64_OFFSET_WIRE_ORACLE_PASS"
    print(json.dumps(out, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
