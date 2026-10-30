#!/usr/bin/env python3
"""Read-only physical compatibility gate for CMPCT macOS wheels.

Checks PEP 427 WHEEL/RECORD, physical Mach-O architectures/subtypes and
architecture-specific deployment minima. No CMPCT import or macOS tools.
This certifies metadata against stored bytes, NOT runtime loader, signatures,
SDK behavior, historical builds, or future OS compatibility.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

ARCHES = {0x01000007: "x86_64", 0x0100000C: "arm64"}
GENERIC = {"x86_64": 3, "arm64": 0}
MAGIC = {
    b"\xcf\xfa\xed\xfe": ("<", "thin"),
    b"\xfe\xed\xfa\xcf": (">", "thin"),
    b"\xca\xfe\xba\xbe": (">", "fat32"),
    b"\xbe\xba\xfe\xca": ("<", "fat32"),
    b"\xca\xfe\xba\xbf": (">", "fat64"),
    b"\xbf\xba\xfe\xca": ("<", "fat64"),
}
MAX_WHEEL = 128 * 1024 * 1024
MAX_MEMBER = 64 * 1024 * 1024
MAX_UNCOMPRESSED = 192 * 1024 * 1024
MAX_ENTRIES = 1024


def reject(message: str) -> None:
    raise ValueError(message)


def version(value: int) -> tuple[int, int, int]:
    return (value >> 16, (value >> 8) & 255, value & 255)


def parse_thin(buf: bytes) -> dict:
    if len(buf) < 32 or buf[:4] not in MAGIC or MAGIC[buf[:4]][1] != "thin":
        reject("not a bounded 64-bit Mach-O slice")
    endian = MAGIC[buf[:4]][0]
    cpu, subtype, ftype, ncmds, cmdsz = struct.unpack_from(endian + "IIIII", buf, 4)
    name = ARCHES.get(cpu)
    if name is None or (subtype & 0x00FFFFFF) != GENERIC[name]:
        reject("unknown or architecture-restricted CPU subtype")
    if ftype not in (6, 8):
        reject("not an executable native dylib/bundle")
    if ncmds < 1 or ncmds > 2048 or cmdsz < 16 or cmdsz > len(buf) - 32:
        reject("Mach-O load command region out of bounds")
    pos, end = 32, 32 + cmdsz
    minima: list[tuple[int, int, int]] = []
    for _ in range(ncmds):
        if pos + 8 > end:
            reject("truncated Mach-O load command")
        cmd, length = struct.unpack_from(endian + "II", buf, pos)
        if length < 8 or pos + length > end or length % 4:
            reject("invalid Mach-O load command size")
        if cmd == 0x32:  # LC_BUILD_VERSION
            if length < 24:
                reject("truncated LC_BUILD_VERSION")
            platform, minimum = struct.unpack_from(endian + "II", buf, pos + 8)
            if platform != 1:  # PLATFORM_MACOS
                reject("native Mach-O slice is not for macOS")
            minima.append(version(minimum))
        elif cmd == 0x24:  # LC_VERSION_MIN_MACOSX
            if length < 16:
                reject("truncated LC_VERSION_MIN_MACOSX")
            minima.append(version(struct.unpack_from(endian + "I", buf, pos + 8)[0]))
        pos += length
    if pos != end or len(minima) != 1 or minima[0][0] == 0:
        reject("missing, ambiguous or malformed macOS deployment target")
    return {"arch": name, "subtype": subtype & 0x00FFFFFF, "min_os": minima[0]}


def physical_slices(data: bytes) -> dict[str, dict]:
    if len(data) < 32 or data[:4] not in MAGIC:
        reject("native member is not Mach-O")
    endian, kind = MAGIC[data[:4]]
    if kind == "thin":
        result = parse_thin(data)
        return {result["arch"]: result}
    n = struct.unpack_from(endian + "I", data, 4)[0]
    if not 1 <= n <= 16:
        reject("invalid fat slice count")
    fmt = endian + ("IIQQII" if kind == "fat64" else "IIIII")
    stride = struct.calcsize(fmt)
    header_end = 8 + stride * n
    if header_end > len(data):
        reject("truncated fat architecture table")
    result, ranges = {}, []
    for i in range(n):
        fields = struct.unpack_from(fmt, data, 8 + i * stride)
        cpu, subtype, offset, length, alignment = fields[:5]
        if alignment > 30 or offset % (1 << alignment):
            reject("invalid fat slice alignment")
        if length < 32 or offset < header_end or offset + length > len(data):
            reject("invalid fat slice geometry")
        if any(offset < hi and lo < offset + length for lo, hi in ranges):
            reject("overlapping fat slices")
        ranges.append((offset, offset + length))
        part = parse_thin(data[offset:offset + length])
        if cpu not in ARCHES or ARCHES[cpu] != part["arch"] or (subtype & 0xFFFFFF) != part["subtype"]:
            reject("fat arch header and embedded Mach-O disagree")
        if part["arch"] in result:
            reject("duplicate native architecture")
        result[part["arch"]] = part
    return result


def _checked_record(z: zipfile.ZipFile, infos: list[zipfile.ZipInfo]) -> None:
    record_names = [i.filename for i in infos if i.filename.endswith(".dist-info/RECORD")]
    if len(record_names) != 1:
        reject("wheel must contain one RECORD")
    record_name = record_names[0]
    if z.getinfo(record_name).file_size > 1024 * 1024:
        reject("RECORD too large")
    try:
        rows = list(csv.reader(io.StringIO(z.read(record_name).decode("utf-8"))))
    except (UnicodeError, csv.Error) as exc:
        reject(f"bad RECORD: {exc}")
    entries = {}
    for row in rows:
        if len(row) != 3 or row[0] in entries:
            reject("bad or repeated RECORD row")
        entries[row[0]] = row[1:]
    names = {i.filename for i in infos}
    if names != set(entries):
        reject("RECORD paths differ from ZIP membership")
    for info in infos:
        # RECORD itself is intentionally unhashed under PEP 427.
        if info.filename == record_name:
            if entries[record_name] != ["", ""]:
                reject("self-hashed RECORD not supported")
            continue
        digest, count = entries[info.filename]
        if not digest.startswith("sha256=") or not count.isdecimal() or int(count) != info.file_size:
            reject("missing or wrong RECORD identity")
        encoded = base64.urlsafe_b64encode(hashlib.sha256(z.read(info)).digest()).rstrip(b"=").decode()
        if digest != "sha256=" + encoded:
            reject("wheel member does not match RECORD")


def inspect(path: Path) -> dict:
    name = path.name
    if not name.startswith("cmpct-") or not name.endswith(".whl"):
        reject("not a CMPCT wheel filename")
    segments = name[:-4].rsplit("-", 3)
    if len(segments) != 4:
        reject("invalid wheel tag grammar")
    _, python_tag, abi, platform = segments
    m = re.fullmatch(r"macosx_(\d+)_(\d+)_(universal2|x86_64|arm64)", platform)
    if not m:
        reject("not an understood macOS wheel platform tag")
    major, minor, platform_arch = int(m[1]), int(m[2]), m[3]
    if major < 10 or major > 99 or minor > 99 or abi == "":
        reject("invalid macOS wheel version/tag")
    platform_min = (major, minor, 0)
    required = {"arm64", "x86_64"} if platform_arch == "universal2" else {platform_arch}
    if path.stat().st_size > MAX_WHEEL:
        reject("wheel too large for bounded audit")
    with zipfile.ZipFile(path, allowZip64=True) as z:
        infos = z.infolist()
        if len(infos) > MAX_ENTRIES or len({i.filename for i in infos}) != len(infos):
            reject("too many or duplicate ZIP entries")
        if any(i.file_size > MAX_MEMBER or i.is_dir() for i in infos):
            reject("unexpected large or directory wheel member")
        if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
            reject("wheel uncompressed size exceeds audit limit")
        _checked_record(z, infos)
        native = [i.filename for i in infos if i.filename.startswith("cmpct/cmpct_core") and i.filename.endswith((".so", ".dylib"))]
        if len(native) != 1:
            reject("ambiguous or absent native binary")
        wheel_meta = [i.filename for i in infos if i.filename.endswith(".dist-info/WHEEL")]
        if len(wheel_meta) != 1:
            reject("missing or ambiguous WHEEL metadata")
        lines = z.read(wheel_meta[0]).decode("utf-8").splitlines()
        tags = [line[5:].strip() for line in lines if line.startswith("Tag: ")]
        if not tags or any(tag.split("-")[-1] != platform for tag in tags):
            reject("internal WHEEL platform tags disagree with filename")
        expected_python_tags = set(python_tag.split("."))
        if not expected_python_tags or any(t.split("-")[0] not in expected_python_tags or len(t.split("-")) != 3 for t in tags):
            reject("internal WHEEL Python tags disagree with filename")
        if any(t.split("-")[1] not in abi.split(".") for t in tags):
            reject("internal WHEEL ABI tags disagree with filename")
        binary = z.read(native[0])
        physical = physical_slices(binary)
    if not required.issubset(physical):
        reject("wheel advertises missing physical architecture(s): " + ",".join(sorted(required - set(physical))))
    for arch in required:
        minimum_allowed = max(platform_min, (11, 0, 0)) if arch == "arm64" else platform_min
        if physical[arch]["min_os"] > minimum_allowed:
            reject(f"{arch} minimum macOS {physical[arch]['min_os']} exceeds declared {minimum_allowed}")
    return {"pass": True, "wheel": name, "wheel_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "native_member": native[0], "native_sha256": hashlib.sha256(binary).hexdigest(),
            "platform": platform, "required": sorted(required), "physical": physical,
            "claim_scope": "physical wheel ABI and RECORD only; not runtime Intel/ARM launch, signature or source provenance"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wheel", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = inspect(args.wheel)
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError, UnicodeError, EOFError) as exc:
        result = {"pass": False, "wheel": args.wheel.name, "reason": str(exc)}
    contents = json.dumps(result, indent=2, sort_keys=True)
    print(contents)
    if args.output:
        args.output.write_text(contents + "\n")
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
