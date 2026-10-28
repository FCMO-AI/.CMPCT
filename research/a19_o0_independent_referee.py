#!/usr/bin/env python3
"""Detached A19-O0 physical-frame and receipt referee.

Does not import the candidate encoder, candidate decoder or CMPCT.
All program semantics are implemented separately from physical MessagePack records.
"""
from __future__ import annotations
import argparse
import copy
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import re

import msgpack

Z = ctypes.CDLL(ctypes.util.find_library("zstd"))
Z.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                              ctypes.c_void_p, ctypes.c_size_t]
Z.ZSTD_decompress.restype = ctypes.c_size_t
Z.ZSTD_isError.argtypes = [ctypes.c_size_t]
Z.ZSTD_isError.restype = ctypes.c_uint


def reference_bytes(family, seed, n):
    def stream(label, length):
        phrase = "/".join(("CMPCT", "A19-O0", "20261028", label, str(seed)))
        return hashlib.shake_256(phrase.encode()).digest(length)
    if family == "random":
        return stream(family, n)
    if family == "periodic":
        word = stream(family, 31)
        return (word * (n//31+1))[:n]
    rng = stream(family + "/changes", n*2)
    states = list(stream(family + "/initial", 4))
    output = bytearray(n)
    for pos in range(n):
        c = pos % 4
        if family == "progression":
            if rng[pos] < 35:
                states[c] ^= rng[n+pos] or 1
        else:
            states[c] = (states[c] + rng[pos] % 5 - 2) & 255
            if rng[n+pos] < 5:
                states[c] ^= rng[pos]
        tap = (c + ((pos//4)//512) % 4) % 4 if family == "heldout" else c
        output[pos] = states[tap]
    if family == "heldout":
        output[n//2:] = stream(family + "/random_half", n-n//2)
    return bytes(output)


def reverse_program(payload, program):
    out = payload
    if not isinstance(program, list) or len(program) > 2:
        raise ValueError("invalid program")
    if len(program) == 2 and (program[0][0] != "deinterleave" or
                              program[1][0] != "xor_prev"):
        raise ValueError("unrecognized composition")
    for entry in reversed(program):
        if not isinstance(entry, list) or len(entry) != 2 or type(entry[1]) is not int:
            raise ValueError("invalid instruction")
        name, argument = entry
        if name == "deinterleave" and argument in (2, 4, 8):
            positions = [list(range(c, len(out), argument)) for c in range(argument)]
            answer = bytearray(len(out))
            ptr = 0
            for group in positions:
                for dst in group:
                    answer[dst] = out[ptr]
                    ptr += 1
            out = bytes(answer)
        elif name == "xor_prev" and argument in (1, 2, 4, 8):
            answer = list(out)
            for j in range(argument, len(answer)):
                answer[j] = out[j] ^ answer[j-argument]
            out = bytes(answer)
        else:
            raise ValueError("unknown opcode")
    return out


def read_physical(path):
    frame = path.read_bytes()
    if frame[:4] != b"A19O" or len(frame) < 9:
        raise ValueError("bad frame")
    count = int.from_bytes(frame[4:8], "big")
    if count < 1 or count > 1024 or 8+count >= len(frame):
        raise ValueError("invalid header length")
    header = msgpack.unpackb(frame[8:8+count], raw=False, strict_map_key=True)
    if not isinstance(header, dict) or header.get("v") != 1 or header.get("codec") != "zstd19":
        raise ValueError("invalid header")
    length = header.get("len")
    if type(length) is not int or not 0 <= length <= 1 << 24:
        raise ValueError("unbounded length")
    buf = ctypes.create_string_buffer(length)
    comp = frame[8+count:]
    src = ctypes.create_string_buffer(comp)
    actual = Z.ZSTD_decompress(buf, length, src, len(comp))
    if Z.ZSTD_isError(actual) or actual != length:
        raise ValueError("decompression size mismatch")
    reconstructed = reverse_program(buf.raw[:actual], header.get("program"))
    if len(reconstructed) != length or hashlib.sha256(reconstructed).digest() != header.get("sha256"):
        raise ValueError("physical logical SHA mismatch")
    return frame, reconstructed, header


def audit(document, directory):
    if document.get("schema") != "cmpct-a19-o0-research-v1":
        raise ValueError("bad schema")
    cases = document.get("cases", [])
    if len(cases) != 10 or document.get("case_count") != 10:
        raise ValueError("wrong case count")
    outcomes = []
    seen = set()
    for case in cases:
        family, seed = case["family"], case["seed"]
        if family not in ("progression","quantized","heldout","random","periodic") or seed not in (0, 1):
            raise ValueError("wrong family/seed")
        if (family, seed) in seen:
            raise ValueError("duplicate")
        seen.add((family,seed))
        expected = reference_bytes(family, seed, 65536 if seed == 0 else 65539)
        if hashlib.sha256(expected).hexdigest() != case["source_sha256"]:
            raise ValueError("wrong logical identity")
        arms = case.get("arms")
        if not isinstance(arms, list) or len(arms) != 20:
            raise ValueError("wrong fixed grammar population")
        physical = []
        for j, arm in enumerate(arms):
            rel = f"{family}-{seed}-{j:02d}.a19"
            if arm.get("frame_rel") != rel or not re.fullmatch(r"[a-z]+-[01]-\d{2}\.a19", rel):
                raise ValueError("wrong physical locator")
            frame, logical, h = read_physical(directory / rel)
            if logical != expected or arm["stored_bytes"] != len(frame) or (
                arm["frame_sha256"] != hashlib.sha256(frame).hexdigest()
            ) or arm["steps"] != h["program"]:
                raise ValueError("physical/receipt mismatch")
            expected_kind = "direct" if not h["program"] else (
                "unary" if len(h["program"]) == 1 else "composed"
            )
            if arm["type"] != expected_kind:
                raise ValueError("untrue program class")
            physical.append(arm)
        def pick(kind):
            return min((a for a in physical if a["type"] == kind),
                       key=lambda a: (a["stored_bytes"], str(a["steps"])))
        for field, target in (("direct",pick("direct")),("best_unary",pick("unary")),
                              ("best_composed",pick("composed"))):
            if case[field] != target:
                raise ValueError("false chosen control")
        actual_portfolio = min(physical, key=lambda a: (a["stored_bytes"],str(a["steps"])))
        if case["best_portfolio"] != actual_portfolio:
            raise ValueError("false winner")
        difference = case["best_unary"]["stored_bytes"] - case["best_composed"]["stored_bytes"]
        ratio = difference / case["best_unary"]["stored_bytes"]
        passed = difference >= 128 and ratio >= .01 and (
            case["best_composed"]["stored_bytes"] < case["direct"]["stored_bytes"]
        )
        if case["unary_minus_composed_bytes"] != difference or (
            abs(case["composed_improvement_fraction"] - ratio) > 1e-12
        ) or case["material_composition_vs_unary_and_direct"] is not passed:
            raise ValueError("false composed decision")
        controls = {json.dumps(x["steps"]) for x in (
            case["direct"],case["best_unary"],case["best_composed"],case["best_portfolio"]
        )}
        timing = case["timings_by_program"]
        if set(timing) != controls or any(
            len(timing[key]) != 5 or any(
                not all(type(obs.get(k)) is int and obs[k] >= 0 for k in
                        ("create_wall_ns","create_cpu_ns","decode_wall_ns","decode_cpu_ns"))
                for obs in timing[key]) for key in timing
        ):
            raise ValueError("broken raw timing observations")
        outcomes.append((family, seed, passed))
    primary = [t for t in outcomes if t[0] in ("progression","quantized")]
    positive = any(all(t[2] for t in primary if t[0] == family)
                   for family in ("progression","quantized"))
    label = "A19_COMPOSITION_O0_HEADROOM" if positive else "A19_COMPOSITION_O0_RETIRE_THIS_GRAMMAR"
    if document["decision"] != label or document["hostile_rejections"] != 4:
        raise ValueError("false aggregate decision")
    return {"decision": label,"cases":len(cases),"physical_frames":200,
            "authentic_bytes_checked":sum(x["stored_bytes"] for c in cases for x in c["arms"]),
            "timing_repetitions":sum(len(v) for c in cases for v in c["timings_by_program"].values())}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--frames-dir", required=True)
    ap.add_argument("--audit", required=True)
    a = ap.parse_args()
    receipt = json.loads(Path(a.result).read_text())
    root = Path(a.frames_dir)
    output = audit(receipt, root)
    # Mutation controls are separate from the instrument, and must fail independently.
    for mode in range(7):
        mutated = copy.deepcopy(receipt)
        if mode == 0: mutated["cases"][0]["source_sha256"] = "0"*64
        elif mode == 1: mutated["cases"][0]["arms"][0]["stored_bytes"] += 1
        elif mode == 2: mutated["cases"][0]["arms"][0]["steps"] = [["xor_prev",4]]
        elif mode == 3: mutated["cases"][0]["arms"][0]["frame_sha256"] = "0"*64
        elif mode == 4: mutated["cases"].pop()
        elif mode == 5: mutated["decision"] = "FABRICATED"
        else: mutated["cases"][0]["unary_minus_composed_bytes"] += 1
        try:
            audit(mutated,root)
        except (ValueError, KeyError, TypeError, IndexError):
            continue
        raise AssertionError(f"forged receipt {mode} accepted")
    output["forged_receipts_rejected"] = 7
    Path(a.audit).write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(json.dumps(output,sort_keys=True))
