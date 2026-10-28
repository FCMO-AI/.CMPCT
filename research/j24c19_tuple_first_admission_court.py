#!/usr/bin/env python3
"""J24C19 research-only MessagePack tuple-first ownership oracle.

Neither path is a shipping Reader or an accepting archive validator. The
same signed-shape MessagePack bytes are used for both constructors. The
tuple-first adapter intentionally does not claim that the current Reader,
native ABI3 or validator accept a tuple of S_CHUNKS reference IDs.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time

import msgpack

# r24 tag integers from src/cmpct/codec.py; validated in selftest when available.
VERSION = 24
K_FILE = 0
S_CHUNKS = 1
CODEC_RAW = 0
SIZES = (4096, 65536, 262144)
SHAPES = ("fixed", "mixed")
MODES = ("freeze_after", "tuple_first")


def generate(n: int, shape: str) -> bytes:
    if shape == "fixed":
        refs = [0] * n
        blobs = [[0, 1, 1, CODEC_RAW, 0]]
        logical = b"A" * n
    elif shape == "mixed":
        refs = [i % 2 for i in range(n)]
        blobs = [[0, 1, 1, CODEC_RAW, 0], [1, 2, 2, CODEC_RAW, 0]]
        logical = b"ABC" * (n // 2) + (b"A" if n % 2 else b"")
    else:
        raise ValueError(shape)
    index = {"v": VERSION, "files": [
        ["fixture.bin", K_FILE, 0o644, 0, len(logical),
         hashlib.sha256(logical).digest(), [S_CHUNKS, refs]]
    ], "blobs": blobs, "recipes": []}
    return msgpack.packb(index, use_bin_type=True)


def freeze_after(payload: bytes) -> dict:
    index = msgpack.unpackb(payload, raw=False, use_list=True)
    storage = index["files"][0][6]
    storage[1] = tuple(storage[1])
    return index


def tuple_first(payload: bytes) -> dict:
    # No N-reference walk/copy. Every r24 structural container needed by the
    # plain index replay/validation boundary becomes mutable explicitly.
    # The leaf S_CHUNKS ref owner remains a decoder-owned tuple.
    decoded = msgpack.unpackb(payload, raw=False, use_list=False)
    index = dict(decoded)
    index["blobs"] = [list(x) for x in decoded["blobs"]]
    index["recipes"] = [list(x) for x in decoded["recipes"]]
    files = []
    for packed_row in decoded["files"]:
        row = list(packed_row)
        storage = list(row[6])
        if storage[0] != S_CHUNKS or not isinstance(storage[1], tuple):
            raise AssertionError("oracle only models S_CHUNKS")
        row[6] = storage
        files.append(row)
    index["files"] = files
    return index


def check_exact(payload: bytes, index: dict) -> None:
    # An independent re-serialization must reconstruct EXACT original bytes.
    raw = msgpack.packb(index, use_bin_type=True)
    if raw != payload:
        raise AssertionError("roundtrip MessagePack bytes differ")
    row = index["files"][0]
    if type(row) is not list or type(row[6]) is not list:
        raise AssertionError("structural list owner not restored")
    if type(row[6][1]) is not tuple or len(row[6][1]) == 0:
        raise AssertionError("immutable chunk refs not owned")
    if type(index["blobs"]) is not list or any(type(b) is not list for b in index["blobs"]):
        raise AssertionError("blob list structural shape")
    if sum(index["blobs"][ref][1] for ref in row[6][1]) != row[4]:
        raise AssertionError("logical size changed")


def maxrss_kib() -> int | None:
    try:
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value / 1024 if sys.platform == "darwin" else value)
    except Exception:
        return None


def worker(path: Path, mode: str, repeats: int) -> dict:
    payload = path.read_bytes()
    assert mode in MODES
    fn = freeze_after if mode == "freeze_after" else tuple_first
    gc.collect()
    rss_before = maxrss_kib()
    samples = []
    for _ in range(repeats):
        gc.collect()
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        index = fn(payload)
        wall = time.perf_counter_ns() - t0
        cpu = time.process_time_ns() - c0
        check_exact(payload, index)  # outside timed operation
        samples.append({"wall_ns": wall, "cpu_ns": cpu})
        del index
    rss_after = maxrss_kib()
    return {
        "mode": mode, "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "samples": samples,
        "peak_rss_before_kib": rss_before,
        "peak_rss_after_kib": rss_after,
        "rss_increment_kib": None if rss_before is None or rss_after is None else max(0, rss_after-rss_before),
    }


def selftest() -> dict:
    from cmpct.codec import K_FILE as true_file, S_CHUNKS as true_chunks
    from cmpct.codec import CODEC_RAW as true_raw, VERSION as true_version
    assert (true_file, true_chunks, true_raw, true_version) == (K_FILE, S_CHUNKS, CODEC_RAW, VERSION)
    from cmpct.validation import _validate_storage, ValidationError
    for n in (1, 2, 17, 4096):
        for shape in SHAPES:
            payload = generate(n, shape)
            raw = msgpack.unpackb(payload, raw=False)
            row = raw["files"][0]
            _validate_storage(row[0], row[1], row[4], row[6], raw["blobs"], raw["recipes"])
            for fn in (freeze_after, tuple_first):
                index = fn(payload)
                check_exact(payload, index)
                # CURRENT validator requires lists and rejects tuple-owned refs;
                # successful oracle construction is NOT drop-in compatibility.
                try:
                    row2 = index["files"][0]
                    _validate_storage(row2[0],row2[1],row2[4],row2[6],index["blobs"],index["recipes"])
                except ValidationError:
                    pass
                else:
                    raise AssertionError("expected current tuple-ref validator incompatibility")
    # Journal recovery also mutates decoded rows and top-level lists:
    raw = msgpack.unpackb(msgpack.packb({"files":[["a",0]],"blobs":[]}), raw=False, use_list=False)
    assert isinstance(raw["files"], tuple)
    try:
        raw["files"].append(["b", 0])
    except AttributeError:
        pass
    else:
        raise AssertionError("tuple-first journal replay incorrectly presented as compatible")
    return {"small_exact_vectors": 8, "validator_tuple_negative": 16,
            "journal_replay_drop_in": False}


def court(out: Path, source_sha: str) -> dict:
    selftest()
    results = []
    with tempfile.TemporaryDirectory() as td:
        for n in SIZES:
            for shape in SHAPES:
                payload = generate(n, shape)
                f = Path(td) / ("index-%d-%s.msgpack" % (n, shape))
                f.write_bytes(payload)
                digest = hashlib.sha256(payload).hexdigest()
                runs = []
                # ABBA paired fresh-process order. Generation is in parent,
                # each worker starts after all fixture generation and imports.
                for mode in ("freeze_after","tuple_first","tuple_first","freeze_after"):
                    cmd = [sys.executable, str(Path(__file__).resolve()),
                           "--worker",str(f),"--mode",mode,"--repeats","3"]
                    ret = subprocess.run(cmd,capture_output=True,text=True,check=True)
                    item = json.loads(ret.stdout)
                    assert item["payload_sha256"] == digest
                    runs.append(item)
                results.append({
                    "n": n, "shape": shape, "payload_sha256": digest,
                    "payload_bytes": len(payload), "runs": runs
                })
    doc = {
        "schema": "cmpct-j24c19-tuple-first-oracle-v1",
        "source_sha": source_sha, "python": sys.version,
        "msgpack": ".".join(map(str,msgpack.version)),
        "phase": "MICRO_RESEARCH_NOT_PRODUCT",
        "selftest": selftest(), "cases": results,
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    return doc


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker",type=Path)
    p.add_argument("--mode",choices=MODES)
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--court",action="store_true")
    p.add_argument("--out",type=Path,default=Path("j24c19-evidence.json"))
    p.add_argument("--source-sha",default="LOCAL_UNBOUND")
    args = p.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker,args.mode,args.repeats),sort_keys=True))
    elif args.selftest:
        print(json.dumps(selftest(),sort_keys=True))
    elif args.court:
        doc = court(args.out,args.source_sha)
        for case in doc["cases"]:
            def med(mode,key):
                return statistics.median(x[key] for run in case["runs"] if run["mode"]==mode for x in run["samples"])
            ww=med("tuple_first","wall_ns")/med("freeze_after","wall_ns")
            cc=med("tuple_first","cpu_ns")/med("freeze_after","cpu_ns")
            print("%d %s: tuple_first/freeze_after wall=%.4f cpu=%.4f" %
                  (case["n"],case["shape"],ww,cc))
        print("micro evidence only: %s" % args.out)
    else:
        p.error("choose --selftest or --court or --worker")


if __name__ == "__main__":
    main()
