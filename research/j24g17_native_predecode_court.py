#!/usr/bin/env python3
"""J24G17 research-only native token-count preflight. NEVER an accepting decoder."""
from __future__ import annotations
import argparse
import ctypes
import gc
import hashlib
import io
import json
import random
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path
import msgpack

CAP = 65536
LIB = Path(__file__).resolve().with_name("j24g17_token_counter.so")

class TooManyNodes(Exception):
    pass

class BadFraming(Exception):
    pass

def tokens(b, cap=CAP):
    lib = ctypes.CDLL(str(LIB))
    f = lib.mp_count_tokens
    f.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
    f.restype = ctypes.c_int
    n = ctypes.c_uint64()
    status = f(b, len(b), cap, ctypes.byref(n))
    if status == 0:
        raise TooManyNodes(n.value)
    if status < 0:
        raise BadFraming("invalid syntactic framing")
    return n.value

def direct(b):
    return msgpack.unpackb(b, raw=False)

def guarded(b):
    tokens(b)
    return direct(b)  # semantic authority; native scan is NOT acceptance

def skipped(b):
    msgpack.Unpacker(io.BytesIO(b), raw=False).skip()
    return direct(b)  # not equivalent as a token counter or semantic skip oracle

MODES = {"direct": direct, "native_decode": guarded, "skip_decode": skipped}

def object_nodes(x):
    if isinstance(x, dict):
        return 1 + sum(object_nodes(k) + object_nodes(v) for k, v in x.items())
    if isinstance(x, (list, tuple)) and not isinstance(x, msgpack.ExtType):
        return 1 + sum(object_nodes(v) for v in x)
    return 1

def selftest():
    rng = random.Random(20261028)
    def obj(depth=0):
        if depth < 3 and rng.randrange(4):
            if rng.randrange(2):
                return [obj(depth + 1) for _ in range(rng.randrange(5))]
            return {"k" + str(i): obj(depth + 1) for i in range(rng.randrange(4))}
        return rng.choice([None, 0, -1, 2**32, True, "text", b"bin", 1.0, msgpack.ExtType(1, b"ab")])
    values = [None, True, False, -(2**63), 2**64-1, "", b"", {}, [], msgpack.ExtType(1, b"xy")]
    values += [obj() for _ in range(2500)]
    for v in values:
        b = msgpack.packb(v, use_bin_type=True)
        assert tokens(b) == object_nodes(v)
        assert guarded(b) == direct(b)
    ok = msgpack.packb([None] * (CAP - 1))
    over = msgpack.packb([None] * CAP)
    assert tokens(ok) == CAP
    assert guarded(ok) == direct(ok)
    try:
        tokens(over)
        raise AssertionError("cap failed")
    except TooManyNodes:
        pass
    assert len(direct(over)) == CAP
    invalid = {
        "nested_unhashable_key": bytes.fromhex("81 a1 78 81 91 01 c0"),
        "trailing": bytes.fromhex("c0 c0"),
        "truncated_str": bytes.fromhex("d9 05 61 62 63"),
        "reserved": bytes.fromhex("c1"),
        "truncated_ext": bytes.fromhex("d4 01"),
        "truncated_array": bytes.fromhex("92 c0"),
        "invalid_utf8": bytes.fromhex("a1 ff"),
    }
    for name, b in invalid.items():
        for method in (direct, guarded):
            try:
                method(b)
            except Exception:
                continue
            raise AssertionError("malformed accepted: " + name)
    # Semantic rejection cannot be decided from C syntax alone.
    assert tokens(invalid["nested_unhashable_key"]) == 6
    msgpack.Unpacker(io.BytesIO(invalid["nested_unhashable_key"]), raw=False).skip()
    return {"valid": len(values), "malformed": len(invalid),
            "semantic_skip_counterexample": True,
            "python": sys.version.split()[0], "msgpack": msgpack.__version__,
            "c_source_sha256": hashlib.sha256(Path(__file__).with_name("j24g17_msgpack_token_counter.c").read_bytes()).hexdigest()}

def generate(dest):
    dest.mkdir(parents=True, exist_ok=True)
    wrap = lambda ex: {"ops": [], "blobs": [], "extension": ex}
    v = {
        "ordinary_10k": wrap([{"name": str(i), "size": i} for i in range(10000)]),
        "ordinary_1k": wrap([{"name": str(i), "size": i} for i in range(1000)]),
        "tiny_maps_200k": wrap([{"x": 0} for _ in range(200000)]),
        "flat_nil_200k": wrap([None] * 200000),
        "nested_4000x50": wrap([[i] * 50 for i in range(4000)]),
    }
    target = len(msgpack.packb(v["tiny_maps_200k"], use_bin_type=True))
    pad = target - 40
    for _ in range(10):
        size = len(msgpack.packb(wrap(b"x" * pad), use_bin_type=True))
        pad += target - size
    v["opaque_same_bytes"] = wrap(b"x" * pad)
    manifest = {}
    for name, value in v.items():
        b = msgpack.packb(value, use_bin_type=True)
        (dest / (name + ".mpk")).write_bytes(b)
        manifest[name] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    assert manifest["tiny_maps_200k"]["bytes"] == manifest["opaque_same_bytes"]["bytes"]
    (dest / "vectors.json").write_text(json.dumps(manifest, indent=2) + "\n")

