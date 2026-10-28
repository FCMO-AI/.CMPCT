#!/usr/bin/env python3
"""A19-O0: bounded, fully charged composition versus best unary/direct control.

Research oracle only. No CMPCT archive/Reader/Builder imported or modified.
Run: python research/a19_o0_program_composition.py --output a19_o0.json
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
import platform
import statistics
import sys
import time

import msgpack

MAGIC = b"A19O"
SEED = 20261028
REPEATS = 5
K = (2, 4, 8)
LAGS = (1, 2, 4, 8)

_libname = ctypes.util.find_library("zstd")
if not _libname:
    raise RuntimeError("libzstd required for actual Zstd-19 same-input control")
_zstd = ctypes.CDLL(_libname)
_zstd.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
_zstd.ZSTD_compressBound.restype = ctypes.c_size_t
_zstd.ZSTD_compress.argtypes = [
    ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int
]
_zstd.ZSTD_compress.restype = ctypes.c_size_t
_zstd.ZSTD_decompress.argtypes = [
    ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t
]
_zstd.ZSTD_decompress.restype = ctypes.c_size_t
_zstd.ZSTD_isError.argtypes = [ctypes.c_size_t]
_zstd.ZSTD_isError.restype = ctypes.c_uint
_zstd.ZSTD_versionString.restype = ctypes.c_char_p


def compress(raw: bytes) -> bytes:
    bound = _zstd.ZSTD_compressBound(len(raw))
    dst = ctypes.create_string_buffer(bound)
    src = ctypes.create_string_buffer(raw)
    n = _zstd.ZSTD_compress(dst, bound, src, len(raw), 19)
    if _zstd.ZSTD_isError(n):
        raise RuntimeError("Zstd-19 compression failed")
    return dst.raw[:n]


def decompress(raw: bytes, size: int) -> bytes:
    if size < 0 or size > 1 << 24:
        raise ValueError("invalid output size")
    dst = ctypes.create_string_buffer(size)
    src = ctypes.create_string_buffer(raw)
    n = _zstd.ZSTD_decompress(dst, size, src, len(raw))
    if _zstd.ZSTD_isError(n) or n != size:
        raise ValueError("Zstd payload invalid or wrong declared decoded length")
    return dst.raw[:n]


def deinterleave(data: bytes, k: int) -> bytes:
    if k not in K:
        raise ValueError("unsupported channels")
    return b"".join(data[j::k] for j in range(k))


def reinterleave(data: bytes, k: int) -> bytes:
    if k not in K:
        raise ValueError("unsupported channels")
    length = len(data)
    result = bytearray(length)
    pos = 0
    for j in range(k):
        count = len(range(j, length, k))
        result[j::k] = data[pos:pos + count]
        pos += count
    if pos != length:
        raise AssertionError("reinterleave coverage error")
    return bytes(result)


def xor_prev(data: bytes, lag: int) -> bytes:
    if lag not in LAGS:
        raise ValueError("unsupported lag")
    result = bytearray(data)
    for i in range(lag, len(data)):
        result[i] = data[i] ^ data[i - lag]
    return bytes(result)


def unxor_prev(data: bytes, lag: int) -> bytes:
    if lag not in LAGS:
        raise ValueError("unsupported lag")
    result = bytearray(data)
    for i in range(lag, len(data)):
        result[i] ^= result[i - lag]
    return bytes(result)


def validated(steps):
    if not isinstance(steps, list) or len(steps) > 2:
        raise ValueError("unbounded reconstruction program")
    for j, step in enumerate(steps):
        if not isinstance(step, list) or len(step) != 2:
            raise ValueError("bad instruction")
        name, arg = step
        if type(arg) is not int or (name == "deinterleave" and arg not in K) or (
            name == "xor_prev" and arg not in LAGS
        ):
            raise ValueError("bad opcode/argument")
        if name not in ("deinterleave", "xor_prev"):
            raise ValueError("unknown opcode")
        if len(steps) == 2 and ((j == 0 and name != "deinterleave") or
                                (j == 1 and name != "xor_prev")):
            raise ValueError("unsupported composition")


def transform(raw: bytes, steps: list) -> bytes:
    validated(steps)
    out = raw
    for name, arg in steps:
        out = deinterleave(out, arg) if name == "deinterleave" else xor_prev(out, arg)
    return out


def inverse(raw: bytes, steps: list) -> bytes:
    validated(steps)
    out = raw
    for name, arg in reversed(steps):
        out = reinterleave(out, arg) if name == "deinterleave" else unxor_prev(out, arg)
    return out


def encode_archive(data: bytes, steps: list) -> bytes:
    transformed = transform(data, steps)
    header = {
        "v": 1, "len": len(data), "sha256": hashlib.sha256(data).digest(),
        "codec": "zstd19", "program": steps
    }
    meta = msgpack.packb(header, use_bin_type=True)
    if len(meta) > 1024:
        raise AssertionError("unexpected metadata growth")
    return MAGIC + len(meta).to_bytes(4, "big") + meta + compress(transformed)


def decode_archive(frame: bytes) -> bytes:
    if len(frame) < 8 or frame[:4] != MAGIC:
        raise ValueError("invalid magic")
    n = int.from_bytes(frame[4:8], "big")
    if n < 1 or n > 1024 or len(frame) <= 8 + n:
        raise ValueError("invalid descriptor boundary")
    m = msgpack.unpackb(frame[8:8+n], raw=False, strict_map_key=True)
    if type(m) is not dict or m.get("v") != 1 or m.get("codec") != "zstd19":
        raise ValueError("unsupported header")
    size, steps, digest = m.get("len"), m.get("program"), m.get("sha256")
    if type(size) is not int or size > 1 << 24 or size < 0 or (
        not isinstance(digest, bytes) or len(digest) != 32
    ):
        raise ValueError("invalid declared length/hash")
    validated(steps)
    out = inverse(decompress(frame[8+n:], size), steps)
    if len(out) != size or hashlib.sha256(out).digest() != digest:
        raise ValueError("logical integrity mismatch")
    return out


def source(label: str, seed: int, length: int) -> bytes:
    """Public deterministic SHAKE byte stream; not a compressor selector."""
    return hashlib.shake_256(
        ("CMPCT/A19-O0/" + str(SEED) + "/" + label + "/" + str(seed)).encode()
    ).digest(length)


def fixture(kind: str, seed: int) -> bytes:
    n = 65536 if seed == 0 else 65539
    if kind == "random":
        return source(kind, seed, n)
    if kind == "periodic":
        motif = source(kind, seed, 31)
        return (motif * (n // len(motif) + 1))[:n]

    changes = source(kind + "/changes", seed, n * 2)
    state = bytearray(source(kind + "/initial", seed, 4))
    out = bytearray(n)
    for i in range(n):
        ch = i % 4
        t = i // 4
        if kind == "progression":
            if changes[i] < 35:
                state[ch] ^= changes[n + i] or 1
        else:
            move = changes[i] % 5
            state[ch] = (state[ch] + move - 2) & 255
            if changes[n + i] < 5:
                state[ch] ^= changes[i]
        dst_ch = (ch + (t // 512) % 4) % 4 if kind == "heldout" else ch
        out[i] = state[dst_ch]
    if kind == "heldout":
        # Replace the second half with high-entropy bytes; retain 3-byte suffix.
        out[n // 2:] = source(kind + "/random_half", seed, n - n // 2)
    return bytes(out)


def candidates():
    yield []
    for k in K:
        yield [["deinterleave", k]]
    for lag in LAGS:
        yield [["xor_prev", lag]]
    for k in K:
        for lag in LAGS:
            yield [["deinterleave", k], ["xor_prev", lag]]


def kind(steps):
    return "direct" if not steps else ("unary" if len(steps) == 1 else "composed")


def time_one(data: bytes, steps: list):
    observations = []
    for _ in range(REPEATS):
        start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
        frame = encode_archive(data, steps)
        create_wall, create_cpu = time.perf_counter_ns()-start_wall, time.process_time_ns()-start_cpu
        start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
        decoded = decode_archive(frame)
        read_wall, read_cpu = time.perf_counter_ns()-start_wall, time.process_time_ns()-start_cpu
        assert decoded == data
        observations.append({
            "create_wall_ns": create_wall, "create_cpu_ns": create_cpu,
            "decode_wall_ns": read_wall, "decode_cpu_ns": read_cpu
        })
    return observations


def run():
    cases = []
    total_search_wall_ns = 0
    for family in ("progression", "quantized", "heldout", "random", "periodic"):
        for seed in (0, 1):
            original = fixture(family, seed)
            before = time.perf_counter_ns()
            arms = []
            for steps in candidates():
                frame = encode_archive(original, steps)
                if decode_archive(frame) != original:
                    raise AssertionError("nonexact reconstruction")
                arms.append({
                    "steps": steps, "type": kind(steps), "stored_bytes": len(frame),
                    "frame_sha256": hashlib.sha256(frame).hexdigest()
                })
            search_wall_ns = time.perf_counter_ns() - before
            total_search_wall_ns += search_wall_ns
            direct = next(a for a in arms if a["type"] == "direct")
            best_unary = min((a for a in arms if a["type"] == "unary"),
                             key=lambda a: (a["stored_bytes"], str(a["steps"])))
            best_comp = min((a for a in arms if a["type"] == "composed"),
                            key=lambda a: (a["stored_bytes"], str(a["steps"])))
            best_all = min(arms, key=lambda a: (a["stored_bytes"], str(a["steps"])))
            selected = {json.dumps(a["steps"]): a["steps"] for a in
                        (direct, best_unary, best_comp, best_all)}
            timing = {key: time_one(original, steps) for key, steps in selected.items()}
            saving = best_unary["stored_bytes"] - best_comp["stored_bytes"]
            passes = (saving >= 128 and saving / best_unary["stored_bytes"] >= .01
                      and best_comp["stored_bytes"] < direct["stored_bytes"])
            cases.append({
                "family": family, "seed": seed, "source_sha256": hashlib.sha256(original).hexdigest(),
                "logical_bytes": len(original), "search_wall_ns": search_wall_ns,
                "direct": direct, "best_unary": best_unary, "best_composed": best_comp,
                "best_portfolio": best_all, "unary_minus_composed_bytes": saving,
                "composed_improvement_fraction": saving / best_unary["stored_bytes"],
                "material_composition_vs_unary_and_direct": passes,
                "arms": arms, "timings_by_program": timing
            })
            print(f"{family}:{seed} direct={direct['stored_bytes']} "
                  f"unary={best_unary['stored_bytes']} composed={best_comp['stored_bytes']} "
                  f"winner={best_all['type']} material={passes}", flush=True)
    primary = [c for c in cases if c["family"] in ("progression", "quantized")]
    earned = any(
        all(c["material_composition_vs_unary_and_direct"] for c in primary
            if c["family"] == family)
        for family in ("progression", "quantized")
    )
    # Non-program-specific hostile cases and auth bounds. Invalidity must fail.
    sample = fixture("random", 0)
    valid = encode_archive(sample, [])
    adversarial = {
        "payload_byte_flip": valid[:-1] + bytes([valid[-1] ^ 0x80]),
        "wrong_magic": b"XXXX" + valid[4:],
        "truncated": valid[:10],
        "wrong_length": valid[:4] + (1025).to_bytes(4, "big") + valid[8:],
    }
    for label, frame in adversarial.items():
        try:
            decode_archive(frame)
        except (ValueError, RuntimeError):
            pass
        else:
            raise AssertionError("hostile frame accepted: " + label)
    for length in (1, 2, 7, 65535, 65539):
        raw = source("length_hostile", length, length)
        for steps in candidates():
            assert inverse(transform(raw, steps), steps) == raw
    return {
        "schema": "cmpct-a19-o0-research-v1",
        "source_baseline": "main@80c358f8824ec1b20d349c92ed94c898090969b0",
        "preregistration_commit": "f48a8b9f2c1788ab83776df22916f75210159857",
        "toolchain": {"python": sys.version, "system": platform.platform(),
                      "libzstd": _zstd.ZSTD_versionString().decode(),
                      "msgpack": msgpack.__version__},
        "settings": {"seed": SEED, "repeats": REPEATS, "zstd_level": 19,
                     "grammar": "direct + unary deinterleave{2,4,8}/xor_prev{1,2,4,8} + deinterleave_then_xor"},
        "decision": "A19_COMPOSITION_O0_HEADROOM" if earned else "A19_COMPOSITION_O0_RETIRE_THIS_GRAMMAR",
        "case_count": len(cases), "total_search_wall_ns": total_search_wall_ns,
        "hostile_rejections": len(adversarial), "roundtrip_length_tests": 5 * 20,
        "cases": cases,
        "limitations": [
            "Component oracle only; not a CMPCT r24 archive or an installed Reader/Builder.",
            "Search explores all 20 arms and create CPU/time cannot be gifted in product.",
            "Decoder has up to two full-size temporary transformations; no streaming proof.",
            "Synthetic structural families and one Ubuntu host cannot establish real-corpus or cross-platform generality.",
            "No encoder policy/selector proof and no promoted product claim."
        ]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="a19_o0_result.json")
    args = parser.parse_args()
    result = run()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    print("DECISION " + result["decision"])
    print("RESULT " + os.path.abspath(args.output))
