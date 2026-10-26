"""O175: source-exact, genuine revision-24 Reader cache economics.

The historical and candidate Reader modules are loaded as *unmodified Git blobs*.
No Builder, monkeypatching, fabricated timing or storage-format changes.
Only a deterministic RAW corpus is studied. This is research evidence, not release parity.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import resource
import sys
import time

import msgpack
from cmpct import codec

COUNT = 96
ONE = 1 << 20
SEED = 20261026


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(4 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def payload(i: int) -> bytes:
    # Construct independently of all of CMPCT's encoders; uniform pseudo-random
    # bytes make 96 distinct RAW physical records deterministic across runs.
    return random.Random(SEED + i).randbytes(ONE)


def make_archive(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "o175-raw-96.cmpct"
    manifest_path = root / "o175-manifest.json"

    rows, blobs = [], []
    data_bytes = 0
    names = {}
    for i in range(COUNT):
        name = f"blob_{i:03d}.bin"
        raw = payload(i)
        names[name] = digest(raw)
        blobs.append([data_bytes, ONE, ONE, codec.CODEC_RAW, 0])
        rows.append([name, codec.K_FILE, 0o644, 0, ONE, None, [codec.S_BLOB, i]])
        data_bytes += codec.BHDR.size + ONE

    index = {
        "v": codec.VERSION,
        "files": rows,
        "blobs": blobs,
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    uncompressed_index = msgpack.packb(index, use_bin_type=True)
    compressed_index = codec.zc(uncompressed_index, 12)
    h = codec.sha(uncompressed_index)

    with archive.open("wb") as fp:
        fp.write(codec.HDR.pack(codec.MAGIC, codec.VERSION, 0,
                                len(compressed_index), len(uncompressed_index),
                                data_bytes, h))
        fp.write(compressed_index)
        for i in range(COUNT):
            raw = payload(i)
            fp.write(codec.BHDR.pack(
                codec.BMAGIC, codec.CODEC_RAW, 0, 0, ONE, ONE, 0,
                binascii.crc32(raw) & 0xffffffff, codec.sha(raw)))
            fp.write(raw)
        fp.write(compressed_index)
        fp.write(codec.FTR.pack(codec.FMAGIC, 0, 1, 0, 0,
                                len(compressed_index), len(uncompressed_index),
                                0, h))
    actual_size = archive.stat().st_size
    assert actual_size == codec.HDR.size + len(compressed_index) * 2 + data_bytes + codec.FTR.size
    manifest = {
        "archive_sha256": file_digest(archive),
        "archive_bytes": actual_size,
        "index_sha256": h.hex(),
        "files": names,
        "size_each": ONE,
        "reader_semantics": "revision-24 authenticated dual-index, 96 independent physical RAW S_BLOB entries",
    }
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("O175_MAKE=" + json.dumps({k: v for k, v in manifest.items() if k != "files"}, sort_keys=True), flush=True)


def load_reference(path: Path):
    spec = importlib.util.spec_from_file_location("cmpct._o175_historical_reader", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rss_bytes() -> int:
    current = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform.startswith("linux"):
        return current * 1024
    if sys.platform == "darwin":
        return current
    raise RuntimeError("O175 RSS requires POSIX Linux or Darwin")


def run_child(root: Path, source_name: str, old_source: Path | None) -> None:
    import cmpct.reader as candidate

    manifest = json.loads((root / "o175-manifest.json").read_text())
    archive = root / "o175-raw-96.cmpct"
    archive_hash = file_digest(archive)
    assert archive_hash == manifest["archive_sha256"], "shared archive identity drift"
    assert len(manifest["files"]) == COUNT
    assert list(manifest["files"]) == [f"blob_{i:03d}.bin" for i in range(COUNT)]
    reader_mod = load_reference(old_source) if source_name == "historical" else candidate
    reader_file = Path(reader_mod.__file__).resolve()
    reader_bytes = reader_file.read_bytes()
    reader_blob = hashlib.sha1(
        (f"blob {len(reader_bytes)}\0").encode() + reader_bytes
    ).hexdigest()

    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    passes = []
    with reader_mod.CMPCT(archive) as ar:
        assert len(ar.files) == COUNT
        assert len(ar.blobs) == COUNT
        assert len(ar.by) == COUNT
        for p in range(2):
            start_ns = time.perf_counter_ns()
            start_cpu_ns = time.process_time_ns()
            fold = hashlib.sha256()
            for name, expected in manifest["files"].items():
                result = ar.read(name)
                assert len(result) == ONE
                assert digest(result) == expected, (source_name, p, name)
                fold.update(name.encode())
                fold.update(bytes.fromhex(digest(result)))
                del result
            cache_payload = sum(map(len, ar.cache.values())) + sum(map(len, ar.vcache.values()))
            cache_entries = len(ar.cache) + len(ar.vcache)
            observed = {
                "pass": p + 1,
                "wall_ns": time.perf_counter_ns() - start_ns,
                "cpu_ns": time.process_time_ns() - start_cpu_ns,
                "max_rss_bytes": rss_bytes(),
                "retained_cache_payload_bytes": cache_payload,
                "retained_cache_entries": cache_entries,
                "fold_sha256": fold.hexdigest(),
            }
            if source_name == "candidate":
                assert ar._cache_bytes == cache_payload
                assert cache_payload <= 64 * ONE
                assert cache_entries <= 32768
            else:
                assert cache_payload == COUNT * ONE
                assert cache_entries == COUNT
            passes.append(observed)

    report = {
        "arm": source_name,
        "source_blob": reader_blob,
        "source_path": str(reader_file),
        "archive_sha256": archive_hash,
        "archive_bytes": manifest["archive_bytes"],
        "count": COUNT,
        "size_each": ONE,
        "passes": passes,
        "total_wall_ns": time.perf_counter_ns() - t0,
        "total_cpu_ns": time.process_time_ns() - c0,
        "os": platform.platform(),
        "python": sys.version,
        "evidence_tier": "genuine installed archive selective-read, not full official product parity",
    }
    assert passes[0]["fold_sha256"] == passes[1]["fold_sha256"]
    print("O175_RESULT=" + json.dumps(report, sort_keys=True), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["make", "historical", "candidate"])
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--original-reader", type=Path)
    args = ap.parse_args()
    if args.mode == "make":
        make_archive(args.root)
    else:
        if args.mode == "historical":
            assert args.original_reader and args.original_reader.is_file()
        run_child(args.root, args.mode, args.original_reader)


if __name__ == "__main__":
    main()
