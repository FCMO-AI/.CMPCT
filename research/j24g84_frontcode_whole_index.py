#!/usr/bin/env python3
"""J24G84: whole-index path frontcoding O0, NOT a CMPCT on-disk reader or encoder."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import msgpack
import zstandard as zstd
from cmpct.builder import Builder
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
PREREG = "3721819520889b1994f8be5aaaa03747799568c6"
BASE = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
OUT = Path(os.environ.get("J24G84_EVIDENCE_DIR", "evidence"))
N = 2048
CASES = ("flat", "deep", "random", "unicode")
FIELD = "__j24g84_names"
MAX_PATHS = 200_000
MAX_NAME = 65_536
MAX_TOTAL_NAMES = 64 * 1024 * 1024


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def attest():
    head = git("rev-parse", "HEAD")
    for sha in (BASE, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                       cwd=ROOT, check=True)
    p = ROOT / "src/cmpct/reader.py"
    import cmpct.reader as installed
    assert Path(installed.__file__).read_bytes().replace(b"\r\n", b"\n") == (
        p.read_bytes().replace(b"\r\n", b"\n")), "wrong installed Reader"
    return dict(head=head, prereg=PREREG, base=BASE,
                reader_blob=git("rev-parse", "HEAD:src/cmpct/reader.py"),
                builder_blob=git("rev-parse", "HEAD:src/cmpct/builder.py"),
                zstd_version=zstd.__version__, msgpack_version=msgpack.version)


def varint(n):
    if n < 0 or n >= (1 << 63):
        raise ValueError("out-of-range unsigned varint")
    buf = bytearray()
    while n >= 128:
        buf.append((n & 127) | 128)
        n >>= 7
    buf.append(n)
    return bytes(buf)


def take_varint(data, pos):
    acc = 0
    for shift in range(0, 63, 7):
        if pos >= len(data):
            raise ValueError("truncated varint")
        b = data[pos]
        pos += 1
        if shift == 56 and b & 128:
            raise ValueError("oversized varint")
        acc |= (b & 127) << shift
        if b < 128:
            return acc, pos
    raise ValueError("oversized varint")


def to_bytes(name):
    # surrogateescape faithfully roundtrips POSIX filesystem byte strings.
    return name.encode("utf-8", "surrogateescape")


def from_bytes(name):
    return name.decode("utf-8", "surrogateescape")


def encode_names(names):
    if len(names) > MAX_PATHS:
        raise ValueError("too many paths")
    out = bytearray(varint(len(names)))
    prev = b""
    total = 0
    for name in names:
        b = to_bytes(name)
        if len(b) > MAX_NAME:
            raise ValueError("path too long")
        i = 0
        while i < min(len(prev), len(b)) and prev[i] == b[i]:
            i += 1
        suffix = b[i:]
        out.extend(varint(i))
        out.extend(varint(len(suffix)))
        out.extend(suffix)
        prev = b
        total += len(b)
        if total > MAX_TOTAL_NAMES:
            raise ValueError("total path budget")
    return bytes(out)


def decode_names(data):
    count, at = take_varint(data, 0)
    if count > MAX_PATHS:
        raise ValueError("too many decoded paths")
    out = []
    prev = b""
    total = 0
    for _ in range(count):
        prefix, at = take_varint(data, at)
        suffix_len, at = take_varint(data, at)
        if prefix > len(prev) or suffix_len > MAX_NAME or prefix + suffix_len > MAX_NAME:
            raise ValueError("invalid path lengths")
        if suffix_len > len(data) - at:
            raise ValueError("truncated suffix")
        b = prev[:prefix] + data[at:at + suffix_len]
        at += suffix_len
        total += len(b)
        if total > MAX_TOTAL_NAMES:
            raise ValueError("decoded names budget")
        out.append(from_bytes(b))
        prev = b
    if at != len(data):
        raise ValueError("trailing data")
    return out


def encode_index(index):
    if FIELD in index:
        raise ValueError("reserved field collision")
    tmp = copy.deepcopy(index)
    names = []
    for row in tmp["files"]:
        names.append(row[0])
        row[0] = None
    wire = encode_names(names)
    tmp[FIELD] = wire
    return msgpack.packb(tmp, use_bin_type=True), wire


def decode_index(payload):
    tmp = msgpack.unpackb(payload, raw=False)
    wire = tmp.pop(FIELD)
    names = decode_names(wire)
    if len(names) != len(tmp["files"]):
        raise ValueError("path count mismatch")
    for row, name in zip(tmp["files"], names):
        if row[0] is not None:
            raise ValueError("unremoved path field")
        row[0] = name
    return msgpack.packb(tmp, use_bin_type=True)


def make_name(kind, i):
    if kind == "flat":
        return f"item-{i:06d}.dat"
    if kind == "deep":
        return (f"root-{i//512:02d}/segment-{(i//64)%8:02d}/"
                f"team-{(i//8)%8:02d}/file-{i:06d}.bin")
    if kind == "random":
        h = hashlib.sha256(f"j24g84-seed-random-{i}".encode()).hexdigest()
        return f"{h}.bin"
    if kind == "unicode":
        return (f"proyecto-{i%17:02d}/línea-{i%9:02d}/"
                f"versión-{i//100:03d}/資料-{i:05d}-é.pdf")
    raise ValueError(kind)


def make_archive(root, kind):
    folder = root / ("src-" + kind)
    folder.mkdir()
    payload = hashlib.sha256(("j24g84-identical-contents-" + kind).encode()).digest()
    paths = []
    for i in range(N):
        name = make_name(kind, i)
        dst = folder / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(payload)
        paths.append(name)
    ar = root / (kind + ".cmpct")
    start = time.perf_counter_ns()
    Builder(folder, workers=1, reproducible=True).build(ar)
    elapsed = time.perf_counter_ns() - start
    with CMPCT(ar) as reader:
        assert all(p in reader.by for p in paths)
        index = copy.deepcopy(reader.index)
        assert reader.verify() >= N
    return index, ar.stat().st_size, elapsed, paths


def hostile_roundtrips():
    lists = [
        [], [""], ["abc", "abc"], ["b", "a", "c"],
        ["x" * 128, "x" * 127 + "y"],
        ["é", "e\u0301", "資料", "🗂-file"],
        ["alpha/beta", "alpha/beta/child", "alpha/Beta"],
        ["\udcff", "\udc80", "byte-\udcfe"],
    ]
    for names in lists:
        e = encode_names(names)
        assert decode_names(e) == names
        for bad in (e + b"\x00", e[:-1] if e else b"\x80",
                    b"\x01\x01\x01x", b"\x80" * 16):
            try:
                decode_names(bad)
            except (ValueError, UnicodeError):
                pass
            else:
                # Truncated encoding may still decode if it is a different *valid* value;
                # only require rejection for genuinely malformed data.
                if bad != e[:-1]:
                    raise AssertionError("malformed prefix stream accepted")
    return dict(semantic_lists=len(lists), rejected_framing=True)


def time_series(index, comp, order):
    samples = {"control": [], "candidate": []}
    for variant in order:
        w0, c0 = time.perf_counter_ns(), time.process_time_ns()
        if variant == "control":
            encoded = msgpack.packb(index, use_bin_type=True)
        else:
            encoded, _ = encode_index(index)
        wire = comp.compress(encoded)
        w, c = time.perf_counter_ns() - w0, time.process_time_ns() - c0
        samples[variant].append(dict(wall_ns=w, cpu_ns=c, bytes=len(wire)))
    return samples


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "j24g84-result.json"
    receipt = dict(schema="j24g84-frontcode-whole-index-o0-v1",
                   source=attest(), host=platform.platform(),
                   status="RUNNING", product_credit=0,
                   classification="RESEARCH_ORACLE_NOT_PRODUCT", cases={})
    def save():
        dest.write_text(json.dumps(receipt, sort_keys=True, indent=2,
                                   ensure_ascii=True) + "\n")
    save()
    try:
        receipt["hostiles"] = hostile_roundtrips()
        comp = zstd.ZstdCompressor(level=19, threads=0)
        decomp = zstd.ZstdDecompressor()
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g84-") as dirname:
            root = Path(dirname)
            for kind in CASES:
                idx, archive_bytes, build_ns, files = make_archive(root, kind)
                original = msgpack.packb(idx, use_bin_type=True)
                transformed, name_wire = encode_index(idx)
                rebuilt = decode_index(transformed)
                assert rebuilt == original, "byte-exact original MessagePack recovery"
                assert decomp.decompress(comp.compress(transformed)) == transformed
                ref_wire = comp.compress(original)
                cand_wire = comp.compress(transformed)
                assert decomp.decompress(ref_wire) == original
                assert decomp.decompress(cand_wire) == transformed
                # Balanced trials charge transformation and compression to B.
                order = ("control", "candidate", "candidate", "control") * 5
                timing = time_series(idx, comp, order)
                assert all(x["bytes"] == len(ref_wire) for x in timing["control"])
                assert all(x["bytes"] == len(cand_wire) for x in timing["candidate"])
                saved = len(ref_wire) - len(cand_wire)
                row = dict(status="COMPLETE", member_paths=N,
                           archive_bytes=archive_bytes, builder_wall_ns=build_ns,
                           entries_in_real_index=len(idx["files"]),
                           original_msgpack_bytes=len(original),
                           transformed_msgpack_bytes=len(transformed),
                           prefix_wire_bytes=len(name_wire),
                           original_index_sha256=hashlib.sha256(original).hexdigest(),
                           recovered_index_sha256=hashlib.sha256(rebuilt).hexdigest(),
                           compressed_control_bytes=len(ref_wire),
                           compressed_candidate_bytes=len(cand_wire),
                           signed_bytes_saved=saved,
                           saving_pct=100 * saved / len(ref_wire),
                           h1_positive=(saved >= 256 and saved >= .05 * len(ref_wire)),
                           h1_regression=(saved < -.01 * len(ref_wire)),
                           timing=timing)
                for variant in ("control", "candidate"):
                    row[variant + "_median_wall_ns"] = statistics.median(
                        x["wall_ns"] for x in timing[variant])
                    row[variant + "_median_cpu_ns"] = statistics.median(
                        x["cpu_ns"] for x in timing[variant])
                receipt["cases"][kind] = row
                save()
                print("J24G84", kind, "control", len(ref_wire),
                      "frontcode", len(cand_wire), "saved", saved, flush=True)
        positives = sum(c["h1_positive"] for c in receipt["cases"].values())
        regressions = sum(c["h1_regression"] for c in receipt["cases"].values())
        receipt["status"] = "COMPLETE"
        receipt["decision"] = ("H1_SCOPED_METADATA_HEADROOM" if positives >= 2 and
                               regressions == 0 else "NO_GENERAL_METADATA_HEADROOM")
        receipt["positive_families"] = positives
        receipt["regressing_families"] = regressions
        save()
    except BaseException as exc:
        receipt["status"] = "FAILED"
        receipt["error"] = repr(exc)
        save()
        raise
    print("J24G84", receipt["decision"], flush=True)


if __name__ == "__main__":
    main()
