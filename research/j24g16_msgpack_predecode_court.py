#!/usr/bin/env python3
"""J24G16 scientific-only structural MessagePack node admission experiment.

Never use the structural precheck as an accepting decoder. If under budget,
the unchanged msgpack.unpackb(raw=False) is always the semantic authority.
This is a research microcourt, not CMPCT Reader/format policy.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import io
import json
from pathlib import Path
import random
import resource
import subprocess
import sys
import tempfile
import time

import msgpack

CAP = 65536

class TooManyNodes(Exception):
    pass

class BadWire(Exception):
    pass

def count_wire_nodes(data: bytes, max_nodes: int = CAP, max_depth: int = 512) -> int:
    """Count all MessagePack wire tokens in O(bytes) time/O(nesting) space."""
    view = memoryview(data)
    n, pos, nodes = len(view), 0, 0
    pending = [1]
    def read_length(width):
        nonlocal pos
        if pos + width > n:
            raise BadWire("truncated length")
        value = int.from_bytes(view[pos:pos + width], "big")
        pos += width
        return value
    def skip(length):
        nonlocal pos
        if length > n - pos:
            raise BadWire("truncated value")
        pos += length
    while pending:
        if pending[-1] == 0:
            pending.pop()
            continue
        pending[-1] -= 1
        if pos >= n:
            raise BadWire("truncated token")
        marker = view[pos]
        pos += 1
        nodes += 1
        if nodes > max_nodes:
            raise TooManyNodes("node budget exceeded")
        children = 0
        if marker <= 0x7f or marker >= 0xe0 or marker in (0xc0, 0xc2, 0xc3):
            pass
        elif 0x80 <= marker <= 0x8f:
            children = (marker & 15) * 2
        elif 0x90 <= marker <= 0x9f:
            children = marker & 15
        elif 0xa0 <= marker <= 0xbf:
            skip(marker & 31)
        elif marker == 0xc1:
            raise BadWire("reserved MessagePack marker")
        elif marker in (0xc4, 0xd9):
            skip(read_length(1))
        elif marker in (0xc5, 0xda):
            skip(read_length(2))
        elif marker in (0xc6, 0xdb):
            skip(read_length(4))
        elif marker in (0xc7, 0xc8, 0xc9):
            skip(read_length({0xc7: 1, 0xc8: 2, 0xc9: 4}[marker]) + 1)
        elif marker in (0xca, 0xce, 0xd2):
            skip(4)
        elif marker in (0xcb, 0xcf, 0xd3):
            skip(8)
        elif marker in (0xcc, 0xd0):
            skip(1)
        elif marker in (0xcd, 0xd1):
            skip(2)
        elif 0xd4 <= marker <= 0xd8:
            skip((1 << (marker - 0xd4)) + 1)
        elif marker == 0xdc:
            children = read_length(2)
        elif marker == 0xdd:
            children = read_length(4)
        elif marker == 0xde:
            children = read_length(2) * 2
        elif marker == 0xdf:
            children = read_length(4) * 2
        else:
            raise BadWire("unknown MessagePack marker")
        if children:
            if len(pending) >= max_depth:
                raise BadWire("maximum structural nesting exceeded")
            if children > max_nodes - nodes:
                raise TooManyNodes("declared children exceed budget")
            pending.append(children)
    if pos != n:
        raise BadWire("trailing bytes")
    return nodes

def baseline(data):
    return msgpack.unpackb(data, raw=False)

def gated(data):
    count_wire_nodes(data)
    return baseline(data)

def skipped(data):
    # C-backed speed control; skip alone is NOT semantic validation.
    msgpack.Unpacker(io.BytesIO(data), raw=False).skip()
    return baseline(data)

def hooked(data):
    # Cannot preempt a giant flat scalar array; hook fires after construction.
    counter = [0]
    def hook(value):
        counter[0] += 1
        if counter[0] > CAP:
            raise TooManyNodes("post-allocation container hook budget")
        return value
    return msgpack.unpackb(data, raw=False, object_hook=hook, list_hook=hook)

def count_object(obj):
    if isinstance(obj, dict):
        return 1 + sum(count_object(k) + count_object(v) for k, v in obj.items())
    if isinstance(obj, (list, tuple)) and not isinstance(obj, msgpack.ExtType):
        return 1 + sum(count_object(v) for v in obj)
    return 1

def selftest():
    r = random.Random(20261028)
    def construct(depth=0):
        if depth < 3 and r.randrange(4):
            if r.randrange(2):
                return [construct(depth + 1) for _ in range(r.randrange(5))]
            return {"k"+str(i): construct(depth+1) for i in range(r.randrange(4))}
        return r.choice([None, 0, -1, 2**32, True, "text", b"bin", 1.0,
                         msgpack.ExtType(1, b"ab")])
    values = [None, True, False, -(2**63), 2**64-1, "", b"", {}, [],
              msgpack.ExtType(1, b"xy")]
    values += [construct() for _ in range(2500)]
    for value in values:
        b = msgpack.packb(value, use_bin_type=True)
        assert count_wire_nodes(b) == count_object(value)
        assert gated(b) == baseline(b)
    bad = {
        "nested_unhashable_key": bytes.fromhex("81 a1 78 81 91 01 c0"),
        "trailing": bytes.fromhex("c0 c0"),
        "truncated_str": bytes.fromhex("d9 05 61 62 63"),
        "reserved_marker": bytes.fromhex("c1"),
        "truncated_ext": bytes.fromhex("d4 01"),
        "truncated_array": bytes.fromhex("92 c0"),
    }
    for name, b in bad.items():
        for f in (baseline, gated):
            try:
                f(b)
            except Exception:
                continue
            raise AssertionError(name + " wrongly accepted")
    # Prove negative control: skip-only can miss invalid nested map keys.
    msgpack.Unpacker(io.BytesIO(bad["nested_unhashable_key"]), raw=False).skip()
    return {"valid_vectors": len(values), "malformed_vectors": len(bad),
            "skip_only_malformed_witness": True,
            "msgpack_version": list(msgpack.version),
            "python_version": sys.version.split()[0]}

def create_vectors(directory):
    vectors = {
        "tiny_maps_200k": {"ops": [], "blobs": [], "extension": [{"x": 0} for _ in range(200000)]},
        "flat_nil_200k": {"ops": [], "blobs": [], "extension": [None]*200000},
        "nested_4000x50": {"ops": [], "blobs": [], "extension": [[i]*50 for i in range(4000)]},
        "ordinary_10k": {"ops": [], "blobs": [], "extension": [{"name": str(i), "size": i} for i in range(10000)]},
        "ordinary_1k": {"ops": [], "blobs": [], "extension": [{"name": str(i), "size": i} for i in range(1000)]},
    }
    target = len(msgpack.packb(vectors["tiny_maps_200k"], use_bin_type=True))
    pad = target - 45
    for _ in range(10):
        size = len(msgpack.packb({"ops": [], "blobs": [], "extension": b"x"*pad}, use_bin_type=True))
        pad += target - size
    vectors["opaque_same_bytes"] = {"ops": [], "blobs": [], "extension": b"x"*pad}
    records = {}
    for name, value in vectors.items():
        b = msgpack.packb(value, use_bin_type=True)
        if name == "opaque_same_bytes":
            assert len(b) == target
        path = directory / (name + ".mpk")
        path.write_bytes(b)
        records[name] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                         "path": str(path)}
    return records

def worker(file, method):
    b = Path(file).read_bytes()
    funcs = {"direct": baseline, "scan_decode": gated, "skip_decode": skipped,
             "hook_decode": hooked}
    gc.collect()
    cpu = time.process_time_ns()
    wall = time.perf_counter_ns()
    accepted, error = True, None
    try:
        output = funcs[method](b)
        assert isinstance(output, dict) and "extension" in output
        del output
    except Exception as exc:
        accepted, error = False, type(exc).__name__
    cpu = time.process_time_ns() - cpu
    wall = time.perf_counter_ns() - wall
    return {"mode": method, "accepted": accepted, "error": error,
            "cpu_ns": cpu, "wall_ns": wall,
            "rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

def court(repeats, dest):
    dest.mkdir(parents=True, exist_ok=True)
    identity = selftest()
    # J24G16b: keep hostile payload construction in a short-lived process.
    # Otherwise fork/exec workers may inherit generation's peak RSS highwater
    # and falsely show identical RSS across direct and preflight arms.
    subprocess.run([sys.executable, __file__, "--generate", str(dest)],
                   capture_output=True, text=True, check=True)
    sources = {}
    for label in ("tiny_maps_200k", "flat_nil_200k", "nested_4000x50",
                  "ordinary_10k", "ordinary_1k", "opaque_same_bytes"):
        p = dest / (label + ".mpk")
        b = p.read_bytes()
        sources[label] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                          "path": str(p)}
    samples = []
    for name, source in sources.items():
        for round_no in range(repeats):
            for mode in ("direct", "scan_decode", "skip_decode", "hook_decode"):
                p = subprocess.run([sys.executable, __file__, "--worker", source["path"], mode],
                                   capture_output=True, text=True, check=True)
                result = json.loads(p.stdout)
                assert result["sha256"] == source["sha256"]
                samples.append({"case": name, "repetition": round_no, **result})
    obj = {"schema": "cmpct-j24g16-v1", "research_only": True,
           "source_parent": "8c5c8cf8c588936b5dd4b856f35e5e0f282ed56d",
           "cap": CAP, "identity": identity, "vectors": sources, "samples": samples}
    (dest / "result.json").write_text(json.dumps(obj, indent=2) + "\n")
    return len(samples)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", nargs=2)
    p.add_argument("--court", type=Path)
    p.add_argument("--generate", type=Path)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        print(json.dumps(selftest()))
    elif a.worker:
        print(json.dumps(worker(*a.worker)))
    elif a.generate:
        a.generate.mkdir(parents=True, exist_ok=True)
        create_vectors(a.generate)
    elif a.court:
        print("samples:", court(a.repeats, a.court))
    else:
        p.error("choose mode")

if __name__ == "__main__":
    main()