def worker(path, mode, repeats):
    b = path.read_bytes()
    samples = []
    for _ in range(repeats):
        gc.collect()
        t = time.perf_counter_ns()
        c = time.process_time_ns()
        status = "accepted"
        try:
            obj = MODES[mode](b)
            assert isinstance(obj, dict) and "extension" in obj
            del obj
        except TooManyNodes:
            status = "refused_token_cap"
        except Exception as ex:
            status = "error_" + type(ex).__name__
        samples.append({"cpu_ns": time.process_time_ns()-c,
                        "wall_ns": time.perf_counter_ns()-t, "status": status})
    return {"case": path.stem, "mode": mode, "sha256": hashlib.sha256(b).hexdigest(),
            "rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "samples": samples}

def court(dest, workers, repeats):
    identity = selftest()
    dest.mkdir(parents=True, exist_ok=True)
    # Construct hostile vectors in a separately exited process, not the supervisor:
    # inherited Linux ru_maxrss otherwise hides a real allocation difference.
    subprocess.run([sys.executable, __file__, "--generate", str(dest)],
                   capture_output=True, text=True, check=True)
    manifest = json.loads((dest / "vectors.json").read_text())
    modes = ["direct", "native_decode", "skip_decode"]
    raw = []
    for case, expected in manifest.items():
        for w in range(workers):
            for mode in modes[w % 3:] + modes[:w % 3]:
                p = subprocess.run([sys.executable, __file__, "--worker", str(dest / (case + ".mpk")),
                                    "--mode", mode, "--repeats", str(repeats)],
                                   capture_output=True, text=True, check=True)
                r = json.loads(p.stdout)
                assert r["sha256"] == expected["sha256"]
                r["worker_index"] = w
                raw.append(r)
    stats = {}
    for case in manifest:
        stats[case] = {}
        for mode in modes:
            subset = [r for r in raw if r["case"] == case and r["mode"] == mode]
            samples = [v for r in subset for v in r["samples"]]
            assert len(subset) == workers and len(samples) == workers * repeats
            stats[case][mode] = {
                "wall_ns_median": int(statistics.median(v["wall_ns"] for v in samples)),
                "cpu_ns_median": int(statistics.median(v["cpu_ns"] for v in samples)),
                "rss_kib_median": int(statistics.median(r["rss_kib"] for r in subset)),
                "statuses": sorted(set(v["status"] for v in samples)),
                "samples": len(samples),
            }
    ordinary = stats["ordinary_10k"]
    decision = {}
    for field in ("cpu_ns_median", "wall_ns_median"):
        decision[field + "_ratio"] = ordinary["native_decode"][field] / ordinary["direct"][field]
    decision["H2_pass"] = all(decision[k] <= 2.0 for k in ("cpu_ns_median_ratio", "wall_ns_median_ratio"))
    rss = stats["tiny_maps_200k"]
    decision["hostile_rss_saved_kib"] = rss["direct"]["rss_kib_median"] - rss["native_decode"]["rss_kib_median"]
    decision["H3_pass"] = decision["hostile_rss_saved_kib"] >= 16384
    decision["semantic_refusal_not_product_compatibility"] = True
    result = {"schema": "cmpct-j24g17-research-v1", "research_only": True,
              "prereg_commit": "32099051333c9a23328bf3bc99778afe8ace8e0f",
              "identity": identity, "vectors": manifest, "raw": raw,
              "stats": stats, "decision": decision}
    (dest / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"decision": decision, "stats": stats}, indent=2))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--generate", type=Path)
    p.add_argument("--worker", type=Path)
    p.add_argument("--mode", choices=list(MODES))
    p.add_argument("--court", type=Path)
    p.add_argument("--workers", type=int, default=5)
    p.add_argument("--repeats", type=int, default=3)
    a = p.parse_args()
    if a.selftest:
        print(json.dumps(selftest()))
    elif a.generate:
        generate(a.generate)
    elif a.worker:
        print(json.dumps(worker(a.worker, a.mode, a.repeats)))
    elif a.court:
        court(a.court, a.workers, a.repeats)
    else:
        p.error("choose action")

if __name__ == "__main__":
    main()
