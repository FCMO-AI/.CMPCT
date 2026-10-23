#!/usr/bin/env python3
"""Secondary preregistered O0: ZIP64 streaming data-descriptor semantics.

No CMPCT Writer/Reader modification. A physically sparse >4 GiB member tests
ZIP64 descriptor layout without allocating or writing 4 GiB of physical data.
"""
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
CONTENT = b"CMPCT ZIP64 stream descriptor late-member\\n" * 23
SIGNATURE = 0x08074B50
FLAGS = 0x808  # UTF-8 and GP bit 3: sizes/CRC follow as data descriptors.


def crc_for_zero_bytes(n):
    slab = b"\0" * (8 << 20)
    q, r = divmod(n, len(slab))
    crc = 0
    for _ in range(q):
        crc = zlib.crc32(slab, crc)
    return zlib.crc32(slab[:r], crc) & 0xffffffff


def construct(path, crc_big, bad_descriptor=False):
    co = zlib.compressobj(6, zlib.DEFLATED, -15)
    compressed = co.compress(CONTENT) + co.flush()
    crc_small = zlib.crc32(CONTENT) & 0xffffffff
    name1, name2 = b"huge/zeros.bin", b"late/payload.txt"
    with path.open("wb") as f:
        extra1 = struct.pack("<HHQQ", 1, 16, 0, 0)  # sizes unknown at local-header time
        f.write(struct.pack("<IHHHHHIIIHH", 0x04034B50, 45, FLAGS, 0, 0, 0,
                            0, 0xffffffff, 0xffffffff, len(name1), len(extra1)))
        f.write(name1)
        f.write(extra1)
        f.seek(SIZE, os.SEEK_CUR)  # bytes exist logically but occupy sparse holes
        big_dd = f.tell()
        f.write(struct.pack("<IIQQ", SIGNATURE, crc_big, SIZE, SIZE))
        second_off = f.tell()
        f.write(struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, FLAGS, 8, 0, 0,
                            0, 0, 0, len(name2), 0))
        f.write(name2)
        f.write(compressed)
        small_dd = f.tell()
        altered_crc = crc_small ^ int(bad_descriptor)
        f.write(struct.pack("<IIII", SIGNATURE, altered_crc, len(compressed), len(CONTENT)))
        cd_start = f.tell()
        for name, method, cs, us, crc, off, extra, ver in (
            (name1, 0, SIZE, SIZE, crc_big, 0, struct.pack("<HHQQ", 1, 16, SIZE, SIZE), 45),
            (name2, 8, len(compressed), len(CONTENT), crc_small, second_off,
             struct.pack("<HHQ", 1, 8, second_off), 45),
        ):
            f.write(struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, (3 << 8) | ver,
                                ver, FLAGS, method, 0, 0, crc,
                                0xffffffff if method == 0 else cs,
                                0xffffffff if method == 0 else us,
                                len(name), len(extra), 0, 0, 0, 0o100644 << 16,
                                0xffffffff if off > 0xffffffff else off))
            f.write(name)
            f.write(extra)
        cd_size = f.tell() - cd_start
        zip64_pos = f.tell()
        f.write(struct.pack("<IQHHIIQQQQ", 0x06064B50, 44, 45, 45,
                            0, 0, 2, 2, cd_size, cd_start))
        f.write(struct.pack("<IIQI", 0x07064B50, 0, zip64_pos, 1))
        f.write(struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, 2, 2, cd_size, 0xffffffff, 0))
    with path.open("rb") as f:
        # Distinct byte-level court: readers passing is not enough to prove DD integrity.
        f.seek(0)
        first = f.read(30)
        assert struct.unpack("<IHH", first[:8]) == (0x04034B50, 45, FLAGS)
        f.seek(big_dd)
        assert struct.unpack("<IIQQ", f.read(24)) == (SIGNATURE, crc_big, SIZE, SIZE)
        f.seek(small_dd)
        assert struct.unpack("<IIII", f.read(16)) == (
            SIGNATURE, altered_crc, len(compressed), len(CONTENT))
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        assert len(members) == 2
        assert members[0].file_size == SIZE
        assert members[-1].header_offset == second_off
        assert z.read("late/payload.txt") == CONTENT
    tool = shutil.which("unzip")
    independent = "UNAVAILABLE"
    if tool:
        p = subprocess.run([tool, "-p", str(path), "late/payload.txt"],
                           capture_output=True, timeout=20)
        assert p.returncode == 0 and p.stdout == CONTENT, p.stderr[-300:]
        independent = "PASS"
    st = path.stat()
    assert st.st_blocks * 512 < 32 * (1 << 20), "filesystem cannot make sparse court cheaply"
    return {"tampered_data_descriptor_crc": bad_descriptor,
            "descriptor_crc": hex(altered_crc), "central_crc": hex(crc_small),
            "logical_zip_bytes": st.st_size, "allocated_zip_bytes": st.st_blocks * 512,
            "large_descriptor_offset": big_dd, "late_local_offset": second_off,
            "late_descriptor_offset": small_dd, "cpython": "PASS",
            "info_zip": independent, "late_sha256": hashlib.sha256(CONTENT).hexdigest()}


def main():
    t0 = time.perf_counter()
    big_crc = crc_for_zero_bytes(SIZE)
    out = {"source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "python": sys.version, "host": platform.platform(), "big_crc32": hex(big_crc)}
    with tempfile.TemporaryDirectory(prefix="cmpct-zip64-descriptor-") as temp:
        for tamper in (False, True):
            path = Path(temp) / ("bad-dd.zip" if tamper else "valid.zip")
            out["tampered_dd" if tamper else "valid"] = construct(path, big_crc, tamper)
            path.unlink()
    out["elapsed_wall_s"] = round(time.perf_counter() - t0, 6)
    out["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out["observation"] = "Readers accepted tampered descriptor CRC" if out["tampered_dd"]["cpython"] == "PASS" and out["tampered_dd"]["info_zip"] == "PASS" else "Mixed reader behavior"
    out["decision"] = "ZIP64_STREAM_DESCRIPTOR_WIRE_PASS_AND_DD_CRC_NOT_INDEPENDENTLY_ENFORCED"
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
