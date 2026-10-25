#!/usr/bin/env python3
"""O126 preregistered A08 exact temporal-window research accounting.

Pure research container (TWOR1), explicitly not CMPCT r24 bytes. Strong
controls and decoder reconstruct from serialized payloads and hashes only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import struct
import subprocess
import sys
import time
from pathlib import Path

MAGIC = b"TWOR1\x00\x00\x00"
ARMS = ("snapshot", "solid_history", "per_file_raw", "per_file_xor", "journal_xor", "window_raw", "window_xor")
WINDOW = 4
HEADER = struct.Struct(">8s16sIIII")  # magic, arm, generation count, file count, file length, frame count
FRAME = struct.Struct(">QQ")  # fully charged 64-bit raw and compressed lengths


def xor(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("xor unequal lengths")
    return bytes(x ^ y for x, y in zip(a, b))


def zstd(data: bytes, *, decode: bool = False) -> bytes:
    cmd = ["zstd", "-d", "-q", "-c"] if decode else ["zstd", "-19", "-q", "-c", "--no-progress"]
    return subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def snapshots(kind: str, seed: int, gens: int, files: int, length: int) -> tuple[tuple[bytes, ...], ...]:
    rng = random.Random(seed)
    state = [bytearray(rng.randbytes(length)) for _ in range(files)]
    out = [tuple(bytes(x) for x in state)]
    for g in range(1, gens):
        if kind == "independent":
            state = [bytearray(rng.randbytes(length)) for _ in range(files)]
        elif kind == "rotate":
            state = [bytearray(x[-(13 + (f % 7)):] + x[:-(13 + (f % 7))]) for f, x in enumerate(state)]
        elif kind in ("sparse", "heldout"):
            changes = 6 if kind == "sparse" else 54
            for f, x in enumerate(state):
                for j in range(changes):
                    p = (f * 223 + g * 17 + j * 239 + (g * j if kind == "heldout" else 0)) % length
                    x[p] ^= (17 + 13 * f + 29 * g + j) % 255 + 1
        elif kind == "shared_epoch":
            for f, x in enumerate(state):
                for j in range(24):
                    p = (g * 19 + j * 127) % length
                    x[p] ^= (31 + 17 * g + 11 * j) % 255 + 1
        else:
            raise ValueError(kind)
        out.append(tuple(bytes(x) for x in state))
    return tuple(out)


def blocks_for_arm(arm: str, data: tuple[tuple[bytes, ...], ...]) -> list[bytes]:
    gcount = len(data)
    fcount = len(data[0])
    if arm == "snapshot":
        return [b"".join(data[g]) for g in range(gcount)]
    if arm == "solid_history":
        return [b"".join(b"".join(row) for row in data)]
    if arm == "per_file_raw":
        return [b"".join(data[g][f] for g in range(gcount)) for f in range(fcount)]
    if arm == "per_file_xor":
        return [data[0][f] + b"".join(xor(data[g - 1][f], data[g][f]) for g in range(1, gcount)) for f in range(fcount)]
    if arm == "journal_xor":
        return [b"".join(data[0])] + [b"".join(xor(data[g - 1][f], data[g][f]) for f in range(fcount)) for g in range(1, gcount)]
    if arm in ("window_raw", "window_xor"):
        blocks = []
        for start in range(0, gcount, WINDOW):
            end = min(gcount, start + WINDOW)
            for f in range(fcount):
                if arm == "window_raw":
                    blocks.append(b"".join(data[g][f] for g in range(start, end)))
                else:
                    blocks.append(data[start][f] + b"".join(xor(data[g - 1][f], data[g][f]) for g in range(start + 1, end)))
        return blocks
    raise ValueError(arm)


def parse_packet(packet: bytes):
    if len(packet) < HEADER.size:
        raise ValueError("short header")
    magic, arm_bytes, gens, files, length, count = HEADER.unpack_from(packet, 0)
    if magic != MAGIC or gens < 1 or files < 1 or length < 1 or gens > 256 or files > 1024 or length > 1 << 20:
        raise ValueError("invalid oracle header")
    arm = arm_bytes.rstrip(b"\0").decode("ascii")
    if arm not in ARMS:
        raise ValueError("unknown arm")
    at = HEADER.size
    names_end = at + files * 16
    hash_end = names_end + gens * files * 32
    desc_end = hash_end + count * FRAME.size
    if len(packet) < desc_end:
        raise ValueError("truncated metadata")
    names = [packet[at + i * 16: at + (i + 1) * 16].rstrip(b"\0").decode("ascii") for i in range(files)]
    expected = [packet[names_end + k * 32:names_end + (k + 1) * 32] for k in range(gens * files)]
    desc = [FRAME.unpack_from(packet, hash_end + k * FRAME.size) for k in range(count)]
    p = desc_end
    raw = []
    for nraw, ncompressed in desc:
        if nraw > (1 << 30) or ncompressed > (1 << 30) or ncompressed > len(packet) - p:
            raise ValueError("bad frame size")
        decoded = zstd(packet[p:p + ncompressed], decode=True)
        if len(decoded) != nraw:
            raise ValueError("raw length mismatch")
        raw.append(decoded)
        p += ncompressed
    if p != len(packet):
        raise ValueError("trailing bytes")
    return arm, gens, files, length, names, expected, raw, desc


def reconstruct(arm: str, gens: int, files: int, length: int, raws: list[bytes]):
    result = [[None] * files for _ in range(gens)]
    def cells(block):
        if len(block) != files * length:
            raise ValueError("bad snapshot block")
        return [block[f * length:(f + 1) * length] for f in range(files)]
    if arm == "snapshot":
        if len(raws) != gens:
            raise ValueError("frame count")
        for g in range(gens):
            result[g] = cells(raws[g])
    elif arm == "solid_history":
        if len(raws) != 1 or len(raws[0]) != gens * files * length:
            raise ValueError("solid length")
        for g in range(gens):
            result[g] = cells(raws[0][g * files * length:(g + 1) * files * length])
    elif arm in ("per_file_raw", "per_file_xor"):
        if len(raws) != files:
            raise ValueError("file frame count")
        for f, block in enumerate(raws):
            if len(block) != gens * length:
                raise ValueError("file history length")
            last = None
            for g in range(gens):
                v = block[g * length:(g + 1) * length]
                last = v if g == 0 or arm == "per_file_raw" else xor(last, v)
                result[g][f] = last
    elif arm == "journal_xor":
        if len(raws) != gens:
            raise ValueError("journal frame count")
        last = None
        for g, block in enumerate(raws):
            v = cells(block)
            last = v if g == 0 else [xor(last[f], v[f]) for f in range(files)]
            result[g] = last
    elif arm in ("window_raw", "window_xor"):
        if len(raws) != ((gens + WINDOW - 1) // WINDOW) * files:
            raise ValueError("window frame count")
        k = 0
        for start in range(0, gens, WINDOW):
            end = min(gens, start + WINDOW)
            for f in range(files):
                block = raws[k]
                k += 1
                if len(block) != (end - start) * length:
                    raise ValueError("window frame length")
                last = None
                for g in range(start, end):
                    v = block[(g-start)*length:(g-start+1)*length]
                    last = v if g == start or arm == "window_raw" else xor(last, v)
                    result[g][f] = last
    else:
        raise ValueError(arm)
    return tuple(tuple(row) for row in result)


def selected_decode_raw_work(arm: str, gens: int, files: int, length: int, raws: list[bytes], g: int) -> int:
    if arm == "snapshot":
        return len(raws[g])
    if arm == "solid_history":
        return len(raws[0])
    if arm in ("per_file_raw", "per_file_xor"):
        return sum(map(len, raws))
    if arm == "journal_xor":
        return sum(len(x) for x in raws[:g + 1])
    if arm in ("window_raw", "window_xor"):
        wi = g // WINDOW
        return sum(len(x) for x in raws[wi*files:(wi+1)*files])
    raise AssertionError(arm)


def encode(arm: str, data):
    gens, files, length = len(data), len(data[0]), len(data[0][0])
    frames = blocks_for_arm(arm, data)
    ru_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    compressed = [zstd(x) for x in frames]
    wall = time.perf_counter() - start_wall
    cpu_parent = time.process_time() - start_cpu
    ru_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = (ru_after.ru_utime + ru_after.ru_stime) - (ru_before.ru_utime + ru_before.ru_stime)
    names = b"".join((f"file-{i:06d}".encode()).ljust(16, b"\0") for i in range(files))
    hashes = b"".join(hashlib.sha256(data[g][f]).digest() for g in range(gens) for f in range(files))
    desc = b"".join(FRAME.pack(len(raw), len(zipped)) for raw, zipped in zip(frames, compressed))
    packet = HEADER.pack(MAGIC, arm.encode().ljust(16, b"\0"), gens, files, length, len(frames)) + names + hashes + desc + b"".join(compressed)
    return packet, {"create_wall_s": wall, "parent_cpu_s": cpu_parent, "child_cpu_s": child_cpu, "frames": len(frames), "input_bytes": gens * files * length,
                    "payload_bytes": sum(map(len, compressed)), "charged_metadata_bytes": len(packet) - sum(map(len, compressed))}


def run_family(kind, seed, gens=12, files=8, length=4096):
    data = snapshots(kind, seed, gens, files, length)
    digest = hashlib.sha256(b"".join(b"".join(snap) for snap in data)).hexdigest()
    rows = []
    for arm in ARMS:
        packet, m = encode(arm, data)
        got_arm, gg, ff, ll, names, hashes, raws, desc = parse_packet(packet)
        rebuilt = reconstruct(got_arm, gg, ff, ll, raws)
        if rebuilt != data or len(names) != files:
            raise AssertionError(f"{kind}/{arm}: byte-exact inverse failed")
        for g in range(gens):
            for f in range(files):
                if hashlib.sha256(rebuilt[g][f]).digest() != hashes[g * files + f]:
                    raise AssertionError(f"{kind}/{arm}: SHA mismatch {g}/{f}")
        work = [selected_decode_raw_work(arm, gens, files, length, raws, g) for g in range(gens)]
        m.update({"arm": arm, "stored_bytes": len(packet), "sha256_packet": hashlib.sha256(packet).hexdigest(),
                  "max_selective_decode_ratio": round(max(work) / (files * length), 6),
                  "median_selective_decode_ratio": round(sorted(work)[len(work) // 2] / (files * length), 6),
                  "byte_exact_generation_count": gens, "sha_verified_members": gens * files})
        rows.append(m)
    candidates = [x for x in rows if x["max_selective_decode_ratio"] <= 4]
    ctrl = min((x for x in candidates if x["arm"] != "window_xor"), key=lambda x: x["stored_bytes"])
    cand = next(x for x in rows if x["arm"] == "window_xor")
    best_any = min(rows, key=lambda x: x["stored_bytes"])
    gain = (ctrl["stored_bytes"] - cand["stored_bytes"]) / ctrl["stored_bytes"]
    return {"family": kind, "seed": seed, "generations": gens, "files": files, "file_length": length, "source_sha256": digest,
            "arms": rows, "best_any": best_any["arm"], "best_admissible_control": ctrl["arm"],
            "candidate_gain_vs_best_admissible": round(gain, 8), "candidate_ge_5pct_better": gain >= 0.05}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="o126-results.json")
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    version = subprocess.check_output(["zstd", "--version"], text=True).strip()
    cases = [("sparse", 801, 12, 8, 4096), ("shared_epoch", 802, 12, 8, 4096),
             ("rotate", 803, 12, 8, 4096), ("independent", 804, 12, 8, 4096),
             ("heldout", 9961, 12, 16, 8192)]
    if args.smoke:
        cases = [("sparse", 801, 4, 2, 384)]
    results = [run_family(*case) for case in cases]
    decisive = [r for r in results if r["family"] in ("sparse", "shared_epoch")]
    decision = "SCOPED_HEADROOM" if len(decisive) == 2 and all(r["candidate_ge_5pct_better"] for r in decisive) else "PREDECLARED_HEADROOM_NOT_SHOWN"
    report = {"schema": "cmpct-o126-a08-v1", "decision": decision, "evidence_level": "charged independent research container; NOT valid CMPCT format/product benchmark",
              "script_sha256": script_sha, "python": sys.version.split()[0], "platform": platform.platform(), "zstd": version,
              "charge": "actual binary research container: 40B fixed header, 16B/file name, 32B/member/gen SHA, 16B/frame descriptor, compressed frame bytes",
              "selective_work": "uncompressed bytes of required whole frames; no seeks/caches gifted; host I/O and subprocess RSS unmeasured",
              "families": results}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for r in results:
        print(r["family"], "best_any", r["best_any"], "admissible_control", r["best_admissible_control"],
              "candidate_vs_control", round(r["candidate_gain_vs_best_admissible"] * 100, 2), "%")
    print("O126_DECISION=" + decision)
    print("O126_RESEARCH_RESULT=" + args.output)


if __name__ == "__main__":
    main()
